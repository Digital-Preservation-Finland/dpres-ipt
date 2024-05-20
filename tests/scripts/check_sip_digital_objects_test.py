"""Test the ipt.scripts.check_digital_objects module"""
# TODO add proper testing plan

import os
import uuid

import lxml.etree as ET
import pytest
import premis

import xml_helpers

from file_scraper.iterator import iter_detectors
from file_scraper.scraper import Scraper
from file_scraper.defaults import (
    RECOMMENDED,
    ACCEPTABLE,
    BIT_LEVEL_WITH_RECOMMENDED,
    BIT_LEVEL,
    UNACCEPTABLE,
    UNAV,
    UNAP
)

from tests.testcommon import shell
from tests.testcommon.settings import TESTDATADIR

# Module to test
from ipt.scripts.check_sip_digital_objects import (main,
                                                   validation,
                                                   validation_report,
                                                   make_result_dict,
                                                   join_validation_results)
import ipt.scripts.check_sip_digital_objects
from ipt.scripts.create_schema_catalog import main as schema_main

METSDIR = os.path.abspath(
    os.path.join(TESTDATADIR, 'mets'))

TEST_CASES = [
    {'testcase': 'Invalid digital object.',
     'filename': 'invalid_1.7.1_invalid_object',
     'expected_result': {
         'returncode': 117,
         'stdout': ['ERROR: warc errors at']}},
    {'testcase': 'Invalid xml file submitted as text/xml.',
     'filename': 'invalid_1.7.1_invalid_xml_as_xml',
     'expected_result': {
         'returncode': 117,
         'stdout': ['Failed: document is not well-formed.']}},
    {'testcase': 'Missing digital object.',
     'filename': 'invalid_1.7.1_missing_object',
     'expected_result': {
         'returncode': 117,
         'stdout': [
             'ERROR: File {}/sips/invalid_1.7.1_missing_object/'
             'data/valid_1.2.png does not exist.'.format(TESTDATADIR)]}},
    {'testcase': 'Unsupported mimetype, with version.',
     'filename': 'invalid_1.7.1_unsupported_mimetype',
     'patch': {'mimetype': 'application/kissa',
               'version': '1.01'},
     'expected_result': {
         'returncode': 117,
         'stdout': ['Proper scraper was not found. The file was not '
                    'analyzed.']}},
    {'testcase': 'Unsupported mimetype, without version.',
     'filename': 'invalid_1.7.1_unsupported_mimetype_no_version',
     'patch': {'mimetype': 'application/kissa',
               'version': ''},
     'expected_result': {
         'returncode': 117,
         'stdout': ['Proper scraper was not found. The file was not '
                    'analyzed.']}},
    {'testcase': 'Unsupported version with supported mimetype.',
     'filename': 'invalid_1.7.1_unsupported_version',
     'patch': {'mimetype': 'image/jpeg',
               'version': '3.1415'},
     'expected_result': {
         'returncode': 117,
         'stdout': [("Predefined version '3.1415' and "
                     "resulted version '1.01' mismatch.")]}},
    {'testcase': 'Report alt-format when validating as primary mimetype.',
     'filename': 'valid_1.7.0_plaintext_alt_format',
     'expected_result': {
         'returncode': 0,
         'stdout': ['METS alternative mimetype: text/html',
                    'Validating as mimetype: text/plain',
                    'The digital object will be preserved as '
                    'mimetype: text/plain']}},
    {'testcase': 'Digital object with audiomd metadata.',
     'filename': 'valid_1.7.1_audio_stream',
     'expected_result': {
         'returncode': 0,
         'stdout': []}},
    {'testcase': 'Digital object with mix metadata.',
     'filename': 'valid_1.7.1_image',
     'expected_result': {
         'returncode': 0,
         'stdout': []}},
    {'testcase': 'Invalid xml submitted as valid text/plain.',
     'filename': 'valid_1.7.1_invalid_xml_as_plaintext',
     'expected_result': {
         'returncode': 0,
         'stdout': ['Detected mimetype: text/xml, version: 1.0',
                    'Validating as mimetype: text/plain',
                    'The digital object will be preserved as '
                    'mimetype: text/plain']}},
    {'testcase': 'SIP with multiple digital objects.',
     'filename': 'valid_1.7.1_multiple_objects',
     'expected_result': {
         'returncode': 0,
         'stdout': []}},
    {'testcase': 'Valid plaintext.',
     'filename': 'valid_1.7.1_plaintext',
     'expected_result': {
         'returncode': 0,
         'stdout': []}},
    {'testcase': 'Videocontainer with audiomd/videomd metadata.',
     'filename': 'valid_1.7.1_video_container',
     'expected_result': {
         'returncode': 0,
         'stdout': []}},
    {'testcase': 'Whitespace in sip and digital object names.',
     'filename': 'valid_1.7.1_white space',
     'expected_result': {
         'returncode': 0,
         'stdout': []}},
    {'testcase': 'SIP with local schemas.',
     'filename': 'valid_1.7.1_xml_local_schemas',
     'expected_result': {
         'returncode': 0,
         'stdout': []}},
    {'testcase': 'SIP with filename diacritics.',
     'filename': 'valid_1.7.1_filename_diacritics',
     'expected_result': {
         'returncode': 0,
         'stdout': []}},
    {'testcase': 'SIP with local schema that is not well-formed.',
     'filename': 'invalid_1.7.1_xml_local_schema_not_wellformed',
     'expected_result': {
         'returncode': 117,
         'stdout': ['ERROR: WXS schema']}},
    {'testcase': 'SIP with local schema with missing schema link.',
     'filename': 'invalid_1.7.1_xml_local_schema_invalid_schema_link',
     'expected_result': {
         'returncode': 117,
         'stdout': ['ERROR: warning: failed to load external entity']}},
    {'testcase': 'SIP with text file containing illegal control character.',
     'filename': 'invalid_1.7.2_control_character',
     'expected_result': {
         'returncode': 117,
         'stdout': ['ERROR: Character decoding error: Illegal character']}},
]
"""
This list contains the following cases:
(1) One validation is done for one digital object
(2) Two validations are done for one object
(3) Two validations are done for one digital object and one to another
    (i.e. 2 events for 1 object and 1 event for 1 object)
"""
RESULT_CASES = [
    # One validation event for one object
    [{'is_valid': True, 'messages': 'OK', 'errors': None,
      'metadata_info': {
          'filename': 'file.txt', 'object_id': {
              'type': 'id-type', 'value': 'only-one-object'}}}],
    # Two validation events for one object
    [{'is_valid': True, 'messages': 'OK', 'errors': None,
      'metadata_info': {
          'filename': 'file.txt', 'object_id': {
              'type': 'id-type',
              'value': 'this-id-should-be-added-only-once'}}},
     {'is_valid': True, 'messages': 'OK too', 'errors': None,
      'metadata_info': {
          'filename': 'file.txt', 'object_id': {
              'type': 'id-type',
              'value': 'this-id-should-be-added-only-once'}}}],
    # Two validation events for one object and one event for one object
    [{'is_valid': True, 'messages': 'OK', 'errors': None,
      'metadata_info': {
          'filename': 'file.txt', 'object_id': {
              'type': 'id-type',
              'value': 'this-id-should-be-added-only-once'}}},
     {'is_valid': True, 'messages': 'OK too', 'errors': None,
      'metadata_info': {
          'filename': 'file.txt', 'object_id': {
              'type': 'id-type',
              'value': 'this-id-should-be-added-only-once'}}},
     {'is_valid': True, 'messages': 'OK', 'errors': None,
      'metadata_info': {
          'filename': 'file2.txt', 'object_id': {
              'type': 'id-type',
              'value': 'this-id-should-not-be-forgotten'}}}]
]


