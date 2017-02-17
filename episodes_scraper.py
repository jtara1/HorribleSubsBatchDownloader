import re
from bs4 import BeautifulSoup
import subprocess
import platform
import threading
from base_scraper import BaseScraper


class RegexFailedToMatch(Exception):
    """One of the regex used to parse html failed to match anything"""
    pass


class HorribleSubsEpisodesScraper(BaseScraper):

    # vars: show_type (show or batch) and show_id
    episodes_url_template = 'http://horriblesubs.info/lib/getshows.php?type={show_type}&showid={show_id}'
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
        self.episode_data_regex = re.compile(
            r".* - ([.\da-zA-Z]*) \[(\d*p)\]")  # grp 1 is ep. number, grp 2 is vid resolution
        self.episodes_page_number = 0
        # self.parse_html(html)
        self.parse_all_in_parallel()

        if self.debug:
            for ep in sorted(self.episodes, key=lambda d: d['episode_number']):
                print(ep)

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

    def parse_all_in_parallel(self):
        next_page_html = self._get_next_page_html(increment_page_number=False)
        while next_page_html != "DONE":
            thread = threading.Thread(name="ep_parse_" + str(self.episodes_page_number),
                                      target=self.parse_episodes,
                                      args=(next_page_html,))
            thread.start()
            next_page_html = self._get_next_page_html()

    def _get_next_page_html(self, increment_page_number=True, show_type="show"):
        if increment_page_number:
            self.episodes_page_number += 1
        next_page_html = self.get_html(
            self.episodes_page_url_template.format(
                show_type=show_type,
                show_id=self.show_id,
                page_number=self.episodes_page_number
            )
        )
        return next_page_html

    def parse_episodes(self, html):
        """Sample of what regex will attemp to match (show and batch):
            Naruto Shippuuden - 495 [1080p]
            Naruto Shippuuden (80-426) [1080p]
        """
        soup = BeautifulSoup(html, 'lxml')

        all_episodes_divs = soup.find_all(name='div', attrs={'class': 'release-links'})
        all_episodes_divs = reversed(all_episodes_divs)  # reversed so the highest resolution ep comes first

        # iterate through each episode html div
        for episode_div in all_episodes_divs:
            episode_data_tag = episode_div.find(name='i')
            episode_data_match = re.match(self.episode_data_regex, episode_data_tag.string)

            if not episode_data_match:
                # regex failed to find a match
                raise RegexFailedToMatch

            ep_number, vid_res = episode_data_match.group(1), episode_data_match.group(2)

            # skips lower resolutions of an episode already added
            if True in map(lambda e: e["episode_number"] == ep_number, self.episodes):
                continue

            magnet_tag = episode_div.find(name='td', attrs={'class': 'hs-magnet-link'})
            magnet_url = magnet_tag.a.attrs['href']

            self.episodes.append({
                'episode_number': ep_number,
                'video_resolution': vid_res,
                'magnet_url': magnet_url,
            })

    def parse_html(self, html):
        """Extract episode number, video resolution, and magnet link for each episode found in the html"""
        soup = BeautifulSoup(html, 'lxml')

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
            subprocess.call([cli_tool, '"' + episode['magnet_url'] + '"'])


if __name__ == "__main__":
    # standard modern 12-13 ep. anime
    # scraper = HorribleSubsEpisodesScraper(731)  # 91 days anime
    # scraper = HorribleSubsEpisodesScraper(show_url='http://horriblesubs.info/shows/91-days/', debug=True)

    # anime with extra editions of episodes
    # scraper = HorribleSubsEpisodesScraper(show_url='http://horriblesubs.info/shows/psycho-pass/', debug=True)

    # anime with 495 episodes
    scraper = HorribleSubsEpisodesScraper(show_url='http://horriblesubs.info/shows/naruto-shippuuden', debug=True)
    # scraper.download()
