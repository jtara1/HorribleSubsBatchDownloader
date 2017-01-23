# HorribleSubsBatchDownloader

Often times I find that HorribleSubs does not upload a single torrent
containing all episodes of an anime, or as they call them, _batches_.

This scraper will search all their shows given a search word (via
command line or after prompt during program execution), and download all
episodes of the desired show in the highest resolution available.

[Demo video](https://www.youtube.com/watch?v=0FqFxD7GCI8&feature=youtu.be)


### Features

* re-uses previous list of shows scraped from the site that gets saved
in a text file if not expired
* asks user which show they wanted if there is more than one match
found


### Requirements

* Python 2.7 or Python 3
* `xdg-open` if using Unix
* Software that can download content from a magnet link (e.g.:
__transmission__, __tixati__, __BitTorrent__, etc.)

##### Modules

* cfscrape
* requests
* bs4


### Usage

Run `main.py` to run the program, and optionally enter anime name
as cli arguments as seen in the 2nd example.

e.g.:

```
python main.py
```

or

```
python main.py one piece
```