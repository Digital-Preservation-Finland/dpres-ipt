"""
This module implements a simplified version of bagit manifest file creation.
Bagit itself is acontainer directory structure developed by
Congress Library. For exact documentation of bagit, please see

    https://github.com/LibraryOfCongress/bagit-python

Here is a brief specification of bagit relevant to this implementation:

Bagit is a container directory structure with a manifest file containing
directory listing with hash values. The purpose of these hash values is to
verify that the data stored in the container is not corrupted. Below is the
directory structure dercibed:

mybagit/
|-- data
|   |-- my_packge
|       |-- images
|           |-- some.jpg
|           |-- other.txt
|-- manifest-md5.txt
|     9e9f7c5bb2315bdbe560f4e167e995a4 data/my_packge/images/some.jpg
|     348a671d663cef32d44a49ed8485efa7 data/my_packge/images/other.txt
|-- bagit.txt
      BagIt-Version: 0.97
      Tag-File-Character-Encoding: UTF-8

bagit.txt contains the version of the module and the encoding of the manifest
file and other optional bagit files(bag-info.txt, tagmanifest-md5.txt,
fetch.txt). Only manifest file and bagit.txt are mandatory. The manifest file
has the hash function described in the name and in this code it is md5.

The module has the following interface and functionalities:

create manifest for a directory:

    bagit.py make_bag <directory>

this results in creation of manifest-md5.txt to the current directory. For
example:

    bagit.py data

creates a manifest file manifest-md5.txt with lines:

    9e9f7c5bb2315bdbe560f4e167e995a4 data/my_packge/images/some.jpg
    348a671d663cef32d44a49ed8485efa7 data/my_packge/images/other.txt
"""

import os

from file_scraper.utils import hexdigest

from ipt.utils import ensure_binary


class BagitError(Exception):
    """Raised when plugin encounters unrecoverable error"""


def make_manifest(bagit_dir):
    """This function creates bagit manifest.
    :bagit_dir: base directory of bagit."""
    manifest = []
    bagit_dir_bytes = ensure_binary(bagit_dir)
    for dir_name, _, file_list in os.walk(bagit_dir_bytes):
        for file_name in file_list:
            path = os.path.join(dir_name, file_name)
            # Manifest should be updated, not re-icluded in new manifest
            if file_name not in [b'manifest-md5.txt', b'bagit.txt']:
                digest = ensure_binary(calculate_md5(path))
                file_path_in_manifest = path.split(bagit_dir_bytes + b'/')[1]
                manifest.append([digest, file_path_in_manifest])
    return manifest


def calculate_md5(file_path):
    """
    This function calculates md5sum for a file.
    :file_path: path of file from which the md5sum is calculated.
    :returns: a string with md5-hexdigest.
    """
    return hexdigest(file_path, algorithm='md5')


def write_manifest(manifest, path):
    """Write mainfest data list to file.
    :manifest: list of lists which each contain line in manifest as string.
    :path: bagit path where manifest file should be written.
    :returns: None"""
    manifest_path = os.path.join(path, 'manifest-md5.txt')
    with open(manifest_path, 'wb') as outfile:
        for line in manifest:
            outfile.write(
                f"{ensure_binary(line[0])}, {ensure_binary(line[1])}\n"\
                .encode("utf-8"))


def write_bagit_txt(path):
    """Write bagit.txt
    :path: bagit path where bagit.txt file should be written.
    :returns: None
    """
    bagit_path = os.path.join(path, 'bagit.txt')
    with open(bagit_path, 'w', encoding='utf-8') as outfile:
        outfile.write(
            'BagIt-Version: 0.97\nTag-File-Character-Encoding: UTF-8\n')


def check_directory_is_bagit(bagit_dir):
    """Verify that directory is bagit complilant(has data directory).
    :bagit_dir: Directory of bagit.
    :returns: 0 if ok, raise BagitError otherwise."""
    if not os.path.isdir(bagit_dir):
        raise BagitError('bagit directory is not directory.')
    data_dir = os.path.join(bagit_dir, 'data')
    if not os.path.isdir(data_dir):
        raise BagitError('bagit directory is missing data directory.')
    return 0


def check_bagit_mandatory_files(bagit_dir):
    """Verify that mandatory bagit files exist.
    :bagit_dir: Directory of bagit.
    :returns: 0 if ok, raise BagitError otherwise."""
    dirs_list = os.listdir(bagit_dir)
    if not {'manifest-md5.txt', 'bagit.txt'}.issubset(set(dirs_list)):
        raise BagitError(f"Directory {bagit_dir} "
                         "is not bagit format compilant. "
                         "manifest-md5.txt and bagit.txt should exist.")
    return 0
