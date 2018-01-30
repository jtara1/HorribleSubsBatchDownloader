from horriblesubs_batch_downloader.base_scraper import BaseScraper
from bs4 import BeautifulSoup
import os
import json


class ShowsScraper(BaseScraper):

    shows_url = "http://horriblesubs.info/shows/"

    def __init__(self, debug=False, verbose=True):
        """When this object is created, the list of shows is scraped"""
        self.debug = debug
        self.verbose = verbose

        html = self.get_html(self.shows_url)
        self.shows = self.parse_list_of_shows(html)

    def parse_list_of_shows(self, html):
        """Go through the text of the (param) html, and pull out the names and
        url (extensions / endings) of each of the shows

        :param html: the html retrieved from the webpage, `this.shows_url`
        """
        soup = BeautifulSoup(html, 'lxml')
        shows = []

        for show_div in soup.find_all(name='div', attrs={'class': 'ind-show linkful'}):
            # print(show_div)
            # show.add_value('name', shows_div.css('a::text').extract_first())
            show_name = show_div.a.string
            # show.add_value('url_extension', shows_div.css('a').xpath('@href').extract_first())
            url_extension = show_div.a.attrs['href']
            shows.append({
                    'name': show_name,
                    'url_extension': url_extension
                }
            )
            if self.debug:
                print(shows[-1])

        return shows

    def save_shows_to_file(self, file=os.path.join(os.getcwd(), '/tmp/shows.json')):
        with open(file, 'w') as f:
            f.write(json.dumps(self.shows))


if __name__ == "__main__":
    scraper = ShowsScraper()
    print()
    print(scraper.shows)
