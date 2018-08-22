import click
from six.moves import input

from horriblesubs_batch_downloader.show_selector import ShowSelector
from horriblesubs_batch_downloader.shows_scraper import ShowsScraper
from horriblesubs_batch_downloader.episodes_scraper import EpisodeScraper


def main(search_word, cache_dir, download):
    """Entry point to run the program. Scrapes the names and links to all the
    shows they have. Uses the user's give search_word to select a show.
    Scrapes the magnet links for the highest resolution episodes for the show.

    :param search_word: <str> the name of the show the user wants to download
    :param download: <bool> continue to download once the show is selected
    and the episodes are scraped
    :return: <ShowScraper, ShowSelector, EpisodesScraper> tuple of objects
    """

    # scraping list of shows
    scraper = ShowsScraper()
    shows_file = scraper.save_shows_to_file(cache_dir)

    # selecting a show
    selector = ShowSelector(shows_file, search_word)
    show_url = selector.get_desired_show_url()

    ep_scraper = None

    if download and input('Press [enter] to download {}'.format(
            selector.desired_show['name'])) == '':

        # scraping all the episodes for the show
        ep_scraper = EpisodeScraper(show_url=show_url, debug=True)
        ep_scraper.download()

    return scraper, selector, ep_scraper


@click.command()
@click.argument('search_word')
@click.option('--cache-dir', type=click.STRING, default='')
@click.option('--download', type=click.BOOL, default=True)
def main_cli_wrapped(search_word, cache_dir, download):
    main(search_word, cache_dir, download)


if __name__ == '__main__':
    main_cli_wrapped()