def test_testcases_stdout():
    """
    Ensure that all test cases wrap expected stdout message in a list.
    Otherwise test_check_sip_digital_objects will check that the
    individual characters of the expected message can be found in
    stdout, instead of the entire string.
    """
    assert all(isinstance(case['expected_result']['stdout'], list)
               for case in TEST_CASES)


@pytest.mark.parametrize(
    'case', TEST_CASES, ids=[x['testcase'] for x in TEST_CASES])
def test_check_sip_digital_objects(case, tmpdir, monkeypatch):
    """
    Test for check_sip_digital_objects
    """
    try:
        monkeypatch.setattr(Scraper, '_identify',
                            patch_scraper_identify(**case['patch']))
    except KeyError:
        # Nothing to patch.
        pass

    filename = os.path.join(TESTDATADIR, 'sips', case['filename'])

    arguments = [filename, 'preservation-sip-id', str(uuid.uuid4())]
    # Schema cases need their own catalogs created by another script.
    schema_cases = ('valid_1.7.1_xml_local_schemas',
                    'invalid_1.7.1_xml_local_schema_invalid_schema_link')
    if case['filename'] in schema_cases:
        output = tmpdir.join('my_catalog_schema.xml').strpath
        mets = os.path.join(filename, 'mets.xml')
        shell.run_main(schema_main, [mets, filename, output])
        arguments.append('-c')
        arguments.append(output)

    (returncode, stdout, stderr) = shell.run_main(
        main, arguments)

    assert stderr == ''

    for match_string in case['expected_result']['stdout']:
        assert match_string in stdout, stdout

    message = '\n'.join([
        'got:', str(returncode), 'expected:',
        str(case['expected_result']['returncode']),
        'stdout:', stdout, 'stderr:', stderr])

    assert returncode == case['expected_result']['returncode'], message


