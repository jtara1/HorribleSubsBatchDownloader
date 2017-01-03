from twisted.internet import reactor, defer

from selenium import webdriver

import scrapy
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.loader import ItemLoader
from horriblesubs_show import Show
from scrapy.exceptions import DropItem

from horriblesubs_batch_downloader import HorribleSubsBatchDownloader
from show_selector import ShowSelector
# from episode_spider import HorribleSubsEpisodesSpider
from horriblesubs_episode import Episode
from ninetyonedays_spider import NinetyOneDaysSpider  # debug
from episodes_scraper import HorribleSubsEpisodesScraper

import cfscrape
import os
import simplejson
import functools


# global variables
SEARCH_KEY_WORD = ''
PHANTOMJS_EXECUTABLE = '/bin/phantomjs'

class ShowIDNotFoundException(Exception):
    pass


class HorribleSubsShowsSpider(scrapy.spiders.CrawlSpider):
    name = "hb_shows"
    start_urls = [
        "http://horriblesubs.info/shows/",
    ]
    # middleware = set([])

    def __init__(self):
        super(HorribleSubsShowsSpider).__init__(type(self))

    def start_requests(self):
        cf_requests = []
        for url in self.start_urls:
            token, agent = cfscrape.get_tokens(url, 'Your preferable user agent, _optional_')
            cf_requests.append(scrapy.http.Request(
                url=url,
                cookies=token,
                headers={'User-Agent': agent}))
        return cf_requests

    def parse(self, response):
        # self.get_search_word()
        for shows_div in response.css('div.ind-show'):
            show = ItemLoader(item=Show(), response=response)
            show.add_value('name', shows_div.css('a::text').extract_first())
            show.add_value('url_extension', shows_div.css('a').xpath('@href').extract_first())
            yield show.load_item()
            # yield {
            #     'title': shows_div.css('a::text').extract_first(),
            #     'url': shows_div.css('a').xpath('@href').extract_first(),
            # }

    def get_search_word(self):
        global SEARCH_KEY_WORD
        SEARCH_KEY_WORD = input("Enter Anime name: ")


class ShowItemsPipeline(object):
    """Filter shows returned by ShowsSpider parser so that we only have the shows that contain the key word search"""
    def __init__(self):
        self.matched_shows = []
        self.file = None

    def open_spider(self, spider):
        self.file = open('shows.json', 'wb')

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        global SEARCH_KEY_WORD
        if item['url_extension'] and SEARCH_KEY_WORD in item['url_extension']:
            line = simplejson.dumps(dict(item)) + '\n'
            print(line)
            self.matched_shows.append(item)
            self.file.write(line)
            return item
        else:
            raise DropItem("{} does not match key word search".format(item['name']))


class HorribleSubsEpisodesSpider(scrapy.spiders.Spider):
    name = "hs_episodes"
    # start_urls = [
    #     "http://horriblesubs.info/shows/91-days",
    # ]
    # middleware = set([JSDownload])

    def __init__(self, show_url):
        self.start_urls = [show_url]
        super(HorribleSubsEpisodesSpider).__init__(type(self))

    def start_requests(self):
        # get url stored in file (e.g.: http://horriblesubs.info/shows/91-days)
        cf_requests = []
        for url in self.start_urls:
            token, agent = cfscrape.get_tokens(url, 'Your preferable user agent, _optional_')
            cf_requests.append(scrapy.http.Request(
                url=url,
                cookies=token,
                headers={'User-Agent': agent}))
        return cf_requests

    def get_ajax_request_for_episodes(self, show_id):
        xhr_request_template = 'http://horriblesubs.info/lib/getshows.php?type=show&showid={show_id}'
        url = xhr_request_template.format(show_id=show_id)
        print(url)
        return scrapy.http.Request(url, callback=self.parse_episodes)

    def parse(self, response):
        selector = scrapy.selector.Selector(response=response)
        # get show id
        show_id_regex = r".*var hs_showid = (\d*)"
        match = selector.re.match(show_id_regex)
        if not match:
            raise ShowIDNotFoundException(
                "'{}' failed to match the show id from {}".format(show_id_regex, response.url))
        show_id = int(match.group(1))

        episodes_request = self.get_ajax_request_for_episodes(show_id=show_id)
        print(type(episodes_request))
        return episodes_request

    def parse_episodes(self, response):
        # debug
        with open('episodes-response', 'w') as f:
            text_rep = scrapy.http.HtmlResponse(response.url)
            f.write(text_rep.text)

        episode_numbers = set()
        all_episodes = response.css('div.release-links').extract()
        all_episodes = reversed(all_episodes)  # reverse so the highest quality and 1st episode come first

        episode_data_regex = '.* - (\d*) \[(\d*p)\]'  # group 1 is ep. number, group 2 is vid resolution
        for episode_div in all_episodes:
            episode_data_match = episode_div.css('td.dl-label::text').extract_first().re.match(episode_data_regex)
            episode_number = episode_data_match.group(1)
            if episode_number in episode_numbers:
                continue
            episode_numbers.add(episode_number)
            vid_resolution = episode_data_match.group(2)
            magnet_link = episode_div.css('span.dl-link').xpath('a[@href]').extract_first()

            episode = ItemLoader(item=Episode(), response=response)
            episode.add_value('episode_number', episode_number)
            episode.add_value('video_resolution', vid_resolution)
            episode.add_value('magnet_link', magnet_link)

            yield episode.load_item()


