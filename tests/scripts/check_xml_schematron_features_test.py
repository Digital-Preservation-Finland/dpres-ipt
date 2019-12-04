"""
Test that check-xml-schematron-features script behaves correctly
when the input is:
    - a valid METS file
    - an invalid METS file
    - not an xml file
"""
import os
import lxml.etree
import pytest

from ipt.scripts.check_xml_schematron_features import main
from tests.testcommon import shell
from tests.testcommon.settings import TESTDATADIR


def is_parsable_xml(string):
    """Helper to check if string can be parsed as xml."""
    try:
        lxml.etree.fromstring(string)
        return True
    except lxml.etree.XMLSyntaxError:
        return False


@pytest.mark.parametrize(
    ['filename', 'expected'],
    [
        ('valid_1.7.1_mets.xml',
         {'returncode': 0,
          'stderr_part': None}),
        ('valid_1.7.1_mets_noheader.xml',
         {'returncode': 0,
          'stderr_part': None}),
        ('invalid_1.7.1_mets.xml',
         {'returncode': 117,
          'stderr_part': None}),
        ('invalid__not_xml.txt',
         {'returncode': 117,
          'stderr_part': 'parser error : Start tag expected'})
    ])
def test_check_xml_schematron_features(filename, expected):
    """
    Run each test case and check that
        - stderr contains the correct error or is empty if no
          errors are expected
        - stdout can be parsed as xml (so it can be included in
          the validation report element 'eventOutcomeDetailExtension')
        - return code is what is expected
    """
    mets_path = os.path.join(TESTDATADIR, 'xml', filename)
    schema_path = '/usr/share/dpres-xml-schemas/schematron/mets_audiomd.sch'
    args = ['-s', schema_path, mets_path]
    (returncode, stdout, stderr) = shell.run_main(main, args)

    if expected['stderr_part']:
        assert expected['stderr_part'] in stderr
    else:
        assert not stderr
    if stdout:
        assert is_parsable_xml(stdout)
    assert expected['returncode'] == returncode
