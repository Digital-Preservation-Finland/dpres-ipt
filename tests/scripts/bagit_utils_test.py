"""tests for bagit_util-commandline interface."""
import shutil

import pytest

from ipt.aiptools.bagit import BagitError
from ipt.scripts.bagit_util import main


def test_main(bagit_no_manifest_fx, manifest_fx):
    """test cases for main funtions commandline interface."""
    assert main(['make_manifest', str(bagit_no_manifest_fx)]) == 0

    manifest_path = bagit_no_manifest_fx / 'manifest-md5.txt'

    with open(bytes(manifest_path), 'rb') as infile:
        assert manifest_fx == infile.read()


def test_main_missing_datadir(bagit_no_manifest_fx):
    """Test command line utility with missing data directory"""
    shutil.rmtree(bytes(bagit_no_manifest_fx / "data"))
    with pytest.raises(BagitError):
        main(['make_manifest', str(bagit_no_manifest_fx)])

    manifest_path = bagit_no_manifest_fx / 'manifest-md5.txt'
    assert not manifest_path.exists()
