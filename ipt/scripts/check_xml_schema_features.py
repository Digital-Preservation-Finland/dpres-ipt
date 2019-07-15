#!/usr/bin/python
# -*- encoding:utf-8 -*-
# vim:ft=python

from __future__ import print_function
import os
import sys
import optparse

from file_scraper.scraper import Scraper

from ipt.utils import concat


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

    scraper = Scraper(args[0], schema=options.schemapath,
                      catalog_path=catalog_path)
    scraper.scrape()

    # TODO olisiko tämänkaltainen toiminnallisuus tarpeen toteuttaa yhteiseen
    #      käyttöön esim utilsseissa? Nyt copypastakoodia täällä ja
    #      check_xml_schematron_featuresissa, pistetään kondikseen kun haluttu
    #      outputformaatti on päätetty ja on selvää, onko missä(än) muualla
    #      käyttöä.
    messages = []
    errors = []
    for info in scraper.info():
        scraper_class = info["scraper_class"]
        messages.append(scraper_class + ": " + info["messages"])
        errors.append(scraper_class + ": " + info["errors"])

    print(concat(messages), file=sys.stdout)
    print(concat(errors), file=sys.stderr)

    # TODO halutaanko tarkastaa myös tiedostotyyppi ja/tai käytetyt scraperit?
    if not scraper.well_formed:
        return 117

    return 0


if __name__ == '__main__':
    # If run from the command line, take out the program name from sys.argv
    RETVAL = main(sys.argv[1:])
    sys.exit(RETVAL)
