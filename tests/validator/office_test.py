"""
Tests for Office validator.
"""

import os
import pytest
from multiprocessing import Pool
from file_scraper.scraper import Scraper
from ipt.validator.office import Office


def _metadata_info(filename, mimetype, version):
    basepath = "tests/data/02_filevalidation_data/office"
    return {
        'filename': os.path.join(basepath, filename),
        'format': {
            'mimetype': mimetype,
            'version': version
        }
    }


@pytest.mark.parametrize(
    ['filename', 'mimetype', 'version'],
    [
        ("ODF_Text_Document.odt", "application/vnd.oasis.opendocument.text",
         "1.1"),
        ("ODF_Text_Document.odt", "application/vnd.oasis.opendocument.text",
         "1.2"),
        ("MS_Word_97-2003.doc", "application/msword", "11.0"),
        ("Office_Open_XML_Text.docx",
         "application/vnd.openxmlformats-"
         "officedocument.wordprocessingml.document", "15.0"),
        ("ODF_Presentation.odp",
         "application/vnd.oasis.opendocument.presentation", "1.2"),
        ("MS_PowerPoint_97-2003.ppt", "application/vnd.ms-powerpoint", "11.0"),
        ("Office_Open_XML_Presentation.pptx",
         "application/vnd.openxml"
         "formats-officedocument.presentationml.presentation", "15.0"),
        ("ODF_Spreadsheet.ods",
         "application/vnd.oasis.opendocument.spreadsheet", "1.2"),
        ("MS_Excel_97-2003.xls", "application/vnd.ms-excel", "11.0"),
        ("Excel_Online_Spreadsheet.xlsx",
         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
         "15.0"),
        ("ODF_Drawing.odg", "application/vnd.oasis.opendocument.graphics",
         "1.2"),
        ("ODF_Formula.odf", "application/vnd.oasis.opendocument.formula",
         "1.2"),
        pytest.param("Office_Open_XML_Spreadsheet.xlsx",
                     "application/vnd."
                     "openxmlformats-officedocument.spreadsheetml.sheet",
                     "15.0", marks=(pytest.mark.skip(
                "Scraper is unable to scrape the file successfully"))),
        ("ODF_Text_Document.odt", "application/msword", "11.0"),
        ("ODF_Text_Document_with_wrong_filename_extension.doc",
         "application/msword", "11.0"),
        ("MS_Word_97-2003.doc", "application/msword", "15.0"),
        ("ODF_Text_Document.odt",
         "application/vnd.oasis.opendocument.text", ""),
    ]
)
@pytest.mark.usefixtures('monkeypatch_scraper_version_dict')
def test_validate_valid_file(filename, mimetype, version, create_scraper_obj):
    metadata_info = _metadata_info(filename, mimetype, version)
    scraper_obj = create_scraper_obj(metadata_info)
    validator = Office(metadata_info, scraper_obj=scraper_obj)
    validator.validate()
    assert validator.is_valid


@pytest.mark.parametrize(
    ['filename', 'mimetype', 'version'],
    [
        # Corrupted file
        ("ODF_Text_Document_corrupted.odt",
         "application/vnd.oasis.opendocument.text", "1.2"),
        # .zip renamed to .docx
        ("MS_Word_2007-2013_XML_zip.docx",
         "application/vnd.openxmlformats-"
         "officedocument.wordprocessingml.document", "15.0"),
    ]
)
def test_validate_invalid_file(filename, mimetype, version, create_scraper_obj):
    metadata_info = _metadata_info(filename, mimetype, version)
    scraper_obj = create_scraper_obj(metadata_info)
    validator = Office(metadata_info, scraper_obj=scraper_obj)
    validator.validate()
    assert not validator.is_valid
