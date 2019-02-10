from horriblesubs_batch_downloader.base_scraper import BaseScraper
from bs4 import BeautifulSoup
import bs4
import os
import json


class ShowsScraper(BaseScraper):

    shows_url = "http://horriblesubs.info/shows/"

    def __init__(self, debug=False, verbose=True):
        """When this object is created, the list of shows is scraped"""
        self.debug = debug
        self.verbose = verbose

        html = self.get_html(self.shows_url)
        self.shows = self._parse_list_of_shows(html)

    def _parse_list_of_shows(self, html):
        """Go through the text of the (param) html, and pull out the names and
        url (extensions / endings) of each of the shows

        :param html: the html retrieved from the webpage, `this.shows_url`
        """
        soup = BeautifulSoup(html, 'lxml')
        shows = []

        for show_div in soup.find_all(name='div', attrs={'class': 'ind-show'}):
            show_anchor = show_div.next

            # if the next (child) element / tag is a Tag
            if isinstance(show_anchor, bs4.Tag):
                show_name = show_anchor.text

                url_extension = show_anchor.attrs['href']
                shows.append({
                    'name': show_name,
                    'url_extension': url_extension
                })
                if self.debug:
                    print(shows[-1])

        return shows

    def save_shows_to_file(self, directory=os.getcwd()):
        """

        :param directory: dir that cotains file of serialized list of shows
        defaults to $PWD/tmp/shows.json
        :return: the path to the file that is the serialization of the list of
        shows
        """
        # default save path
        temp_dir = os.path.join(directory, 'tmp')
        os.makedirs(temp_dir, exist_ok=True)

        file = os.path.join(temp_dir, 'shows.json')
        with open(file, 'w') as f:
            f.write(json.dumps(self.shows))

        return file


if __name__ == "__main__":
    scraper = ShowsScraper()
    scraper.save_shows_to_file()
    print()
    print(scraper.shows)
