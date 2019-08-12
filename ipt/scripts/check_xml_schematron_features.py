#!/usr/bin/python
# -*- encoding:utf-8 -*-
# vim:ft=python
from __future__ import print_function, unicode_literals
import os
import sys
import optparse

import six
from file_scraper.scraper import Scraper

from ipt.utils import concat


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
    scraper.detect_filetype()

    messages, errors = [], []
    if scraper.mimetype == 'text/xml':
        scraper.scrape()
        schematron_info = next((info for info in six.itervalues(scraper.info)
                                if info['class'] == 'SchematronScraper'), None)
        if schematron_info:
            messages.append(schematron_info['messages'])
            errors.append(schematron_info['errors'])
        else:
            errors.append('ERROR: Could not find SchematronScraper info.')
    else:
        errors.append('ERROR: {} does not appear to be XML (found '
                      'mimetype {}).'.format(filename, scraper.mimetype))

    message_string = concat(messages).strip()
    error_string = concat(errors).strip()
    if message_string:
        print(message_string)
    if error_string:
        print(error_string, file=sys.stderr)

    if error_string or not scraper.well_formed:
        return 117

    return 0


if __name__ == '__main__':
    # If run from the command line, take out the program name from sys.argv
    RETVAL = main(sys.argv[1:])
    sys.exit(RETVAL)