@pytest.mark.parametrize(
    'results, object_count, event_count',
    [(RESULT_CASES[0], 1, 1),
     (RESULT_CASES[1], 1, 2),
     (RESULT_CASES[2], 2, 3)])
def test_validation_report(monkeypatch, results, object_count, event_count):
    """Test that validation report creates correct number of premis sections"""

    def _validation(*_, **__):
        return (result for result in results)

    monkeypatch.setattr(ipt.scripts.check_sip_digital_objects,
                        'validation',
                        _validation)
    premis_xml = validation_report('sip-path',
                                   'catalog-path',
                                   'sip-type',
                                   'sip-value')
    assert premis.object_count(premis_xml) == object_count
    assert premis.event_count(premis_xml) == event_count
    assert premis.agent_count(premis_xml) == 1


PDF_MD_INFO = {
    'filename': 'pdf',
    'relpath': 'pdf',
    'use': '',
    'errors': None,
    'spec_version': '1.7.3',
    'format': {'mimetype': 'application/pdf', 'version': '1.4'},
    'object_id': {'type': 'test_object', 'value': 'pdf1'},
    'algorithm': 'MD5',
    'digest': 'aa4bddaacf5ed1ca92b30826af257a1b'
}

CDR_MD_INFO = {
    'filename': 'cdr',
    'relpath': 'cdr',
    'use': '',
    'errors': None,
    'spec_version': '1.7.3',
    'format': {'mimetype': 'application/cdr', 'version': '9.0'},
    'object_id': {'type': 'test_object', 'value': 'cdr1'},
    'algorithm': 'MD5',
    'digest': 'aa4bddaacf5ed1ca92b30826af257a1c'
}

NO_VALIDATION = "fi-dpres-no-file-format-validation"
IDENTIFICATION = "fi-dpres-file-format-identification"


@pytest.mark.parametrize(
    ("md_info", "use", "grade", "is_valid"),
    (
        # Recommended file format
        (PDF_MD_INFO, "", RECOMMENDED, True),
        # Recommended file format skip validation
        (PDF_MD_INFO, NO_VALIDATION, RECOMMENDED, False),
        # Acceptable file format
        (PDF_MD_INFO, "", ACCEPTABLE, True),
        # Acceptable file format skip validation
        (PDF_MD_INFO, NO_VALIDATION, ACCEPTABLE, False),
        # Bit level format not marked as native
        (CDR_MD_INFO, "", BIT_LEVEL, False),
        # Bit level recommended format not marked as native
        (CDR_MD_INFO, "", BIT_LEVEL_WITH_RECOMMENDED, False),
        # Bit level format marked as native
        (CDR_MD_INFO, NO_VALIDATION, BIT_LEVEL, True),
        # Bit level format marked as native with identification
        (CDR_MD_INFO, IDENTIFICATION, BIT_LEVEL, True),
        # Bit level recommended format marked as native without identification
        (CDR_MD_INFO, NO_VALIDATION, BIT_LEVEL_WITH_RECOMMENDED, True),
        # Bit level recommended format marked as native with identification
        (CDR_MD_INFO, IDENTIFICATION, BIT_LEVEL_WITH_RECOMMENDED, False),
        # Bit level format with wrong mets use
        (CDR_MD_INFO, "yes-file-format-validation", BIT_LEVEL, False),
        # Unacceptable format marked as native
        (CDR_MD_INFO, NO_VALIDATION, UNACCEPTABLE, True),
        # UNAP and UNAV grades should always fail
        (CDR_MD_INFO, "", UNAP, False),
        (CDR_MD_INFO, NO_VALIDATION, UNAP, False),
        (CDR_MD_INFO, "", UNAV, False),
        (CDR_MD_INFO, NO_VALIDATION, UNAV, False),
        # Unexpected grade shoud always fail
        (CDR_MD_INFO, NO_VALIDATION, "test", False),
    )
)
def test_native_marked(md_info, use, grade, is_valid, monkeypatch):
    """
    Test validation with native file format.

    These native formats have are marked with
        'use': 'fi-dpres-no-file-format-validation'
    in metadata_info and have a corresponding file in an acceptable format.
    This test tests that native files with valid METS are valid and no further
    validation steps are done, whereas files not marked as native can be valid
    or invalid according to the normal rules.
    """
    def _iter_metadata_info(*args, **kwargs):
        md_info["use"] = use
        yield md_info

    monkeypatch.setattr(
        ipt.scripts.check_sip_digital_objects,
        'check_metadata_match',
        # Pass metadata check only for pdf files. This should not affect files
        # where validation is skipped.
        lambda *args: make_result_dict(md_info["filename"] == "pdf")
    )
    monkeypatch.setattr(
        ipt.scripts.check_sip_digital_objects,
        'check_well_formed',
        lambda *args, **kwargs: (make_result_dict(is_valid), {}, grade)
    )
    monkeypatch.setattr(
        ipt.scripts.check_sip_digital_objects,
        'iter_metadata_info',
        _iter_metadata_info
    )
    monkeypatch.setattr(
        xml_helpers.utils,
        'readfile',
        lambda *args: "mock"
    )

    results = [result for result in validation("/mock/mets", "/mock/catalog")]
    assert len(results) == 1
    assert results[0]["is_valid"] == is_valid


