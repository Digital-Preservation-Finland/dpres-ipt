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
