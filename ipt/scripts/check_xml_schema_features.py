#!/usr/bin/python
# vim:ft=python

"""Check well-formedness of XML file and validate against an XML schema."""

import os
import sys
import optparse

from file_scraper.scraper import Scraper

from ipt.utils import concat, get_scraper_info, ensure_text


def main(arguments=None):
    """Main loop"""
    usage = "usage: %prog [options] xml-file-name"
    catalog_path = ("/etc/xml/dpres-xml-schemas/schema_catalogs")
    schema_path = ("/etc/xml/dpres-xml-schemas/schema_catalogs/schemas")

    parser = optparse.OptionParser(usage=usage)

    parser.add_option("-c", "--catalog", dest="catalogpath",
                      default=os.path.join(
                          catalog_path, "catalog_main.xml"),
                      help="Full path to XML catalog file",
                      metavar="FILE")

    parser.add_option("-s", "--schemapath", dest="schemapath",
                      default=os.path.join(schema_path, "mets/mets.xsd"),
                      help="XML schema filename for validation",
                      metavar="PATH")

    (options, args) = parser.parse_args(arguments)

    if len(args) != 1:
        parser.error("Must give XML filename as argument")

    filename = args[0]
    scraper = Scraper(filename, schema=options.schemapath,
                      catalog_path=options.catalogpath,
                      mimetype="text/xml", version="1.0",
                      charset="UTF-8")

    messages, errors = [], []
    scraper.scrape()
    info = get_scraper_info(scraper)
    messages.extend(info['messages'])
    errors.extend(info['errors'])

    if messages:
        print(ensure_text(concat(messages)), file=sys.stdout)
    if errors:
        print(ensure_text(concat(errors)), file=sys.stderr)

    if errors or not scraper.well_formed:
        return 117
    return 0


# pylint: disable=duplicate-code
# Main function can be similar in different scripts
if __name__ == '__main__':
    # If run from the command line, take out the program name from sys.argv
    RETVAL = main(sys.argv[1:])
    sys.exit(RETVAL)
