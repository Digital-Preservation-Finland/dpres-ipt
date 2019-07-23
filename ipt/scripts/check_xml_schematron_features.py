#!/usr/bin/python
# -*- encoding:utf-8 -*-
# vim:ft=python
from __future__ import print_function
import os
import sys
import optparse

from file_scraper.scraper import Scraper

from ipt.utils import concat, get_scraper_info


def main(arguments=None):
    """Main loop"""
    usage = "usage: %prog [options] xml-file-path"

    parser = optparse.OptionParser(usage=usage)

    parser.add_option("-s", "--schemapath", dest="schemapath",
                      help="Path to schematron schemas",
                      metavar="PATH")

    (options, args) = parser.parse_args(arguments)

    if len(args) != 1:
        parser.error("Must give a path to an XML file as argument")

    if options.schemapath is None:
        parser.error("The -s switch is required")

    filename = args[0]

    if os.path.isdir(filename):
        filename = os.path.join(filename, 'mets.xml')

    scraper = Scraper(filename, schematron=options.schemapath)
    scraper.scrape()

    messages, errors = get_scraper_info(scraper)

    print(concat(messages))
    print(concat(errors), file=sys.stderr)

    # TODO halutaanko tarkastaa myös tiedostotyyppi ja/tai käytetyt scraperit?
    if not scraper.well_formed:
        return 117

    return 0


if __name__ == '__main__':
    # If run from the command line, take out the program name from sys.argv
    RETVAL = main(sys.argv[1:])
    sys.exit(RETVAL)
