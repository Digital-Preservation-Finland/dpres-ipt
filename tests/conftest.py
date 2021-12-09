# coding=utf-8
"""Common configuration and fixtures for all tests"""
# pylint does not understand pytest fixtures
# pylint: disable=redefined-outer-name

from ipt.six_utils import ensure_binary

import logging
import tempfile
import subprocess
import shutil
import os
import io

import six
import pytest


from tests.testcommon.utils import Directory

# Setup logging facility
LOGGER = logging.getLogger('tests.fixtures')
logging.basicConfig(level=logging.DEBUG)


def pytest_addoption(parser):
    """Configure pytest options"""
    parser.addoption(
        "--monkeypatch-popen", action="store_true",
        help="Use monkeypatch subprocess.Popen() which reads outputs from file"
             "instead executing the actual command.", default=False)


@pytest.fixture(scope="function")
def testpath(request):
    """Creates temporary directory and clean up after testing.

    :request: Pytest request fixture
    :returns: Path to temporary directory

    """
    temp_path = tempfile.mkdtemp(prefix="tests.testpath.")

    LOGGER.debug(
        'testpath:%s:create temp_path:%s', request,
        temp_path)

    def fin():
        """remove temporary path"""
        LOGGER.debug(
            'testpath:%s:delete temp_path:%s', request,
            temp_path)
        subprocess.call(['find', temp_path, '-ls'])
        shutil.rmtree(temp_path)

    request.addfinalizer(fin)

    return Directory(temp_path)


@pytest.fixture(scope="function")
def temp_sip(testpath):
    """Copy SIP from testdata to temporary path for testing """

    def _temp_sip(sip_name):
        """Copy function used inside tests used inside tests"""
        sip_path = os.path.join('tests/data/sips', sip_name)
        temp_sip_path = os.path.join(testpath, sip_name)
        shutil.copytree(sip_path, temp_sip_path)
        return temp_sip_path

    return _temp_sip


@pytest.fixture(params=[b'utf8_\xc3\xa4', b'latin1_\xe4'])
def chars_fx(request):
    """Return characters in various encodings as bytes"""
    return request.param


@pytest.fixture
def bagit_no_manifest_fx(tmpdir, chars_fx):
    """Generate Bagit directory structure without manifest file

    :returns: Path to bagit directory

    """

    bagit_path = tmpdir / chars_fx

    sip_path = bagit_path / 'data' / 'transfers' / "sip_" + chars_fx
    sip_path.ensure(dir=True)

    mets_path = sip_path / 'mets.xml'
    mets_path.write('<mets:mets></mets:mets>')

    payload = sip_path / 'files' / "file_" + chars_fx
    payload.write('abcdef', ensure=True)

    bagit_meta = bagit_path / 'bagit.txt'
    bagit_meta.write('foo')

    return bagit_path


@pytest.fixture
def manifest_fx(chars_fx):
    """Return manifest file contents as bytes"""
    return b"\n".join([
        b"84a37a4d5bd4b36db0da5379aa6fbde3 "
        b"data/transfers/sip_X/mets.xml",

        b"e80b5017098950fc58aad83c8c14978e "
        b"data/transfers/sip_X/files/file_X\n"
    ]).replace(b'X', chars_fx)


@pytest.fixture
def bagit_with_manifest_fx(bagit_no_manifest_fx, manifest_fx):
    """Generate Bagit directory with manifest file included

    :returns: Path to bagit directory

    """

    manifest = bagit_no_manifest_fx / 'manifest-md5.txt'
    manifest.ensure()

    # LocalPath support binary writes only after Python3.5
    with io.open(six.binary_type(manifest), 'wb') as outfile:
        outfile.write(manifest_fx)

    return bagit_no_manifest_fx
