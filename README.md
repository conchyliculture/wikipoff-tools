# WikipOff-tools

## About
This set of tools are required to build [Wikimedia](https://www.wikimedia.org/) databases for use with [WikipOff](https://github.com/conchyliculture/wikipoff) Android App.

## Getting Started

0. You need python-dev libs to compile pylzma
1. `python convert.py` and follow instructions
2. `adb push wiki.sqlite /mnt/sdcard/fr.renzo.wikipoff/databases/` or your other storage (see [Wikipoff README](https://github.com/conchyliculture/wikipoff/blob/master/README.md))

## Convert.py

Use this script its purpose is to make you life easier:
`python convert.py` and follow instructions

## WikiExtractor.py

I've originally snatched this script from [Here](http://medialab.di.unipi.it/wiki/Wikipedia_Extractor).
It's been VERY HEAVILY refactored for my needs.
Its purpose is to take a Wikimedia XML dump file and convert it to a sqlite database file.
It will:
* Loop over each article and redirect page
* Convert the wikicode to HTML (with the help of lib/wiki<lang>.py files)
* Compress the text using LZMA
* Store it in the database

It's been tested on French, Basque, Friulian, and English dumps.

Example use:

    python WikiExtractor.py -x enwiki-latest-pages-articles.xml -d en.wiki.sqlite

### Troubleshooting

How to fix: `Error: database or disk is full (for example after the VACUUM command)`
SQlite will use PRAGMA temp_store_directory; for its temporary work. It defaults to /tmp.
If your /tmp is lacking some space, you can do:

    sqlite> PRAGMA temp_store_directory = '<some place with disk space>';
    sqlite> PRAGMA temp_store =1;
    sqlite> vacuum;

## WikiConvert.py

This scripts helps tracking converting issues. It's able to parse the raw xml file and, with the use of a helper database (which contains locations of articles in the XML file), displays outputs of the wikicode to HTML conversion.

Examples:
Show the HTML conversion output of an article with title `Algorithme` :

    python ConvertArticle.py  -d helper.sqlite -f /raid/incoming/tests_wiki/frwiki-latest-pages-articles.xml  -t Algorithme

Show the raw wikicode article with title `Algorithme` :

    python ConvertArticle.py  -d helper.sqlite -f /raid/incoming/tests_wiki/frwiki-latest-pages-articles.xml r -t Algorithme -r

The file `helper.sqlite` is required, and will be built if needed.

## split_db.py

This scripts helps spliting huge (read: bigger than FAT32 max file size) sqlite databases into 2

Example:

    python split_db.py -l en -d en.wiki.sqlite

## License
GPLv3. Get it, hack it, compile it, share it.

## Donate
I accept donations in beer, various cryptcoins, angry and happy emails.
* AUR   AH9hYc6BxHNxqGWn21Gmv8Q3ztDtnWurSo
* BTC   1BAaxTvK1jkoFKf7qWF2C6M4UX1y86MxaF
* DGC   DQ1WiuWKwj8g5NYdq8PbzRaVFckm8TX7Sc
* DOGE  DAQhTKVj592GrjbzYgogDyiBAHm6t6HpiQ 
* FTC   6znenYP8Ry3sv1Mr7F2dgkuZmfvWwkgcss
* LTC   LYAaCu2SuPA36QDZrjvYCK8HcVHXxYVmfu
* MOON  2Pb3KvJ61vj9qcCkQj565owveAVuwctfdB
* NVC   4ad6a9Uwim8RhLn9tX4ouLSNGxo5chu2g8
* TIPS  EYKUTRAoum6f4rGxJZaGn8GnZdWs1amHwH
* VTC   VvEZ7iUrZZR8bhFLCyCqA3LbPUiM15oDrj
* WDC   WiCH7zuAwrS4EQ78dJrqrqLb8ESeEmgECc
* YAC   Y2fgdMign7vvjZzztWRZsWzWkJqTHSDat9
* happy emails : wikipoff@renzokuken.eu
* angry emails : devnull@renzokuken.eu
