"""
Tests for DPX validator.
"""

import os
import pytest
from ipt.validator.dpxv import DPXv

BASEPATH = "tests/data/02_filevalidation_data/dpx"


@pytest.mark.parametrize(
    ['filename', 'mimetype', 'version'],
    [
        ("valid_dpx.dpx", "image/x-dpx", "2.0")
    ]
)
def test_validate_valid_file(filename, mimetype, version, create_scraper_obj):
    metadata_info = {
        'filename': os.path.join(BASEPATH, filename),
        'format': {
            'mimetype': mimetype,
            'version': version
        }
    }
    scraper_obj = create_scraper_obj(metadata_info)
    validator = DPXv(metadata_info, scraper_obj)
    validator.validate()
    assert validator.is_valid and scraper_obj.well_formed


@pytest.mark.parametrize(
    ['filename', 'mimetype', 'version'],
    [
        ("corrupted_dpx.dpx", "image/x-dpx", "2.0"),
        ("empty_file.dpx", "image/x-dpx", "2.0"),
    ]
)
def test_validate_invalid_file(filename, mimetype, version, create_scraper_obj):
    metadata_info = {
        'filename': os.path.join(BASEPATH, filename),
        'format': {
            'mimetype': mimetype,
            'version': version
        }
    }

    scraper_obj = create_scraper_obj(metadata_info)
    validator = DPXv(metadata_info, scraper_obj)
    validator.validate()
    assert not validator.is_valid and not scraper_obj.well_formed
