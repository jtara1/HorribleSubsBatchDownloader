from pprint import pprint
import sys
import subprocess
import os
import re
from bs4 import BeautifulSoup
from horriblesubs_batch_downloader.base_scraper import BaseScraper
from horriblesubs_batch_downloader.exception import HorribleSubsException, RegexFailedToMatch
from horriblesubs_batch_downloader.setup_logger import setup_logger


class EpisodesScraper(BaseScraper):

    # vars in string template: show_type (show or batch) and show_id
    episodes_url_template = 'https://horriblesubs.info/api.php?' \
                            'method=getshows&type={show_type}&showid={show_id}'
    # additional vars: page_number
    episodes_page_url_template = \
        episodes_url_template+'&nextid={page_number}&_'

    def __init__(self, show_id=None, show_url=None, verbose=True, debug=False, r=None, qual=None):
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
        self.logger = setup_logger('hsbd.episodes_scraper')

        # need a show_id or show_url
        if not show_id and not show_url:
            raise ValueError("either show_id or show_url is required")
        # only show_url was given
        elif show_url and not show_id:
            self.show_id = self.get_show_id_from_url(show_url)
        # use show_id over show_url if both are given or only show_id is given
        else:
            show_id = str(show_id)
            if not show_id.isdigit():
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

        # grp 1 is 1st ep. of batch, grp 2 is last ep. of batch, grp 3 is res
        self.batch_episodes_data_regex = re.compile(
            r".* \((\d*)-(\d*)\) \[(\d*p)\]")

        # most recent ep. number used to help determine when we have
        # scraped all episodes available
        try:
            last_ep_number = self._get_most_recent_episode_number(url)
            if self.debug:
                print("most recent episode number: ", last_ep_number)
            # print(last_ep_number, r[1], type(r[1]), type(last_ep_number))
            if r[1] == int(last_ep_number):
                r = (r[0], int(last_ep_number) + 1)
            # set of episode numbers available to download
            self.episodes_available = set(range(1, int(last_ep_number) + 1))
        except HorribleSubsException:
            print('WARN: there was no most recent '
                  'episode number from non-batch')

            # get last episode number from batches
            self.episodes_available = None



        self.all_episodes_acquired = False
        self.episodes = []
        self.episode_numbers_collected = set()
        self.episodes_page_number = 0

        # begin the scraping of episodes
        batch_episodes_url = self.episodes_url_template.format(
            show_type='batch', show_id=self.show_id)
        # there shouldn't be more than 1 page of batch
        self._parse_batch_episodes(self.get_html(url=batch_episodes_url))

        # there's more episodes available that haven't been parsed for
        # magnet url from batch episodes
        if self.episodes_available != self.episode_numbers_collected and \
                self.episodes_available:
            self.parse_all(qual)

        if self.debug:
            self.episodes = sorted(
                self.episodes,
                key=lambda episode_info:
                episode_info['episode_number'][-1]
                if isinstance(episode_info['episode_number'], list)
                else self._compute_episode_value(episode_info['episode_number'])
            )

            if r:
                r = self._get_episode_index(r)
                    
                self.episodes = self.episodes[r[0] - 1:r[1]]

            for episode in self.episodes:
                pprint(episode)
                print()

            

    def _get_episode_index(self, r):
        nur = sorted(tuple(i + 1 for i in range(len(self.episodes)) if self._compute_episode_value(self.episodes[i].get("episode_number")) == self._compute_episode_value(r[0]) or self._compute_episode_value(self.episodes[i].get("episode_number")) == self._compute_episode_value(r[1])))
        if len(r) < 2 and r[0] != r[1]:
            print("Range was invalid! Defaulting...")
            nur = (1, len(self.episodes))
        elif r[0] == r[1]:
            nur = nur * 2

        return nur


    def _compute_episode_value(self, ev):
        try:
            nuev = (float(ev),)
        except:
            m = re.search(r"\d+", ev)
            nuev = (float(ev[m.start():m.end()]),) + tuple(ord(x) for x in ev[m.end():]) 

        return nuev

    def get_show_id_from_url(self, show_url):
        """Finds the show_id in the html using regex

        :param show_url: url of the HorribleSubs show
        """
        self.logger.debug('get_show_id_from_url: {}'.format(show_url))

        html = self.get_html(show_url)
        show_id_regex = r".*var hs_showid = (\d*)"
        match = re.match(show_id_regex, html, flags=re.DOTALL)

        if not match:
            raise RegexFailedToMatch

        return match.group(1)

    def parse_all(self, qual=None):
        """Parse all of the episodes available from the current page
        for a show

        :return:
        """
        next_page_html = self._get_next_page_html(increment_page_number=False)

        while next_page_html != "DONE" and not self.all_episodes_acquired:
            self._parse_episodes(next_page_html, qual)

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

    def _parse_episodes(self, html, qual=None):
        """Parses episode info and magnet urls from html from request from
        link from class variable
        """
        soup = BeautifulSoup(html, 'lxml')

        all_episodes_divs = soup.find_all(
            name='div', attrs={'class': 'rls-info-container'})
        # reversed so the highest resolution ep comes first
        # all_episodes_divs = reversed(all_episodes_divs)

        # iterate through each episode html div
        for episode_div in all_episodes_divs:

            label_tag = episode_div.find(name='a', attrs={'class': 'rls-label'})

            
            ep_number = episode_div.find(name='strong').text

            # skips lower resolutions of an episode already added
            if ep_number in self.episode_numbers_collected:
                continue

            # all download link tags to all resolutions and sources
            links = episode_div.find_all(name='div', attrs={'class': 'rls-link'})

            resolution = -len(links) + qual if qual != len(links) else -1

            # last one (highest resolution) html tag for magnet link
            magnet_tag = links[resolution].find(
                name='span', attrs={'class': 'hs-magnet-link'})
            magnet_url = magnet_tag.next.attrs['href']

            vid_res = label_tag.contents[resolution].text

            self._add_episode(
                episode_number=ep_number,
                video_resolution=vid_res,
                magnet_url=magnet_url)

        if self.episode_numbers_collected == self.episodes_available:
            self.all_episodes_acquired = True

    def _parse_batch_episodes(self, html):
        """Parse the magnet links, episode numbers, and vid resolutions of
        episodes contained in their batches from html from request formed by
        class static variable

        :param html:
        :return:
        """
        soup = BeautifulSoup(html, 'lxml')

        all_episodes_divs = soup.find_all(
            name='a', attrs={'class': 'rls-label'})

        # iterate through each episode html div
        for episode_div in all_episodes_divs:
            episode_range = episode_div.find(name='strong').text
            first_ep_number, last_ep_numb = episode_range.split('-')
            vid_res = episode_div.contents[-1].text

            episode_range = list(range(
                int(first_ep_number), int(last_ep_numb) + 1))

            links_div = episode_div.next_sibling

            # highest res is the last one by their convention
            highest_res_div = links_div.contents[-1]
            magnet_url = highest_res_div.find(name='a').attrs['href']

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
        episode = {
            'episode_number': episode_range or episode_number,
            'video_resolution': video_resolution,
            'magnet_url': magnet_url,
        }
        self.episodes.append(episode)

        if episode_range:
            self.episode_numbers_collected.update(set(episode_range))
        else:
            self.episode_numbers_collected.add(episode_number)
        # print(sorted(self.episode_numbers_collected))

        self.logger.debug('added episode: {}'.format(episode))

    def _get_most_recent_episode_number(self, url):
        html = self.get_html(url)
        soup = BeautifulSoup(html, "lxml")

        episode_tag = soup.find(name='a', attrs={"class": "rls-label"})
        if episode_tag is None:
            raise HorribleSubsException("there are no individual episodes")

        text_tag = episode_tag.find(name="strong")
        return text_tag.string

    def download(self, r):
        """Downloads every episode in self.episodes"""
        for episode in self.episodes:
            if sys.platform == "win32" or sys.platform == "cygwin":
                os.startfile(episode['magnet_url'])
            else:
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, episode['magnet_url']])


if __name__ == "__main__":
    # standard modern 12-13 ep. anime
    # scraper = EpisodesScraper(show_id=731, debug=True)  # 91 days anime
    # scraper = EpisodesScraper(show_url='http://horriblesubs.info/shows/91-days/', debug=True)

    # anime with extra editions of episodes
    # scraper = EpisodesScraper(show_url='http://horriblesubs.info/shows/psycho-pass/', debug=True)

    # anime with 175 episodes all in 1 batch
    scraper = EpisodesScraper(show_url='https://horriblesubs.info/shows/fairy-tail/', debug=True)
    # scraper.download()

    # anime with 495 episodes
    # scraper = EpisodesScraper(show_url='http://horriblesubs.info/shows/naruto-shippuuden', debug=True)
    # scraper.download()
