import click
from six.moves import input

from horriblesubs_batch_downloader.show_selector import ShowSelector
from horriblesubs_batch_downloader.shows_scraper import ShowsScraper
from horriblesubs_batch_downloader.episodes_scraper import HorribleSubsEpisodesScraper


@click.command()
@click.argument('search_word')
def main(search_word):

    # scraping list of shows
    scraper = ShowsScraper()
    shows_file = scraper.save_shows_to_file()

    # selecting a show
    selector = ShowSelector(shows_file, search_word)
    show_url = selector.get_desired_show_url()

    if input('Press [enter] to download {}'.format(
            selector._desired_show['name'])) == '':

        # scraping all the episodes for the show
        ep_scraper = HorribleSubsEpisodesScraper(show_url=show_url, debug=True)
        ep_scraper.download()


if __name__ == '__main__':
    main()
