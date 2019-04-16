"""Configure py.test default values and functionality"""

import sys
import pytest
from file_scraper.scraper import Scraper

from ipt.utils import create_scraper_params
from tests.fixtures import *

# Prefer modules from source directory rather than from site-python
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                '..'))


def pytest_addoption(parser):
    parser.addoption(
        "--monkeypatch-popen", action="store_true",
        help="Use monkeypatch subprocess.Popen() which reads outputs from file"
             "instead executing the actual command.", default=False)


@pytest.fixture(scope='function')
def create_scraper_obj():
    """Fixture to provide a scraper object that has scraped based on given
    metadata.
    """

    def _f(metadata_info):
        scraper_obj = Scraper(metadata_info['filename'],
                              **create_scraper_params(metadata_info))
        scraper_obj.scrape()
        return scraper_obj

    return _f
