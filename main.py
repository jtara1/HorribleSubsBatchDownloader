import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.loader import ItemLoader
from scrapy.exceptions import DropItem

from horriblesubs_show import Show
from show_selector import ShowSelector
from episodes_scraper import HorribleSubsEpisodesScraper

import cfscrape
import os
import simplejson


# global variables
SEARCH_KEY_WORD = ''


class ShowIDNotFoundException(Exception):
    pass


class HorribleSubsShowsSpider(scrapy.spiders.CrawlSpider):
    name = "hs_shows"
    start_urls = [
        "http://horriblesubs.info/shows/",
    ]

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


class PrintItemsPipeline(object):

    def __init__(self):
        pass

    def process_item(self, item, spider):
        line = simplejson.dumps(dict(item))
        print(line)
        return item


def main():
    def create_new_file(file_path):
        if not os.path.isdir(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        with open(file_path, 'w') as f:
            f.write('')

    # get key word used to search shows
    global SEARCH_KEY_WORD
    SEARCH_KEY_WORD = raw_input("Enter Anime name: ")
    # SEARCH_KEY_WORD = '91-days'

    # output file for shows spider
    shows_file_path = os.path.join(os.getcwd(), 'tmp/shows.txt')
    create_new_file(shows_file_path)

    settings = {
        'USER_AGENT': '''Mozilla/5.0 (X11;
            Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36''',
        'LOG_STDOUT': False,
        'LOG_FILE': None,
        'ITEM_PIPELINES': {'main.PrintItemsPipeline': 100},
        'FEED_URI': 'file:///' + shows_file_path,  # or 'stdout:'
        'FEED_FORMAT': 'json',
        }

    # start crawling with the shows spider
    process = scrapy.crawler.CrawlerProcess(settings)
    process.crawl(HorribleSubsShowsSpider)
    process.start()

    # get url of show user searched for
    show_selector = ShowSelector(shows_file=shows_file_path, search_key_word=SEARCH_KEY_WORD)
    show_url = show_selector.get_desired_show_url()

    # scrape the episodes and download all of them in the highest resolution available
    ep_scraper = HorribleSubsEpisodesScraper(show_url=show_url, debug=True)
    ep_scraper.download()


if __name__ == "__main__":
    main()