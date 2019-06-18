"""Tests for PythonCsv validator"""

import os
import lxml.etree
from io import open
from tempfile import NamedTemporaryFile

import pytest

from ipt.validator.csv_validator import PythonCsv
from ipt.addml.addml import to_dict
from ipt.utils import ensure_binary

PDF_PATH = os.path.join(
    'tests/data/02_filevalidation_data/pdf_1_4/sample_1_4.pdf')

ADDML_PATH = os.path.join('tests', 'data', 'addml', 'addml.xml')

VALID_CSV = (
    '''1997,Ford,E350,"ac, abs, moon",3000.00\n'''
    '''1999,Chevy,"Venture ""Extended Edition""","",4900.00\n'''
    '''1999,Chevy,"Venture ""Extended Edition, Very Large""",,5000.00\n'''
    '''1996,Jeep,Grand Cherokee,"MUST SELL!\n'''
    '''air, moon roof, loaded",4799.00\n''')

VALID_WITH_HEADER = \
    'year,brand,model,detail,other\n' + VALID_CSV

MISSING_END_QUOTE = VALID_CSV + \
                    '1999,Chevy,"Venture ""Extended Edition"","",4900.00\n'

DEFAULT_FORMAT = {
    "mimetype": "text/csv",
    "version": "",
    "charset": "UTF-8"}

DEFAULT_ADDML = {
    "charset": "UTF-8",
    "separator": "CR+LF",
    "delimiter": ",",
    "header_fields": ""}


def run_validator(csv_text, addml=None, file_format=None, metadata_info=None,
                  scraper_obj_func=None):
    """Write test data and run csv validation for the file"""

    if addml is None:
        addml = DEFAULT_ADDML

    if file_format is None:
        file_format = DEFAULT_FORMAT

    with NamedTemporaryFile(delete=False) as outfile:

        try:
            outfile.write(ensure_binary(csv_text))
            outfile.close()

            if metadata_info is None:
                metadata_info = {
                    "format": file_format,
                    "addml": addml
                }

            metadata_info["filename"] = outfile.name
            scraper_obj = scraper_obj_func(metadata_info)
            validator = PythonCsv(metadata_info, scraper_obj)
            validator.validate()
        finally:
            os.unlink(outfile.name)

    return validator, scraper_obj


@pytest.mark.usefixtures('monkeypatch_scraper_mime_csv')
def test_valid_created_addml(create_scraper_obj):
    """Test that CSV validator can handle the ADDML given from addml.py"""
    addml_tree = lxml.etree.parse(ADDML_PATH)
    addml = to_dict(addml_tree)
    validator, scraper_obj = run_validator("name; email", addml['addml'],
                                           scraper_obj_func=create_scraper_obj)

    assert validator.is_valid


@pytest.mark.usefixtures('monkeypatch_scraper_mime_csv')
def test_valid_no_header(create_scraper_obj):
    """Test the validator with valid data from Wikipedia's CSV article"""

    validator, scraper_obj = run_validator(VALID_CSV,
                                           scraper_obj_func=create_scraper_obj)

    assert validator.is_valid


@pytest.mark.usefixtures('monkeypatch_scraper_mime_csv')
def test_valid_with_header(create_scraper_obj):
    """Test valid CSV with headers"""

    addml = {
        "charset": "UTF-8",
        "separator": "CR+LF",
        "delimiter": ",",
        "header_fields": ["year", "brand", "model", "detail", "other"]
    }

    validator, scraper_obj = run_validator(VALID_WITH_HEADER, addml,
                                           scraper_obj_func=create_scraper_obj)

    assert validator.is_valid


@pytest.mark.usefixtures('monkeypatch_scraper_mime_csv')
def test_single_field_csv(create_scraper_obj):
    """Test CSV which contains only single field.

    Here we provide original data, but use different field separator

    """
    addml = {
        "charset": "UTF-8",
        "separator": "CR+LF",
        "delimiter": ";",
        "header_fields": ["year,brand,model,detail,other"]}

    validator, scraper_obj = run_validator(VALID_WITH_HEADER, addml,
                                           scraper_obj_func=create_scraper_obj)

    assert validator.is_valid


@pytest.mark.usefixtures('monkeypatch_scraper_mime_csv')
def test_missing_header(create_scraper_obj):
    """Test in invalid csv validation"""

    addml = {
        "charset": "UTF-8",
        "separator": "CR+LF",
        "delimiter": ",",
        "header_fields": ["MISSING HEADER"]}

    validator, scraper_obj = run_validator(VALID_WITH_HEADER, addml,
                                           scraper_obj_func=create_scraper_obj)

    assert not validator.is_valid


def test_pdf_as_csv(create_scraper_obj):
    """Test CSV validator with PDF files"""

    validator, scraper_obj = run_validator(open(PDF_PATH, 'rb').read(),
                                           scraper_obj_func=create_scraper_obj)

    assert not validator.is_valid


@pytest.mark.usefixtures('monkeypatch_scraper_mime_csv')
def test_missing_end_quote(create_scraper_obj):
    """Test missing end quote"""

    validator, scraper_obj = run_validator(MISSING_END_QUOTE,
                                           scraper_obj_func=create_scraper_obj)

    assert not validator.is_valid


@pytest.mark.usefixtures('monkeypatch_scraper_mime_csv')
def test_invalid_field_delimiter(create_scraper_obj):
    """Test different field separator than defined in addml"""

    addml = {
        "charset": "UTF-8",
        "separator": "CR+LF",
        "delimiter": ";",
        "header_fields": ["year", "brand", "model", "detail", "other"]}

    validator, scraper_obj = run_validator(VALID_WITH_HEADER, addml,
                                           scraper_obj_func=create_scraper_obj)

    assert not validator.is_valid


@pytest.mark.usefixtures('monkeypatch_scraper_mime_csv')
def test_invalid_missing_addml_metadata_info(create_scraper_obj):
    """Test valid CSV without providing ADDML data in metadata_info"""

    addml = {
        "charset": "UTF-8",
        "separator": "CR+LF",
        "delimiter": ",",
        "header_fields": ["year", "brand", "model", "detail", "other"]
    }
    metadata_info = {
        "format": DEFAULT_FORMAT
    }

    validator, scraper_obj = run_validator(VALID_WITH_HEADER, addml,
                                           metadata_info=metadata_info,
                                           scraper_obj_func=create_scraper_obj)

    assert not validator.is_valid
