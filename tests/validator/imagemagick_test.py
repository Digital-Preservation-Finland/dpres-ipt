"""
Tests for ImageMagick validator.
"""

import os
import pytest
from ipt.validator.imagemagick import ImageMagick

BASEPATH = "tests/data/02_filevalidation_data/imagemagick"


@pytest.mark.parametrize(
    ['filename', 'mimetype', 'version'],
    [
        ("valid_jpeg.jpeg", "image/jpeg", "1.01"),
        ("valid_jp2.jp2", "image/jp2", ""),
        pytest.param("valid_tiff.tiff", "image/tiff", "6.0",
                     marks=(pytest.mark.skip('Pillow 6.0.0 raises an error'))),
        ("valid_png.png", "image/png", "1.2"),
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
    validator = ImageMagick(metadata_info, scraper_obj=scraper_obj)
    validator.validate()
    assert validator.is_valid


@pytest.mark.parametrize(
    ['filename', 'mimetype', 'version'],
    [
        ("valid_png.png", "image/tiff", "6.0")
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
    validator = ImageMagick(metadata_info, scraper_obj=scraper_obj)
    validator.validate()
    assert not validator.is_valid
