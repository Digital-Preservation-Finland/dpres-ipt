"""Common configuration and fixtures for all tests"""
# pylint does not understand pytest fixtures
# pylint: disable=redefined-outer-name

import logging
import tempfile
import subprocess
import shutil
import os

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


@pytest.fixture(scope='function')
def diacritic_bagit_path(temp_sip):
    """Setup a test bagit dir that contains sip with special character in mets
    and filename.
    """
    bagit_root_path = temp_sip('valid_1.7.1_filename_diacritics')
    return bagit_root_path


@pytest.fixture
def bagit_fx(tmpdir):
    """Create test bagit."""
    bagit_path = tmpdir / "bagit_fx"
    sip_path = bagit_path / "data" / "transfers" / "sippi"
    sip_path.ensure(dir=True)

    mets_path = sip_path / "mets.xml"
    mets_path.write('asfasdfasdfsda')

    image_path = sip_path / "images" / "image.jpg"
    text_path = sip_path / "file_1.txt"

    image_path.ensure().write('abcd')
    text_path.ensure().write('abcdef')

    manifest = bagit_path / "manifest-md5.txt"
    manifest.write("\n".join([
        'e2fc714c4727ee9395f324cd2e7f331f data/file.txt',
        'e80b5017098950fc58aad83c8c14978e file2.txt'
    ]))

    bagit_meta = bagit_path / 'bagit.txt'
    bagit_meta.write('foo')

    return bagit_path
