'''I got tired of trying to figure out scrapy and what was going wrong with getting the https response so I'll use
the requests and bs4 libraries instead
__author__ = jtara1
'''


import re
import cfscrape
import requests
from bs4 import BeautifulSoup


class HorribleSubsEpisodesScraper(object):

    episodes_url_template = 'http://horriblesubs.info/lib/getshows.php?type=show&showid={show_id}'

    def __init__(self, show_id):
        """Get the highest resolution magnet link of each episode of a show from HorribleSubs given a show id

        :param show_id: the integer HorribleSubs associates with a show - each show has a unique id (e.g.: 731)
        """
        self.show_id = show_id
        self.url = self.episodes_url_template.format(show_id=show_id)

        self.html, self.episodes = None, None
        self.get_html()
        self.parse_html()

    def get_html(self):
        """Make a request and get the html from the response"""
        token, agent = cfscrape.get_tokens(url=self.url)
        request = requests.get(self.url, headers={'User-Agent': agent}, cookies=token)

        if request.status_code != 200:
            raise requests.exception.HTTPError

        self.html = request.text
        return request.text

    def parse_html(self):
        """Extract episode number, video resolution, and magnet link for each episode found in the html"""
        soup = BeautifulSoup(self.html)

        episodes = []
        episodes_added = set()  # used to avoid getting duplicates of an episode

        all_episodes_divs = soup.find_all(name='div', attrs={'class': 'release-links'})
        all_episodes_divs = reversed(all_episodes_divs)

        episode_data_regex = re.compile(r".* - ([\d.]*) \[(\d*p)\]")  # grp 1 is ep. number, grp 2 is vid resolution
        for episode_div in all_episodes_divs:
            # print(episode_div.prettify())
            # episode_data_tag = episode_div.find(name='td', attr={'class': 'dl-label'})
            episode_data_tag = episode_div.find(name='i')
            episode_data_match = re.match(episode_data_regex, episode_data_tag.string)

            if not episode_data_match:
                # regex failed to find a match
                raise NoEpisodeDataException

            ep_number, vid_res = episode_data_match.group(1), episode_data_match.group(2)

            # skips lower resolutions
            if ep_number in episodes_added:
                continue
            episodes_added.add(ep_number)

            magnet_tag = episode_div.find(name='td', attrs={'class': 'hs-magnet-link'})
            magnet_url = magnet_tag.a.attrs['href']

            episodes.append({
                'episode_number': ep_number,
                'video_resolution': vid_res,
                'magnet_url': magnet_url,
            })

        # print(episodes)
        self.episodes = episodes
        return episodes


class NoEpisodeDataException(Exception):
    pass


if __name__ == "__main__":
    scraper = HorribleSubsEpisodesScraper(731)  # 91 days anime

