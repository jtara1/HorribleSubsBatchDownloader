from scrapy.crawler import CrawlerProcess

from shows_spider import HorribleSubsShowsSpider
from show_selector import ShowSelector
from episodes_scraper import HorribleSubsEpisodesScraper

import os
import sys


def get_command_line_arguments():
    """Returns all cli args joins with '-' char if there are any, otherwise returns the empty string"""
    if len(sys.argv) > 1:
        return "-".join(sys.argv[1:])
    else:
        return ""


def main():
    def create_new_file(file_path):
        if not os.path.isdir(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        with open(file_path, 'w') as f:
            f.write('')

    # use cli args if provided
    cli_args_concatenated = get_command_line_arguments()
    if cli_args_concatenated:
        search_key_word = cli_args_concatenated
    else:
        search_key_word = raw_input("Enter anime to download from HorribleSubs: ")

    # search_key_word = '91-days'
    print("Searching for {} ...".format(search_key_word))

    # output file for shows spider
    shows_file_path = os.path.join(os.getcwd(), 'tmp/shows.txt')
    create_new_file(shows_file_path)

    settings = {
        'USER_AGENT': '''Mozilla/5.0 (X11;
            Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36''',
        'LOG_STDOUT': False,
        'LOG_FILE': None,
        # 'ITEM_PIPELINES': {'horriblesubs_shows_spider.PrintItemsPipeline': 100},
        'FEED_URI': 'file:///' + shows_file_path,
        'FEED_FORMAT': 'json',
        }

    # start crawling with the shows spider
    process = CrawlerProcess(settings)
    process.crawl(HorribleSubsShowsSpider)
    process.start()

    # get url of show user searched for
    show_selector = ShowSelector(shows_file=shows_file_path, search_key_word=search_key_word)
    show_url = show_selector.get_desired_show_url()

    # scrape the episodes and download all of them in the highest resolution available
    ep_scraper = HorribleSubsEpisodesScraper(show_url=show_url, debug=True)
    ep_scraper.download()


if __name__ == "__main__":
    main()
