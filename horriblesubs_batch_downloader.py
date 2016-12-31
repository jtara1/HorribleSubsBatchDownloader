from urllib.request import urlretrieve
import sys


class HorribleSubsBatchDownloader:

    shows_url = "http://horriblesubs.info/shows/"

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.get_command_line_arguments()

    def get_command_line_arguments(self):
        args = sys.argv[1:]
        self.process_command_line_arguments(args)

    def process_command_line_arguments(self, args):
        search_keyword = "-".join(args).lower().replace("'", "")
        if self.verbose:
            print("Searching for: {}".format(search_keyword))


if __name__ == "__main__":
    downloader = HorribleSubsBatchDownloader()