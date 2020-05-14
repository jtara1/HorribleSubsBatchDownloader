#!/bin/bash
# needs testing

if [[ ${PWD##*/} != 'horriblesubs_batch_downloader' ]]; then
	echo wrong dir
	exit 1
fi

rm -rf ./dist
python setup.py sdist
twine upload dist/*