# TODO add test for native files needing to have a supported companion file?


@pytest.fixture(scope='function')
def patch_metadata_info(monkeypatch):
    """Patch iter_metadata_info to return output for erroneus pdf mets."""

    def _iter_metadata_info(mets_tree, mets_path, catalog_path=None):
        """Mock iter_metadata_info to return """
        # pylint: disable=unused-argument
        return [{
            'filename': 'pdf',
            'relpath': 'pdf',
            'use': '',
            'errors': 'Some error',
            'format': {'mimetype': 'application/pdf', 'version': '1.4'},
            'object_id': {'type': 'test_object', 'value': 'pdffile'},
            'algorithm': 'MD5',
            'digest': 'aa4bddaacf5ed1ca92b30826af257a1b'
        }]

    monkeypatch.setattr(
        ipt.scripts.check_sip_digital_objects, 'iter_metadata_info',
        _iter_metadata_info)


def patch_scraper_identify(mimetype='', version=''):
    """Monkeypatch Scraper to identify desired MIME type and version."""

    def _identify(obj):
        obj.info = {}
        for detector in iter_detectors():
            tool = detector(obj.filename)
            tool.detect()
            obj.info[len(obj.info)] = tool.info()
            obj.mimetype = mimetype
            obj.version = version

    return _identify


@pytest.mark.usefixtures('patch_metadata_info')
def test_metadata_info_erros(monkeypatch):
    """Test that when mets has errors, other validation steps are skipped."""
    monkeypatch.setattr(
        xml_helpers.utils,
        'readfile',
        lambda *args: "mock"
    )

    results = [result for result in validation("/mock/mets", "/mock/catalog")]
    assert len(results) == 1

    result = results[0]
    assert not result['is_valid']
    assert result['messages'] == ('Failed parsing METS, skipping '
                                  'validation.')
    assert result['errors'] == 'Some error'


def test_join_validation_results():
    """Test joining result dictionaries made with make_result_dict."""
    extension1 = ET.fromstring('<ext1 />')
    extension2 = ET.fromstring('<ext2></ext2>')
    res1 = make_result_dict(True, messages=['message1'],
                            extensions=[extension1])
    res2 = make_result_dict(False, messages=['message2'], errors=['error'],
                            extensions=[extension2])
    res3 = make_result_dict(True, valid_only_messages=['valid'])
    joined1 = join_validation_results({}, [res1, res2])
    joined2 = join_validation_results({}, [res1, res3])

    assert not joined1['is_valid']
    assert joined1['messages'] == 'message1\nmessage2'
    assert joined1['errors'] == 'error'
    assert joined1['extensions'] == [extension1, extension2]

    assert joined2['is_valid']
    assert joined2['messages'] == 'message1\nvalid'
    assert not joined2['errors']
    assert joined2['extensions'] == [extension1]
