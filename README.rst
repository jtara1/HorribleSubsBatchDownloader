horriblesubs_batch_downloader
=============================

Often times I find that HorribleSubs does not upload a single torrent
containing all episodes of an anime, or as they call them, *batches*.

This scraper will search all their shows given a search word (via
command line or after prompt during program execution), and download all
episodes of the desired show in the highest resolution available.

Demo
video https://www.youtube.com/watch?v=0FqFxD7GCI8&feature=youtu.be

Features
~~~~~~~~
-  re-uses previous list of shows scraped from the site that gets saved
   in a text file if not expired
-  asks user which show they wanted if there is more than one match
   found

Requirements
~~~~~~~~~~~~

-  Python 3.5+
-  ``xdg-open`` if using Unix
-  Software that can download content from a magnet link (e.g.:
   **transmission**, **tixati**, **BitTorrent**, etc.)

Install
~~~~~~~

``pip install -U horriblesubs-batch-downloader``

or

1. clone this repo
2. ``cd horriblesubs_batch_downloader``
3. ``python setup.py install``


Usage
~~~~~

Here's some examples. There'd actually be prompts for the user to go through
for each one to select the desired show.

::

    hsbd "one piece"
    hsbd jojo
    hsbd naruto
    hsbd --help


Note: it will save the shows in the current working directory ($PWD) and
attempt to load cached info from the HS site so it's better to cd to a directory
like Downloads first.
