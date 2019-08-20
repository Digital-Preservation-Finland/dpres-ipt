#!/usr/bin/python
# vim:ft=python
"""Command line utility to create bagit manifests for AIP packages.


Usage instructions::

    create-aip <sip directory>

On successful operation returns exit status 0.
On system error returns exit status != 0.

.. _Bagit: http://en.wikipedia.org/wiki/BagIt
.. _`Bagit specification`:
    http://www.digitalpreservation.gov/documents/bagitspec.pdf

For more information see the :mod:`aiptools.bagit` module.

"""

import sys
import optparse

from ipt.aiptools.bagit import make_manifest, write_manifest, \
    write_bagit_txt, check_directory_is_bagit, check_bagit_mandatory_files


def main(arguments=None):
    """Parse command line arguments and run application.
    :arguments: Commandline parameters.
    :returns: 0 if all ok, otherwise BagitError(or other exception) is risen"""

    usage = "usage: %prog make_manifest <sip_path>"
    parser = optparse.OptionParser(usage=usage)
    if not arguments:
        arguments = sys.argv
    (_, args) = parser.parse_args(arguments)

    if len(args) != 3:
        sys.stderr.write("Must provide make_manifest command and SIP directory"
                         " name as parameter\n")
        parser.print_help()
        return 1

    if args[1] != 'make_manifest':
        sys.stderr.write('Wrong arguments, make_manifest must be first '
                         'argument\n')
        parser.print_help()
        return 1

    sip_path = args[2]

    check_directory_is_bagit(sip_path)
    manifest = make_manifest(sip_path)
    write_manifest(manifest, sip_path)
    write_bagit_txt(sip_path)
    check_bagit_mandatory_files(sip_path)

    return 0


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
