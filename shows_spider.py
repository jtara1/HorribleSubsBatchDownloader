import scrapy
from scrapy.loader import ItemLoader
from scrapy.exceptions import DropItem

from horriblesubs_show import Show

import simplejson
import cfscrape


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