# WikipOff-tools

## About

This set of tools are required to build [Wikimedia](https://www.wikimedia.org/) databases for use with [WikipOff](https://github.com/conchyliculture/wikipoff) Android App.

## Getting Started

0. You need python-dev libs to compile pylzma
1. Download a WikiMedia XML dump file (ie: [from wikipedia.com](https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2)). Decompress it if needed.
2. `python WikiConverter.py dump.xml wiki.sqlite` and follow instructions
3. `adb push wiki.sqlite /mnt/sdcard/fr.renzo.wikipoff/databases/` or your other Android storage (see [Wikipoff README](https://github.com/conchyliculture/wikipoff/blob/master/README.md))


## WikiConverter.py

Takes a Wikimedia XML dump file and convert it to a sqlite database file.

It will:
* Parse the XML dump, to extract the wikicode
* Convert the wikicode to HTML
* Compress the text using LZMA
* Store it in the SQLite database

It's been tested on French, Basque, Friulian, and English dumps.

Example use:

    python WikiConverter.py enwiki-latest-pages-articles.xml en.wiki.sqlite

This can take a few eons even on a buffed up system. It will also use all your CPUs, and RAM.

### Performance

I try to use all resources available to do the stuff.

To get an overview, converting a small wikipedia (fur) with no fancy translation, I get the following:

| Number of articles | Fancy conversions | i5-4210U @ 1.70GHz(4t) 8G RAM  | i7-47700U @ 3.40GHz(8t) 16G RAM |
|--------------------|-------------------|--------------------------------|---------------------------------|
| 5k~ (fur.wiki)     | No                | ~20s                           | ~8s                             |
| 600k~ (eu.wiki)    | No                | ~35min                         | ~14min                          |
| 1.9M~ (fr.wiki)    | Yes               | ????                           | ~67min                          |

### Troubleshooting

How to fix: `Error: database or disk is full (for example after the VACUUM command)`
SQlite will use PRAGMA temp_store_directory; for its temporary work. It defaults to /tmp.
If your /tmp is lacking some space, you can do:

    sqlite> PRAGMA temp_store_directory = '<some place with disk space>';
    sqlite> PRAGMA temp_store =1;
    sqlite> vacuum;


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
