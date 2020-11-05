"""Test the ipt.scripts.check_digital_objects module"""
# TODO add proper testing plan

import os
import uuid

import lxml.etree as ET
import pytest
import premis

from file_scraper.iterator import iter_detectors
from file_scraper.scraper import Scraper

from tests import testcommon
from tests.testcommon import shell

# Module to test
from ipt.scripts.check_sip_digital_objects import (main, validation,
                                                   validation_report,
                                                   make_result_dict,
                                                   join_validation_results)
import ipt.scripts.check_sip_digital_objects

METSDIR = os.path.abspath(
    os.path.join(testcommon.settings.TESTDATADIR, 'mets'))

TESTCASES = [
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
         'stdout': ['ERROR: File {}/sips/invalid_1.7.1_missing_object/'
                    'data/valid_1.2.png does not exist.'
                    .format(testcommon.settings.TESTDATADIR)]}},
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
         'stdout': ["Predefined version '3.1415' and resulted version '1.01' mismatch."]}},
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
               for case in TESTCASES)


@pytest.mark.parametrize(
    'case', TESTCASES, ids=[x['testcase'] for x in TESTCASES])
@pytest.mark.usefixtures('monkeypatch_Popen')
def test_check_sip_digital_objects(case, monkeypatch):
    """
    Test for check_sip_digital_objects
    """
    try:
        monkeypatch.setattr(Scraper, '_identify',
                            patch_scraper_identify(**case['patch']))
    except KeyError:
        # Nothing to patch.
        pass

    filename = os.path.join(
        testcommon.settings.TESTDATADIR, 'sips', case['filename'])

    arguments = [filename, 'preservation-sip-id', str(uuid.uuid4())]

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
def test_validation_report(results, object_count, event_count):
    """Test that validation report creates correct number of premis sections"""
    premis_xml = validation_report(results, 'sip-type', 'sip-value')
    assert premis.object_count(premis_xml) == object_count
    assert premis.event_count(premis_xml) == event_count
    assert premis.agent_count(premis_xml) == 1


@pytest.fixture(scope='function')
def patch_validate(monkeypatch):
    """
    Patch validation  to work without readable files.

    Metadata info dict list is always returned for package containing a pdf
    and three cdr fles (native, not validated).
    """

    def _check_well_formed(metadata_info):
        """Monkeypatch well-formedness check (there are no real files)."""
        result = {}

        if metadata_info['filename'] == 'pdf':
            result = make_result_dict(
                is_valid=True,
                messages=['JHovePdfScraper: Well-Formed and valid',
                          ('MagicScraper: The file was analyzed '
                           'successfully.')])
        elif metadata_info['filename'] == 'cdr':
            result = make_result_dict(
                is_valid=None,
                messages=['Proper scraper was not found. The file was not '
                          'analyzed.'])
        return (result, {})

    def _check_metadata_match(metadata_info, results):
        """Monkeypatch metadata matching: there are no real files to scrape."""
        # pylint: disable=unused-argument
        if metadata_info['filename'] == 'pdf':
            result = make_result_dict(
                is_valid=True,
                messages=['Some message.'])
        else:
            result = make_result_dict(
                is_valid=False,
                errors=['Some error.'])
        return result

    def _iter_metadata_info(mets_tree, mets_path, catalog_path=None):
        """Monkeypatch mets reading."""
        # pylint: disable=unused-argument
        md_info = [
            # PDF: supported and valid
            {'filename': 'pdf', 'use': '', 'errors': None,
             'format': {'mimetype': 'application/pdf',
                        'version': '1.4'},
             'object_id': {'type': 'test_object', 'value': 'pdf1'},
             'algorithm': 'MD5',
             'digest': 'aa4bddaacf5ed1ca92b30826af257a1b'},
            # CDR: not supported, not marked as native
            {'filename': 'cdr', 'use': '', 'errors': None,
             'format': {'mimetype': 'application/cdr',
                        'version': '9.0'},
             'object_id': {'type': 'test_object', 'value': 'cdr1'},
             'algorithm': 'MD5',
             'digest': 'aa4bddaacf5ed1ca92b30826af257a1c'},
            # CDR: not supproted, marked as native
            {'filename': 'cdr', 'use': 'no-file-format-validation',
             'errors': None,
             'format': {'mimetype': 'application/cdr',
                        'version': '9.0'},
             'object_id': {'type': 'test_object', 'value': 'cdr2'},
             'algorithm': 'MD5',
             'digest': 'aa4bddaacf5ed1ca92b30826af257a1d'},
            # CDR: not supported, use given but not the one that would
            #      mark it as native
            {'filename': 'cdr', 'use': 'yes-file-format-validation',
             'errors': None,
             'format': {'mimetype': 'application/cdr',
                        'version': '9.0'},
             'object_id': {'type': 'test_object', 'value': 'cdr3'},
             'algorithm': 'MD5',
             'digest': 'aa4bddaacf5ed1ca92b30826af257a1d'}]

        for md_element in md_info:
            yield md_element

    monkeypatch.setattr(
        ipt.scripts.check_sip_digital_objects, 'check_metadata_match',
        _check_metadata_match)
    monkeypatch.setattr(
        ipt.scripts.check_sip_digital_objects, 'check_well_formed',
        _check_well_formed)
    monkeypatch.setattr(
        ipt.scripts.check_sip_digital_objects, 'iter_metadata_info',
        _iter_metadata_info)


@pytest.mark.usefixtures('patch_validate')
def test_native_marked():
    """
    Test validation with native file format.

    These native formats have are marked with
        'use': 'no-file-format-validation'
    in metadata_info and have a corresponding file in an acceptable format.
    This test tests that native files with valid METS are valid and no further
    validation steps are done, whereas files not marked as native can be valid
    or invalid according to the normal rules.
    """

    collection = [result for result in validation(None)]
    assert (['no-file-format-validation' in result['metadata_info']['use'] for
             result in collection] == [False, False, True, False])
    assert ([result['is_valid'] for result in collection] ==
            [True, False, True, False])

# TODO add test for native files needing to have a supported companion file?


@pytest.fixture(scope='function')
def patch_metadata_info(monkeypatch):
    """Patch iter_metadata_info to return output for erroneus pdf mets."""

    def _iter_metadata_info(mets_tree, mets_path, catalog_path=None):
        """Mock iter_metadata_info to return """
        # pylint: disable=unused-argument
        return [{'filename': 'pdf', 'use': '', 'errors': 'Some error',
                 'format': {'mimetype': 'application/pdf', 'version': '1.4'},
                 'object_id': {'type': 'test_object', 'value': 'pdffile'},
                 'algorithm': 'MD5',
                 'digest': 'aa4bddaacf5ed1ca92b30826af257a1b'}]

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
            obj.info[len(obj.info)] = tool.info
            obj.mimetype = mimetype
            obj.version = version

    return _identify


@pytest.mark.usefixtures('patch_metadata_info')
def test_metadata_info_erros():
    """Test that when mets has errors, other validation steps are skipped."""

    results = [x for x in validation(None)]
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
