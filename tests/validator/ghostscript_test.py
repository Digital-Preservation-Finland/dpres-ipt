"""
Test for pdf 1.7 ghostscript validator.
"""

import os

from ipt.validator.ghostscript import GhostScript

BASEPATH = "tests/data/02_filevalidation_data"

FILEINFO = {
    "filename": "",
    "format": {
        "version": "1.7",
        "mimetype": "application/pdf"
    }
}


def test_pdf_1_7_ok(create_scraper_obj):
    """
    test pdf 1.7 ok case
    """
    FILEINFO["filename"] = os.path.join(BASEPATH, "pdf_1_7", "valid_1_7.pdf")
    scraper_obj = create_scraper_obj(FILEINFO)
    validator = GhostScript(FILEINFO, scraper_obj=scraper_obj)
    validator.validate()
    assert validator.is_valid


def test_pdf_1_7_validity_error(create_scraper_obj):
    """
    test pdf 1.7 invalid case
    """
    FILEINFO["filename"] = os.path.join(BASEPATH, "pdf_1_7", "invalid_1_7.pdf")
    scraper_obj = create_scraper_obj(FILEINFO)
    validator = GhostScript(FILEINFO, scraper_obj=scraper_obj)
    validator.validate()
    assert not validator.is_valid


def test_pdf_1_7_version_error(create_scraper_obj):
    """
    test pdf 1.7 wrong version case
    """
    FILEINFO["filename"] = os.path.join(BASEPATH, "pdf_1_7",
                                        "invalid_wrong_version.pdf")
    scraper_obj = create_scraper_obj(FILEINFO)
    validator = GhostScript(FILEINFO, scraper_obj=scraper_obj)
    validator.validate()
    assert not validator.is_valid


def test_pdfa_valid(create_scraper_obj):
    """Test that valid PDF/A is valid
       This file is also used in veraPDF test, where it should result "valid".
    """
    FILEINFO["filename"] = os.path.join(BASEPATH, "pdfa-1", "valid.pdf")
    FILEINFO["format"]["version"] = "A-1b"
    scraper_obj = create_scraper_obj(FILEINFO)
    validator = GhostScript(FILEINFO, scraper_obj=scraper_obj)
    validator.validate()
    assert validator.is_valid


def test_pdf_invalid_pdfa_invalid(create_scraper_obj):
    """Test that valid PDF (but invalid PDF/A) is valid.
       This file is also used in veraPDF test, where it should result
       "invalid".
    """
    FILEINFO["filename"] = os.path.join(BASEPATH, "pdfa-1", "invalid.pdf")
    FILEINFO["format"]["version"] = "A-1b"
    scraper_obj = create_scraper_obj(FILEINFO)
    validator = GhostScript(FILEINFO, scraper_obj=scraper_obj)
    assert not validator.is_valid
