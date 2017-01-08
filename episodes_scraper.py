'''
__author__ = jtara1
'''

import re
import cfscrape
import requests
from bs4 import BeautifulSoup
import subprocess
import platform


class RegexFailedToMatch(Exception):
    pass


class HorribleSubsEpisodesScraper(object):

    episodes_url_template = 'http://horriblesubs.info/lib/getshows.php?type=show&showid={show_id}'  # vars: show_id
    episodes_page_url_template = episodes_url_template + '&nextid={page_number}&_'  # vars: show_id, page_number

    def __init__(self, show_id=None, show_url=None, verbose=True, debug=False):
        """Get the highest resolution magnet link of each episode of a show from HorribleSubs given a show id

        :param show_id: the integer HorribleSubs associates with a show - each show has a unique id (e.g.: 731)
        :param show_url: the url of show from HorribleSubs (e.g.: http://horriblesubs.info/shows/91-days)
        :param verbose: if True prints additional information
        :param debug: if True prints additional more information
        """
        self.verbose = verbose
        self.debug = debug

        if not show_id and not show_url:
            raise ValueError("either show_id or show_url is required")
        elif show_url and not show_id:
            self.show_id = self.get_show_id_from_url(show_url)
        else:
            if not isinstance(show_id, int) or not show_id.isdigit():
                raise ValueError("Invalid show_id; expected an integer or string containing an integer")
            self.show_id = show_id

        url = self.episodes_url_template.format(show_id=self.show_id)
        if self.debug:
            print("show_id = {}".format(self.show_id))
            print("url = {}".format(url))

        html = self.get_html(url)
        self.episodes = []
        self.episodes_page_number = 1
        self.parse_html(html)

    def get_show_id_from_url(self, show_url):
        """Finds the show_id in the html using regex

        :param show_url: url of the HorribleSubs show
        """
        html = self.get_html(show_url)
        show_id_regex = r".*var hs_showid = (\d*)"
        match = re.match(show_id_regex, html, flags=re.DOTALL)

        if not match:
            raise RegexFailedToMatch

        return match.group(1)

    def get_html(self, url):
        """Make a request and get the html from the response"""
        token, agent = cfscrape.get_tokens(url=url)
        request = requests.get(url, headers={'User-Agent': agent}, cookies=token)

        if request.status_code != 200:
            raise requests.exception.HTTPError

        return request.text

    def parse_html(self, html):
        """Extract episode number, video resolution, and magnet link for each episode found in the html"""
        soup = BeautifulSoup(html)

        episodes = []
        episodes_added = set()  # used to avoid getting duplicates of an episode

        all_episodes_divs = soup.find_all(name='div', attrs={'class': 'release-links'})
        all_episodes_divs = reversed(all_episodes_divs)  # reversed so the highest resolution ep comes first

        episode_data_regex = re.compile(r".* - ([.\da-zA-Z]*) \[(\d*p)\]")  # grp 1 is ep. number, grp 2 is vid resolution
        for episode_div in all_episodes_divs:
            episode_data_tag = episode_div.find(name='i')
            episode_data_match = re.match(episode_data_regex, episode_data_tag.string)

            if not episode_data_match:
                # regex failed to find a match
                raise RegexFailedToMatch

            ep_number, vid_res = episode_data_match.group(1), episode_data_match.group(2)

            # skips lower resolutions of an episode already added
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

        if self.debug:
            for ep in episodes:
                print(ep)
        self.episodes.extend(episodes)

        # get next page of episodes and call this method again with next page html
        next_page_html = self.get_html(
            self.episodes_page_url_template.format(
                show_id=self.show_id,
                page_number=self.episodes_page_number
            )
        )
        # if there's more episodes on the next page for this anime / show
        if next_page_html != 'DONE':
            self.episodes_page_number += 1
            self.parse_html(next_page_html)  # recursive call
        else:
            print("\nNumber of episodes: {}".format(len(self.episodes)))
            return self.episodes

    def download(self):
        """Downloads every episode in self.episodes"""
        cli_tool = 'start' if platform.system() == 'Windows' else 'xdg-open'
        for episode in self.episodes:
            subprocess.call([cli_tool, episode['magnet_url']])


if __name__ == "__main__":
    # scraper = HorribleSubsEpisodesScraper(731)  # 91 days anime
    scraper = HorribleSubsEpisodesScraper(show_url='http://horriblesubs.info/shows/91-days/', debug=True)
    scraper.download()
