"""Configure py.test default values and functionality"""

import sys
import pytest
from file_scraper.iterator import iter_detectors
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


@pytest.fixture(scope='function')
def monkeypatch_scraper_mime_csv(monkeypatch):
    """To monkeypatch Scraper-class's default behaviour.

    At the time of this writing, there's a bug that makes Scraper unable
    to detect text/csv files.
    """

    def patch_scraper_identify(mimetype='', version=''):
        def _identify(obj):
            obj.info = {}
            for detector in iter_detectors():
                tool = detector(obj.filename)
                tool.detect()
                obj.info[len(obj.info)] = tool.info
                obj.mimetype = mimetype
                obj.version = version

        return _identify

    monkeypatch.setattr(Scraper, '_identify',
                        patch_scraper_identify(mimetype='text/csv'))
    monkeypatch.setattr('file_scraper.scraper.LOSE',
                        [None, '(:unav)', '(:unap)', 'text/plain'])
    monkeypatch.setattr('file_scraper.magic_base.MIMETYPE_DICT', {
        'application/xml': 'text/xml',
        'application/mp4': None,
        'application/vnd.ms-asf': 'video/x-ms-asf',
        'video/x-msvideo': 'video/avi',
        'application/x-ia-arc': 'application/x-internet-archive',
        'text/plain': 'text/csv'
    })
