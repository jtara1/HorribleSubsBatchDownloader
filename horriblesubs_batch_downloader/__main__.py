import click

from horriblesubs_batch_downloader.show_selector import ShowSelector
from horriblesubs_batch_downloader.shows_scraper import ShowsScraper
from horriblesubs_batch_downloader.episodes_scraper import HorribleSubsEpisodesScraper


@click.command()
@click.argument('search_word')
def main(search_word):
    scraper = ShowsScraper()
    shows_file = scraper.save_shows_to_file()

    selector = ShowSelector(shows_file, search_word)
    show_url = selector.get_desired_show_url()

    ep_scraper = HorribleSubsEpisodesScraper(show_url=show_url, debug=True)
    print(ep_scraper.episodes)
    ep_scraper.download()


if __name__ == '__main__':
    main()
