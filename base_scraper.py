import cfscrape
import requests


class BaseScraper(object):

    def get_html(self, url):
        """Make a request and get the html from the response"""
        token, agent = cfscrape.get_tokens(url=url)
        request = requests.get(url, headers={'User-Agent': agent}, cookies=token)

        if request.status_code != 200:
            raise requests.exception.HTTPError

        return request.text
