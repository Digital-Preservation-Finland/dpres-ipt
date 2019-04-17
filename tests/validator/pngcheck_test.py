"""Test the ipt.validator.pngcheck module"""

import os

import ipt.validator.pngcheck


def validate(filename, create_scraper_obj):
    """Return validator with given filename"""

    metadata_info = {
        "filename": os.path.join(
            'tests/data/02_filevalidation_data/png', filename),
        "format": {
            "mimetype": 'image/png',
            "version": '1.2'}}
    scraper_obj = create_scraper_obj(metadata_info)
    val = ipt.validator.pngcheck.Pngcheck(metadata_info,
                                          scraper_obj=scraper_obj)
    val.validate()
    return val


def test_pngcheck_valid(create_scraper_obj):
    """Test valid PNG file"""

    val = validate('valid.png', create_scraper_obj)

    assert val.is_valid


def test_pngcheck_invalid(create_scraper_obj):
    """Test corrupted PNG file"""

    val = validate('invalid.png', create_scraper_obj)

    assert not val.is_valid
