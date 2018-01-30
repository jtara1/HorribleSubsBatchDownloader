import sys
import subprocess
import os
import re
from bs4 import BeautifulSoup
import threading
from horriblesubs_batch_downloader.base_scraper import BaseScraper
from horriblesubs_batch_downloader.exception import HorribleSubsException, RegexFailedToMatch


class HorribleSubsEpisodesScraper(BaseScraper):

    # vars in string template: show_type (show or batch) and show_id
    episodes_url_template = 'http://horriblesubs.info/lib/getshows.php?' \
                            'type={show_type}&showid={show_id}'
    # additional vars: page_number
    episodes_page_url_template = \
        episodes_url_template+'&nextid={page_number}&_'

    def __init__(self, show_id=None, show_url=None, verbose=True, debug=False):
        """Get the highest resolution magnet link of each episode
        of a show from HorribleSubs given a show id

        :param show_id: the integer HorribleSubs associates with a show -
            each show has a unique id (e.g.: 731)
        :param show_url: the url of show from HorribleSubs
            (e.g.: http://horriblesubs.info/shows/91-days)
        :param verbose: if True prints additional information
        :param debug: if True prints additional more information
        """
        self.verbose = verbose
        self.debug = debug

        # need a show_id or show_url
        if not show_id and not show_url:
            raise ValueError("either show_id or show_url is required")
        # only show_url was given
        elif show_url and not show_id:
            self.show_id = self.get_show_id_from_url(show_url)
        # use show_id over show_url if both are given or only show_id is given
        else:
            if not isinstance(show_id, int) or not show_id.isdigit():
                raise ValueError("Invalid show_id; expected an integer "
                                 "or string containing an integer")
            self.show_id = show_id

        # url that'll give us the webpage containing the
        # magnet links of episodes or batches of episodes
        url = self.episodes_url_template.format(show_type='show',
                                                show_id=self.show_id)
        if self.debug:
            print("show_id = {}".format(self.show_id))
            print("url = {}".format(url))

        # regex used to extract episode number(s) and video resolution
        # grp 1 is ep. number, grp 2 is vid resolution
        self.episode_data_regex = re.compile(
            r".* - ([.\da-zA-Z]*) \[(\d*p)\]")
        # grp 1 is 1st ep. of batch, grp 2 is last ep. of batch, grp 3 is res
        self.batch_episodes_data_regex = re.compile(
            r".* \((\d*)-(\d*)\) \[(\d*p)\]")

        # most recent ep. number used to help determine when we have
        # scraped all episodes available
        try:
            last_ep_number = self.get_most_recent_episode_number(url)
            if self.debug:
                print("most recent episode number: ", last_ep_number)
            self.episodes_available = set(range(1, int(last_ep_number) + 1))
        except HorribleSubsException:
            # get last episode number from batches
            self.episodes_available = None

        self.all_episodes_acquired = False
        self.threads = []
        self.episodes = []
        self.episode_numbers_collected = set()
        self.episodes_page_number = 0

        # begin the scraping of episodes
        batch_episodes_url = self.episodes_url_template.format(
            show_type='batch', show_id=self.show_id)
        # there shouldn't be more than 1 page of batch
        self.parse_batch_episodes(self.get_html(url=batch_episodes_url))

        if self.episodes_available:
            self.parse_all_in_parallel()

        if self.debug:
            for ep in sorted(
                    self.episodes,
                    key=lambda d:
                    d['episode_number'][-1]
                    if isinstance(d['episode_number'], list)
                    else d['episode_number']):
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
        while next_page_html != "DONE" and not self.all_episodes_acquired:
            thread = threading.Thread(
                name="ep_parse_" + str(self.episodes_page_number),
                target=self.parse_episodes,
                args=(next_page_html,))
            thread.start()
            self.threads.append(thread)

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
        """Sample of what regex will attempt to match (show and batch):
            Naruto Shippuuden - 495 [1080p]
            Naruto Shippuuden (80-426) [1080p]
        """
        soup = BeautifulSoup(html, 'lxml')

        all_episodes_divs = soup.find_all(
            name='div', attrs={'class': 'release-links'})
        # reversed so the highest resolution ep comes first
        all_episodes_divs = reversed(all_episodes_divs)

        # iterate through each episode html div
        for episode_div in all_episodes_divs:
            episode_data_tag = episode_div.find(name='i')
            episode_data_match = re.match(
                self.episode_data_regex, episode_data_tag.string)

            if not episode_data_match:
                # regex failed to find a match
                raise RegexFailedToMatch

            # keep ep_number as a string
            ep_number, vid_res = \
                episode_data_match.group(1), episode_data_match.group(2)

            # skips lower resolutions of an episode already added
            if ep_number in self.episode_numbers_collected:
                continue

            magnet_tag = episode_div.find(
                name='td', attrs={'class': 'hs-magnet-link'})
            magnet_url = magnet_tag.a.attrs['href']

            self._add_episode(
                episode_number=ep_number,
                video_resolution=vid_res,
                magnet_url=magnet_url)

        if self.episode_numbers_collected == self.episodes_available:
            self.all_episodes_acquired = True

    def parse_batch_episodes(self, html):
        soup = BeautifulSoup(html, 'lxml')

        all_episodes_divs = soup.find_all(
            name='div', attrs={'class': 'release-links'})

        # reversed so the highest resolution ep comes first
        all_episodes_divs = reversed(all_episodes_divs)

        # iterate through each episode html div
        for episode_div in all_episodes_divs:
            episode_data_tag = episode_div.find(name='i')
            episode_data_match = re.match(
                self.batch_episodes_data_regex, episode_data_tag.string)

            if not episode_data_match:
                # regex failed to find a match
                raise RegexFailedToMatch

            first_ep_number = episode_data_match.group(1)
            last_ep_numb = episode_data_match.group(2)
            vid_res = episode_data_match.group(3)

            episode_range = list(range(
                int(first_ep_number), int(last_ep_numb) + 1))

            # skips lower resolutions
            if True in map(
                    lambda d: d["episode_number"] == episode_range,
                    self.episodes):
                continue

            magnet_tag = episode_div.find(
                name='td', attrs={'class': 'hs-magnet-link'})
            magnet_url = magnet_tag.a.attrs['href']

            self._add_episode(
                episode_range=episode_range,
                video_resolution=vid_res,
                magnet_url=magnet_url)

    def _add_episode(self, episode_number=None, episode_range=None,
                     video_resolution=None, magnet_url=None):
        """

        :param episode_number:
        :param episode_range: list of integers
        :param video_resolution:
        :param magnet_url:
        :return:
        """
        self.episodes.append({
            'episode_number': episode_range
            if episode_range else episode_number,
            'video_resolution': video_resolution,
            'magnet_url': magnet_url,
        })

        if episode_range:
            self.episode_numbers_collected.update(set(episode_range))
        else:
            self.episode_numbers_collected.add(episode_number)
        # print(sorted(self.episode_numbers_collected))

    def get_most_recent_episode_number(self, url):
        html = self.get_html(url)
        soup = BeautifulSoup(html, "lxml")

        episode_div_tag = soup.find(
            name='div', attrs={"class": "release-links"})
        if episode_div_tag is None:
            raise HorribleSubsException("there are no individual episodes")

        text_tag = episode_div_tag.find(name="i")
        regex_match = re.match(
            pattern=self.episode_data_regex, string=text_tag.string)

        if not regex_match:
            raise RegexFailedToMatch

        return regex_match.group(1)

    def download(self):
        """Downloads every episode in self.episodes"""
        for episode in self.episodes:
            if sys.platform == "win32" or sys.platform == "cygwin":
                os.startfile(episode['magnet_url'])
            else:
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, episode['magnet_url']])


if __name__ == "__main__":
    # standard modern 12-13 ep. anime
    # scraper = HorribleSubsEpisodesScraper(731)  # 91 days anime
    # scraper = HorribleSubsEpisodesScraper(show_url='http://horriblesubs.info/shows/91-days/', debug=True)

    # anime with extra editions of episodes
    # scraper = HorribleSubsEpisodesScraper(show_url='http://horriblesubs.info/shows/psycho-pass/', debug=True)

    # anime with 495 episodes
    scraper = HorribleSubsEpisodesScraper(show_url='http://horriblesubs.info/shows/naruto-shippuuden', debug=True)
    # scraper.download()
