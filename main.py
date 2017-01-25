from settings import main_settings
from shows_scraper import ShowsScraper
from show_selector import ShowSelector
from episodes_scraper import HorribleSubsEpisodesScraper

import os
import sys
import time


def get_command_line_arguments():
    """Returns all cli args joins with '-' char if there are any, otherwise returns the empty string"""
    if len(sys.argv) > 1:
        return "-".join(sys.argv[1:])
    else:
        return ""


def get_age_of_file(file):
    """Returns how much time has passed since the file's creation time in hours"""
    # python_version = sys.version[0]
    # FileNotFoundException = IOError if python_version == '2' else FileNotFoundException
    try:
        # the file is empty
        with open(file, 'r') as f:
            if f.read() == '':
                return sys.maxsize

        file_stats = os.stat(file)
        file_age = time.time() - file_stats.st_ctime  # time in seconds
        return file_age / 3600
    except IOError:  # file does not exist
        return sys.maxsize  # largest number value


def main():
    """Get anime name to from command line args or ask user for show name, scrape the list of shows from HS, scrape the
    magnet links of each episode, and open each link with OS default program that opens magnet links
    """
    def create_new_file(file_path):
        if not os.path.isdir(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        with open(file_path, 'w') as f:
            f.write('')

    py_version = sys.version[0]

    # use cli args if provided
    cli_args_concatenated = get_command_line_arguments()
    if cli_args_concatenated:
        search_key_word = cli_args_concatenated
    else:
        # search_key_word = raw_input("Enter anime to download from HorribleSubs: ")
        msg_for_user_input = "Enter anime to download from HorribleSubs: "
        search_key_word = raw_input(msg_for_user_input) if py_version == '2' else input(msg_for_user_input)

    print("Searching for {} ...".format(search_key_word))

    # output file for shows spider
    shows_file_path = os.path.join(os.getcwd(), 'tmp/shows.txt')
    file_age = get_age_of_file(shows_file_path)

    # the file containing the list of shows does not exist or is expired
    if file_age > main_settings['show_list_expiration']:
        create_new_file(shows_file_path)
        shows_scraper = ShowsScraper(debug=True)
        shows_scraper.save_shows_to_file(file=shows_file_path)

    # get url of show user searched for
    show_selector = ShowSelector(shows_file=shows_file_path, search_key_word=search_key_word)
    show_url = show_selector.get_desired_show_url()

    # scrape the episodes and download all of them in the highest resolution available
    ep_scraper = HorribleSubsEpisodesScraper(show_url=show_url, debug=True)
    # user_input = raw_input("Press enter to proceed to download or [n]o to cancel: ")
    msg_for_user_input = "Press enter to proceed to download or [n]o to cancel: "
    user_input = raw_input(msg_for_user_input) if py_version == '2' else input(msg_for_user_input)
    if user_input == "":
        ep_scraper.download()


if __name__ == "__main__":
    main()
