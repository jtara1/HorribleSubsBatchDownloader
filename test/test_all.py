import unittest
from horriblesubs_batch_downloader import main


class Test12EpisodeShow(unittest.TestCase):

    def test_episodes_parsed(self):
        scraper, selector, ep_scraper = main('91 days', None, False)
        assert(ep_scraper.episode_numbers_collected == {'07', '06', '08', '02', '12', '7.5', '04', '11', '05', '01', '10', '13', '03', '09'})
        assert(ep_scraper.show_id == '731')

    def test_usage(self):
        scraper, selector, ep_scraper = main('91 days', None, False, [1, 7.5], 1)
        parsed = set([ep['episode_number'] for ep in ep_scraper.episodes])
        assert(parsed == {'07', '06', '02', '7.5', '04', '05', '01', '03'})
        assert(ep_scraper.show_id == '731')


if __name__ == '__main__':
    unittest.main()