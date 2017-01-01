import requests
import urllib
import sys
from bs4 import BeautifulSoup


class HorribleSubsBatchDownloader:

    shows_url = "http://horriblesubs.info/shows/"

    def __init__(self, verbose=True):
        self.verbose = verbose

        self.search_keyword = None
        self.process_command_line_arguments()

        self.soup = None
        self.load_html()

    def process_command_line_arguments(self):
        args = sys.argv[1:]

        self.search_keyword = "-".join(args).lower().replace("'", "")
        if self.verbose:
            print("Searching for: {}".format(self.search_keyword))

    def load_html(self):

        hdr2 = {'User-Agent': 'Mozilla/5.0'}
        hdr = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive'}

        # attempt using urllib library - got either HTTP 403 or 503 errors
        # request = urllib.request.Request(url=HorribleSubsBatchDownloader.shows_url, headers=hdr)
        # page = urllib.request.urlopen(request)
        # print(page)

        # attempt using requests library - got HTML text, but it wasn't loaded
        session = requests.Session()
        session.headers.update(hdr)
        page = session.get(HorribleSubsBatchDownloader.shows_url)
        # page = requests.get(HorribleSubsBatchDownloader.shows_url)
        html_text = page.text
        print(type(html_text))
        print(page.status_code)
        print(page.headers['content-type'])
        print(page.encoding)

        # load HTML text
        # self.soup = BeautifulSoup(html_text, "lxml")
        # print(self.soup.prettify())


    def search_html(self):
        self.search_results = ''


if __name__ == "__main__":
    downloader = HorribleSubsBatchDownloader()