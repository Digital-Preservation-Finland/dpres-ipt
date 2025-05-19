#!/usr/bin/python
"""Check fixity for SIP digital objects"""
from __future__ import annotations

import argparse
import errno
import sys
import os

from collections.abc import Generator, Sequence
from typing import Any
import xml_helpers.utils as u
from file_scraper.utils import hexdigest

from ipt.comparator.utils import iter_metadata_info
from ipt.utils import ensure_text


def iter_files(path: os.PathLike) -> Generator[str, None, None]:
    """Iterate all files under path.

    Does not iterate files that are listed in signature.sig file.

    :param path: Path for iterable files
    :returns: Iterable over full paths to
    """

    ignored_files = ['mets.xml', 'varmiste.sig', 'signature.sig']

    for root, _, files in os.walk(path):
        for filename in files:
            if root == path and filename in ignored_files:
                continue
            yield os.path.join(root, filename)


def check_checksums(sip_path: os.PathLike) -> Generator[str, None, None]:
    """Check checksums for all digital objects in METS.

    :param sip_path: The path to the SIP contents
    :returns: Iterable containing all error messages
    """
    checked_files = {}
    mets_path = os.path.join(sip_path, 'mets.xml')
    mets_tree = u.readfile(mets_path)

    for metadata_info in iter_metadata_info(mets_tree, mets_path):
        filename = metadata_info.get("filename")
        checked_files[filename] = None

        error = __validate_checksum(metadata_info, sip_path)
        if error:
            yield error

    for path in iter_files(sip_path):
        if path.endswith("ignore_validation_errors"):
            continue
        if path not in checked_files:
            yield __format_message({'filename': path}, "Nonlisted file",
                                   sip_path)


def __format_message(metadata_info: dict[str, Any],
                     message: str,
                     sip_path: os.PathLike) -> str:
    filename = metadata_info.get("filename")
    relative_path = os.path.relpath(filename, sip_path)
    return f"{message}: {relative_path}"


def __validate_checksum(metadata_info: dict[str, Any],
                        sip_path: os.PathLike) -> str | None:
    filename = metadata_info.get("filename")
    algorithm = metadata_info.get("algorithm")
    expected_digest = metadata_info.get("digest")

    if algorithm is None:
        return __format_message(metadata_info,
                                "Could not find checksum algorithm", sip_path)

    try:
        hex_digest = hexdigest(filename, algorithm)
    except OSError as e:
        if e.errno == errno.ENOENT:
            return __format_message(metadata_info,
                                    "File does not exist", sip_path)
        return None

    if hex_digest.lower() != expected_digest.lower():
        return __format_message(metadata_info, "Invalid Checksum", sip_path)
    print(__format_message(metadata_info, "Checksum OK", sip_path))
    return None


def main(arguments: Sequence[str] | None = None) -> int:
    """Main loop"""

    args = parse_arguments(arguments)

    returncode = 0
    for error_message in check_checksums(ensure_text(args.sip_path)):
        print(error_message)
        returncode = 117

    return returncode


def parse_arguments(
        arguments: Sequence[str] | None = None) -> argparse.Namespace:
    """ Create arguments parser and return parsed command line argumets"""
    parser = argparse.ArgumentParser()
    parser.add_argument('sip_path')
    return parser.parse_args(arguments)


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
