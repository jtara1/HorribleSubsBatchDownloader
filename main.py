import scrapy
from scrapy.crawler import CrawlerProcess
import cfscrape
from horriblesubs_batch_downloader import HorribleSubsBatchDownloader
import os


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
        for show_div in response.css('div.ind-show'):
            yield {
                'title': show_div.css('a::text').extract_first(),
                'url': show_div.css('a').xpath('@href').extract_first(),
            }


def main():
    log_file_path = os.path.join(os.getcwd(), 'tmp/shows.txt')
    if not os.path.isdir(os.path.dirname(log_file_path)):
        os.makedirs(os.path.dirname(log_file_path))
    with open(log_file_path, 'w') as f:
        f.write('')

    settings = {
        'USER_AGENT': '''Mozilla/5.0 (X11;
            Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36''',
        'LOG_STDOUT': False,
        'LOG_FILE': log_file_path,
        }

    process = scrapy.crawler.CrawlerProcess(settings)
    process.crawl(HorribleSubsShowsSpider)
    process.start()

    # downloader = HorribleSubsBatchDownloader()


if __name__ == "__main__":
    main()