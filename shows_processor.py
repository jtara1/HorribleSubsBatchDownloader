import simplejson
from __builtin__ import enumerate


class ShowsProcessor(object):

    def __init__(self, shows_file, search_key_word):
        """Given a list of dictionaries with keys 'name' and 'url_extension' and a search_key_word,
        determine which show the user would like

        :param shows_file: file containing shows (list of dictionaries)
        :param search_key_word: (string) used to select a show
        """
        self.file = open(shows_file)
        self.search_key_word = search_key_word
        self.matches = []  # matching shows
        self.desired_show = None  # the show the user wants

        self.get_matching_show()
        self.file.close()

    def get_matching_show(self):
        """Iterates through all the shows and adds each match to self.matches then determines the desired show the user
        wants"""
        all_shows = simplejson.load(self.file)
        # add all shows that matched search_key_word to self.matches
        # for line in self.file:
        for show in all_shows:
            # show = simplejson.loads(line)
            if show['url_extension'] and self.search_key_word in show['url_extension']:
                self.matches.append(show)

        # determine which show the user wanted
        if len(self.matches) > 1:
            self.desired_show = self._select_a_show_from_matches()
        elif len(self.matches) == 1:
            self.desired_show = self.matches[0]

    def _select_a_show_from_matches(self, message=""):
        """Iterates through all matching shows then asks user which show he wants"""
        for counter, show in enumerate(self.matches):
            print("[" + str(counter) + "] " + show['name'])
        print(message)

        user_input = raw_input("Enter number to select a show: ")
        if not user_input.isdigit():
            self._select_a_show_from_matches("You did not enter a digit.")
        else:
            return self.matches[int(user_input)]


if __name__ == "__main__":
    import os
    file_path = os.path.join(os.getcwd(), 'tmp/shows.txt')
    proc = ShowsProcessor(file_path, 'jojo')
    print(proc.desired_show)
