import cfscrape
import requests


class BaseScraper(object):

    def get_html(self, url):
        """Make a request and get the html (text) from the response"""
        token, agent = cfscrape.get_tokens(url=url)
        response = requests.get(url, headers={'User-Agent': agent}, cookies=token)

        if response.status_code != 200:
            raise requests.exception.HTTPError

        return response.text