class PrintItemsPipeline(object):

    def __init__(self):
        pass

    def process_item(self, item, spider):
        line = simplejson.dumps(dict(item)) + '\n'
        print(line)
        return item


def create_new_file(file_path):
    if not os.path.isdir(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    with open(file_path, 'w') as f:
        f.write('')


def main():
    # get key word used to search shows
    global SEARCH_KEY_WORD
    SEARCH_KEY_WORD = raw_input("Enter Anime name: ")
    # SEARCH_KEY_WORD = '91-days'
    print(SEARCH_KEY_WORD)

    # output file for shows spider
    shows_file_path = os.path.join(os.getcwd(), 'tmp/shows.txt')
    create_new_file(shows_file_path)

    # output file for episodes spider
    episodes_file_path = os.path.join(os.getcwd(), 'tmp/episodes.txt')
    create_new_file(episodes_file_path)

    settings = {
        'USER_AGENT': '''Mozilla/5.0 (X11;
            Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36''',
        'LOG_STDOUT': False,
        'LOG_FILE': None,
        'ITEM_PIPELINES': {'main.ShowItemsPipeline': 100},
        'FEED_URI': 'file:///' + shows_file_path,  # or 'stdout:'
        'FEED_FORMAT': 'json',
        }
    episodes_spider_settings = {
        'USER_AGENT': '''Mozilla/5.0 (X11;
                Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36''',
        'LOG_STDOUT': True,
        'LOG_FILE': None,
        'ITEM_PIPELINES': {'main.PrintItemsPipeline': 100},
        # 'ITEM_PIPELINES': {'main.ShowItemsPipeline': 100},
        'FEED_URI': 'file:///' + episodes_file_path,  # or 'stdout:'
        # 'FEED_URI': 'stdout:',
        'FEED_FORMAT': 'json',
        # 'DOWNLOADER_MIDDLEWARES': {'main.JSDownload': 500}
    }

    # process = scrapy.crawler.CrawlerProcess(settings)
    # process.crawl(HorribleSubsShowsSpider)
    # process.start()
    runner = scrapy.crawler.CrawlerRunner(settings=settings)

    @defer.inlineCallbacks
    def crawl():
        # shows spider
        yield runner.crawl(HorribleSubsShowsSpider)

        # episodes spider
        # runner.settings = episodes_spider_settings
        # yield runner.crawl(HorribleSubsEpisodesSpider, show_url=show_url)
        # yield runner.crawl(NinetyOneDaysSpider)  # spider for a specific anime
        reactor.stop()

    crawl()
    reactor.run()

    # get url of show user searched for
    show_selector = ShowSelector(shows_file=shows_file_path, search_key_word=SEARCH_KEY_WORD)
    show_url = show_selector.get_desired_show_url()

    ep_scraper = HorribleSubsEpisodesScraper(show_url=show_url, debug=True)
    ep_scraper.download()
    # shows = parse_shows_from_log_file(shows_file_path)

    # process2 = scrapy.crawler.CrawlerProcess(settings)
    # process2.crawl(HorribleSubsEpisodesSpider, show_url=show_url)
    # process2.start()


    # downloader = HorribleSubsBatchDownloader()


if __name__ == "__main__":
    main()