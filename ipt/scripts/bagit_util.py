#!/usr/bin/python
# vim:ft=python
"""Command line utility to create bagit manifests for AIP packages.

Usage instructions::

    bagit_util make_manifest <sip directory>

On successful operation returns exit status 0.
On system error returns exit status != 0.

.. _Bagit: http://en.wikipedia.org/wiki/BagIt
.. _`Bagit specification`:
    http://www.digitalpreservation.gov/documents/bagitspec.pdf

For more information see the :mod:`aiptools.bagit` module.

"""

import sys
import argparse

from ipt.aiptools.bagit import make_manifest, write_manifest, \
    write_bagit_txt, check_directory_is_bagit, check_bagit_mandatory_files


def main(arguments=None):
    """Parse command line arguments and run application.
    :arguments: Commandline parameters.
    :returns: 0 if all ok, otherwise BagitError(or other exception) is risen"""

    usage = "usage: bagit_util make_manifest <sip_path>"
    parser = argparse.ArgumentParser(usage=usage)

    parser.add_argument("make_manifest", help="Write manifest file for bagit")
    parser.add_argument("sip_path", help="Path to SIP directory")

    args = parser.parse_args(arguments)

    if not args.make_manifest == "make_manifest":
        sys.stderr.write("Must provide make_manifest command and SIP directory"
                         " name as parameter\n")
        parser.print_help()
        return 1

    check_directory_is_bagit(args.sip_path)
    manifest = make_manifest(args.sip_path)
    write_manifest(manifest, args.sip_path)
    write_bagit_txt(args.sip_path)
    check_bagit_mandatory_files(args.sip_path)

    return 0


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
