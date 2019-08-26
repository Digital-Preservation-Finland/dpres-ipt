"""
Test that check-xml-schema-features script behaves correctly
when the input is:
    - a valid METS file
    - an invalid METS file
    - not an xml file
"""
import os
import pytest

from ipt.scripts.check_xml_schema_features import main
from tests.testcommon import shell
from tests.testcommon.settings import TESTDATADIR


@pytest.mark.parametrize(
    ['filename', 'expected'],
    [
        ('valid_1.7.1_mets.xml',
         {'returncode': 0,
          'stdout_part': 'Success',
          'stderr_part': None}),
        ('invalid_1.7.1_mets.xml',
         {'returncode': 117,
          'stdout_part': None,
          'stderr_part': 'invalid_1.7.1_mets.xml fails to validate'}),
        ('invalid__not_xml.txt',
         {'returncode': 117,
          'stdout_part': None,
          'stderr_part': 'invalid__not_xml.txt does not appear to be XML'})
    ])
def test_check_xml_schema_features(filename, expected):
    """
    Run each test case and check that returncode, stdout and
    stderr match the expected.
    """
    args = [os.path.join(TESTDATADIR, 'xml', filename)]
    (returncode, stdout, stderr) = shell.run_main(main, args)

    if expected['stderr_part']:
        assert expected['stderr_part'] in stderr
    else:
        assert not stderr
    if expected['stdout_part']:
        assert expected['stdout_part'] in stdout
    assert expected['returncode'] == returncode
