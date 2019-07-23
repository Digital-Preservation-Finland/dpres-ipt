"""Test the ipt.scripts.check_digital_objects module"""
# TODO add proper testing plan

import os
import uuid

import pytest
import premis

from file_scraper.iterator import iter_detectors
from file_scraper.scraper import Scraper

from tests import testcommon
from tests.testcommon import shell

# Module to test
from ipt.scripts.check_sip_digital_objects import (main, validation,
                                                   validation_report,
                                                   make_result_dict)
import ipt.scripts.check_sip_digital_objects

METSDIR = os.path.abspath(
    os.path.join(testcommon.settings.TESTDATADIR, 'mets'))

TESTCASES = [
# TODO enable / replace tests when integration is done
    {'testcase': 'Test valid sip package #2',
     'filename': 'CSC_test002',
     'expected_result': {
         'returncode': 0,
         'stdout': '',
         'stderr': ''}},
    {'testcase': 'Test sip with whitespace sip package #3',
     'filename': 'CSC whitespace',
     'expected_result': {
         'returncode': 0,
         'stdout': '',
         'stderr': ''}},

    # The version given in METS for the pdf does not match what scraper
    # thinks it is
    # {'testcase': 'Test valid sip package #6: csc-test-valid-kdkmets-1.3',
    #  'filename': 'CSC_test006',
    #  'expected_result': {
    #      'returncode': 0,
    #      'stdout': '',
    #      'stderr': ''}},

    {'testcase': 'Test valid sip package #7: csc-test-metadata-text-plain',
     'filename': 'csc-test-metadata-text-plain',
     'expected_result': {
         'returncode': 0,
         'stdout': ['Found alternative format "text/html", but validating '
                    'as "text/plain".'],
         'stderr': ''}},

    # Scraper seems to support the file
    # {'testcase': 'Unsupported file version',
    #  'filename': 'CSC_test_unsupported_version',
    #  'patch': {'version': '2.0'},
    #  'expected_result': {
    #      'returncode': 117,
    #      'stdout': ['No validator for mimetype: '
    #                 'application/warc version: 2.0'],
    #      'stderr': ''}},
    {'testcase': 'Unsupported file mimetype, without version',
     'filename': 'CSC_test_unsupported_mimetype_no_version',
     'patch': {'mimetype': 'application/kissa',
               'version': ''},
     'expected_result': {
         'returncode': 117,
         'stdout': ['Proper scraper was not found. The file was not '
                    'analyzed.'],
         'stderr': ''}},
    {'testcase': 'Unsupported file mimetype',
     'filename': 'CSC_test_unsupported_mimetype',
     'patch': {'mimetype': 'application/kissa',
               'version': '1.0'},
     'expected_result': {
         'returncode': 117,
         'stdout': ['Proper scraper was not found. The file was not '
                    'analyzed.'],
         'stderr': ''}},
    {'testcase': 'Invalid mets, missing ADMID.',
     'filename': 'CSC_test_missing_admid',
     'patch': {'mimetype': None,
               'version': None},
     'expected_result': {
         'returncode': 117,
         'stdout': ['Proper scraper was not found. The file was not '
                    'analyzed.'],
         'stderr': ''}},
    {'testcase': 'Invalid mets, missing amdSec',
     'filename': 'CSC_test_missing_amdSec',
     'patch': {'mimetype': None,
               'version': None},
     'expected_result': {
         'returncode': 117,
         'stdout': ['Proper scraper was not found. The file was not '
                    'analyzed.'],
         'stderr': ''}},
    {'testcase': 'Invalid warc',
     'filename': 'csc-test-invalid-warc',
     'expected_result': {
         'returncode': 117,
         'stdout': ['Proper scraper was not found. The file was not '
                    'analyzed.'],
         'stderr': ''}},
    {'testcase': 'Invalid arc',
     'filename': 'csc-test-invalid-arc-invalid-start-byte',
     'expected_result': {
         'returncode': 117,
         'stdout': ['Failed: returncode 1',
                    'Exception: missing headers'],
         'stderr': ''}},
    {'testcase': 'Invalid arc',
     'filename': 'csc-test-invalid-arc-xml-incompatible-string',
     'expected_result': {
         'returncode': 117,
         'stdout': ['Failed: returncode 1',
                    'WARNING: Unable to parse HTTP-header: ',
                    'Exception: expected 14 bytes but only read 0'],
         'stderr': ''}},
    {'testcase': 'Invalid warc renamed to .gz',
     'filename': 'csc-test-invalid-warc-not-gz',
     'expected_result': {
         'returncode': 117,
         'stdout': ['Proper scraper was not found. The file was not '
                    'analyzed.'],
         'stderr': ''}}]

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
        testcommon.settings.TESTDATADIR, 'test-sips', case['filename'])

    arguments = [filename, 'preservation-sip-id', str(uuid.uuid4())]

    (returncode, stdout, stderr) = shell.run_main(
        main, arguments)

    assert stderr == ''

    for match_string in case['expected_result']['stdout']:
        assert match_string in stdout

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

    def _check_well_formed(scraper):
        """Monkeypatch well-formedness check (there are no real files)."""
        result = {}

        if scraper.filename == 'pdf':
            result = make_result_dict(
                    is_valid=True,
                    messages=['JHovePdfScraper: Well-Formed and valid',
                              ('MagicScraper: The file was analyzed '
                               'successfully.')],
                    errors=[])
        elif scraper.filename == 'cdr':
            result = make_result_dict(
                    is_valid=None,
                    messages=['Proper scraper was not found. The file was not '
                              'analyzed.'],
                    errors=[],
                    prefix='ScraperNotFound' + ': ')
        return result

    def _check_metadata_match(metadata_info, results):
        """Monkeypatch metadata matching: there are no real files to scrape."""
        # pylint: disable=unused-argument
        if metadata_info['filename'] == 'pdf':
            result = {'is_valid': True,
                      'messages': 'Mimetype and version ok.',
                      'errors': ''}
        else:
            result = {'is_valid': False,
                      'messages': '',
                      'errors': ("MetadataComparator: ERROR: Mimetype and "
                                 "version mismatch. Expected "
                                 "['application/cdr', '9.0'], found "
                                 "['None', '''None']")}
        return result

    def _iter_metadata_info(mets_tree, mets_path):
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

    def _iter_metadata_info(mets_tree, mets_path):
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
    assert result['messages'] == ('Failed parsing metadata, skipping '
                                  'validation.')
    assert result['errors'] == 'Some error'
