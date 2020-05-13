import click
from six.moves import input

from horriblesubs_batch_downloader.show_selector import ShowSelector
from horriblesubs_batch_downloader.shows_scraper import ShowsScraper
from horriblesubs_batch_downloader.episodes_scraper import EpisodesScraper


def main(search_word, cache_dir, download, range, quality):
    """Entry point to run the program. Scrapes the names and links to all the
    shows they have. Uses the user's give search_word to select a show.
    Scrapes the magnet links for the highest resolution episodes for the show.

    :param search_word: <str> the name of the show the user wants to download
    :param download: <bool> continue to download once the show is selected
    and the episodes are scraped
    :param range:
    :param quality:
    :return: <ShowScraper, ShowSelector, EpisodesScraper> tuple of objects
    """

    # scraping list of shows
    scraper = ShowsScraper()
    shows_file = scraper.save_shows_to_file(cache_dir)

    # selecting a show
    selector = ShowSelector(shows_file, search_word)
    show_url = selector.get_desired_show_url()

    # scraping all the episodes for the show
    ep_scraper = EpisodesScraper(show_url=show_url, debug=True, range=range, quality=quality)

    if download and input('Press [enter] to download {}'.format(
            selector.desired_show['name'])) == '':
        ep_scraper.download(range)

    return scraper, selector, ep_scraper


@click.command()
@click.argument('search_word')
@click.option('--cache-dir', type=click.STRING, default='',
              help='directory in which the list of shows is cached')
@click.option('--download/--no-download', default=True,
              help='flag to prevent downloading (opening of magnet links)')
@click.option('--range', "--r", "range", nargs=2, default=(None, None), type=str,
              help='sets a range of files to download')
@click.option('--quality', "--q", "quality", default=2, type=int,
              help='sets quality of file to download. can use 0, 1, 2 for 480, 720, and 1080p respectively.')
def main_cli_wrapped(search_word, cache_dir, download, r, qual):
    main(search_word, cache_dir, download, r, qual)


if __name__ == '__main__':
    main_cli_wrapped()
