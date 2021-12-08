"""tests for bagit_util-commandline interface."""

import pytest

from ipt.aiptools.bagit import BagitError
from ipt.scripts.bagit_util import main


def test_main(bagit_fx):
    """test cases for main funtions commandline interface."""
    assert main(['make_manifest', str(bagit_fx)]) == 0


def test_main_missing_datadir(bagit_fx):
    """Test command line utility with missing data directory"""
    (bagit_fx / "data").remove(rec=1)
    with pytest.raises(BagitError):
        main(['make_manifest', str(bagit_fx)])


def test_main_diacritic(diacritic_bagit_path):
    """Test a regression case where special character named file caused issues.
    """
    assert main(['make_manifest', diacritic_bagit_path]) == 0
