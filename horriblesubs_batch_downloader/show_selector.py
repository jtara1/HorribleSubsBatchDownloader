import sys
import json


class NoMatchingShowException(Exception):
    """Exception for when no show could be matched"""
    pass


class ShowSelector(object):

    horriblesubs_url = 'http://horriblesubs.info'
    py_version = sys.version[0]

    def __init__(self, shows_file, search_key_word, debug=False):
        """Given a list of dictionaries with keys 'name' and 'url_extension' and a search_key_word,
        determine which show the user would like
        e.g. of show data: {"url_extension": "/shows/91-days", "name": "91 Days"}

        :param shows_file: file containing shows (list of dictionaries)
        :param search_key_word: (string) used to select a show
        :param debug: if true, prints additional info
        """
        self.debug = debug
        self._file = open(shows_file)
        self.search_key_word = search_key_word
        self.matches = []  # matching shows
        self._desired_show = None  # the show the user wants

        self.process_search_key_word()
        self.get_matching_show()
        self._file.close()

    def process_search_key_word(self):
        """Replace spaces with hyphen, lowercase letters, and throw out non-alpha or non-digits"""
        new_word = ""
        self.search_key_word = self.search_key_word.lower().replace(" ", "-")

        for letter in self.search_key_word:
            if letter.isalpha() or letter.isdigit() or letter == '-':
                new_word += letter
        self.search_key_word = new_word

        if self.debug:
            print("search_key_word = {}".format(new_word))

    def get_matching_show(self):
        """Iterates through all the shows and adds each match to self.matches then determines the desired show the user
        wants
        """
        all_shows = json.load(self._file)
        for show in all_shows:
            print(show)
            if 'url_extension' in show and self.search_key_word in show['url_extension']:
                self.matches.append(show)

        # determine which show the user wanted
        if len(self.matches) > 1:
            self._desired_show = self._select_a_show_from_matches()
        elif len(self.matches) == 1:
            self._desired_show = self.matches[0]
        else:
            raise NoMatchingShowException(
                "search key word, {}, not found in the list of shows".format(self.search_key_word))

    def _select_a_show_from_matches(self, message=""):
        """Iterates through all matching shows then asks user which show he wants"""
        for counter, show in enumerate(self.matches):
            print("[" + str(counter) + "] " + show['name'])
        print(message)

        msg_for_user_input = "Enter number to select a show: "
        user_input = raw_input(msg_for_user_input) if self.py_version == '2' else input(msg_for_user_input)
        if not user_input.isdigit() or not int(user_input) in range(len(self.matches)):
            return self._select_a_show_from_matches("You did not enter a proper digit.")
        else:
            return self.matches[int(user_input)]

    def get_desired_show_url(self):
        return self.horriblesubs_url + self._desired_show['url_extension']


if __name__ == "__main__":
    import os
    file_path = os.path.join(os.getcwd(), 'tmp/shows.txt')
    proc = ShowSelector(file_path, 'jojo')
    print(proc._desired_show)
    print(proc.get_desired_show_url())
