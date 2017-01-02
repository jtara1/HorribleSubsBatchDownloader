import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.loader import ItemLoader
from scrapy.exceptions import DropItem
import cfscrape
from horriblesubs_batch_downloader import HorribleSubsBatchDownloader
import os
import simplejson
from horriblesubs_show import Show

# global variables
SEARCH_KEY_WORD = ""

class HorribleSubsShowsSpider(scrapy.spiders.CrawlSpider):
    name = "hb_shows"
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
        for show_div in response.css('div.ind-show'):
            show = ItemLoader(item=Show(), response=response)
            show.add_value('name', show_div.css('a::text').extract_first())
            show.add_value('url_extension', show_div.css('a').xpath('@href').extract_first())
            yield show.load_item()
            # yield {
            #     'title': show_div.css('a::text').extract_first(),
            #     'url': show_div.css('a').xpath('@href').extract_first(),
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


def parse_shows_from_log_file(input_file_path, expected_keys=('url', 'title'), output_file_path=None,
                              save_to_file=False):
    """Goes through a file and collects the dictionary from each line only containing a dictionary with keys matching
    one of the keys from (param) expected_keys
    :param save_to_file: if true then save the list of shows to in the output file
    :param input_file_path: file to parse through
    :param output_file_path: list of shows gets saved to this file
    :param expected_keys: if a key is found in the input file that doesn't match
    :return:
    """
    if save_to_file:
        if output_file_path is None:
            output_file_path = os.path.join(os.path.dirname(input_file_path), "shows-parsed.txt")
        create_new_file(output_file_path)

    shows = []  # list containing dictionaries

    file = open(input_file_path, 'r')
    for line in file:
        if line.startswith('{') and "JoJo's Bizarre" not in line:
            is_valid_show = True
            for key in expected_keys:
                if key not in line:
                    is_valid_show = False

            if is_valid_show:
                line = line.replace('\'', "\"").replace(' u"', ' "').replace(" None", '""')
                show = simplejson.loads(line)
                shows.append(show)
    file.close()

    if save_to_file:
        # use json to convert the list of shows to a string and write that in the output file
        with open(output_file_path, 'w') as f:
            f.write(simplejson.dumps(shows))

    return shows


def create_new_file(file_path):
    if not os.path.isdir(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    with open(file_path, 'w') as f:
        f.write('')


def main():
    # get key word used to search shows
    global SEARCH_KEY_WORD
    SEARCH_KEY_WORD = raw_input("Enter Anime name: ")
    print(SEARCH_KEY_WORD)

    shows_file_path = os.path.join(os.getcwd(), 'tmp/shows.txt')
    create_new_file(shows_file_path)

    settings = {
        'USER_AGENT': '''Mozilla/5.0 (X11;
            Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36''',
        'LOG_STDOUT': False,
        'LOG_FILE': None,
        'ITEM_PIPELINES': {'main.ShowItemsPipeline': 100},
        'FEED_URI': 'file:///' + shows_file_path,  # or 'stdout:'
        'FEED_FORMAT': 'json',
        }

    process = scrapy.crawler.CrawlerProcess(settings)
    process.crawl(HorribleSubsShowsSpider)
    process.start()

    # shows = parse_shows_from_log_file(shows_file_path)

    # downloader = HorribleSubsBatchDownloader()


if __name__ == "__main__":
    main()