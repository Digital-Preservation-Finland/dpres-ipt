"""validator iterator for digital object validation"""

# pylint: disable=unused-import
import os

from file_scraper.scraper import Scraper
from file_scraper.scrapers.textfile import CheckTextFile
from six import itervalues

from ipt.utils import create_scraper_params
from ipt.validator.basevalidator import BaseValidator
from ipt.validator.jhove import JHoveBase, JHovePDF, \
    JHoveTiff, JHoveJPEG, JHoveHTML, JHoveGif, JHoveTextUTF8, JHoveWAV
from ipt.validator.xmllint import Xmllint
from ipt.validator.lxml_encoding import XmlEncoding
from ipt.validator.warctools import WarctoolsWARC, WarctoolsARC
from ipt.validator.ghostscript import GhostScript
from ipt.validator.pngcheck import Pngcheck
from ipt.validator.csv_validator import PythonCsv
from ipt.validator.ffmpeg import FFMpeg
from ipt.validator.office import Office
from ipt.validator.file import File, FileEncoding
from ipt.validator.imagemagick import ImageMagick
from ipt.validator.pspp import PSPP
from ipt.validator.verapdf import VeraPDF
from ipt.validator.dpxv import DPXv
from ipt.validator.vnu import Vnu

_FILE_SCRAPER_DETECTOR_CLASSES = ('FidoDetector', 'MagicDetector')
_MIME_TEXT_PLAIN = 'text/plain'


def iter_validators(metadata_info, scraper_obj=None):
    """
    Find a validator for digital object from given `metadata_info` record.
    :returns: validator class

    Implementation of class factory pattern from
    http://stackoverflow.com/questions/456672/class-factory-in-python
    """

    # pylint: disable=no-member

    found_validator = False

    if metadata_info.get("erroneous-mimetype", False):
        yield UnknownFileFormat(metadata_info)
        return

    if not os.path.exists(metadata_info['filename']):
        yield NonExistingFile(metadata_info)
        return

    for cls in (BaseValidator.__subclasses__() + JHoveBase.__subclasses__()):
        if cls.is_supported(metadata_info):
            found_validator = True
            yield cls(metadata_info, scraper_obj)

    if not found_validator:
        yield UnknownFileFormat(metadata_info)


class UnknownFileFormat(object):
    """
    Validator class for unknown filetypes. This will always result as
    invalid validation result.
    """

    def __init__(self, metadata_info):
        """
        Initialize object
        """
        self.metadata_info = metadata_info

    def validate(self):
        """
        No implementation
        """
        pass

    def result(self):
        """
        Return validation result
        """
        error_message = 'No validator for mimetype: %s version: %s' % (
            self.metadata_info['format']['mimetype'],
            self.metadata_info['format']['version'])

        return {
            'is_valid': False,
            'messages': "",
            'errors': error_message}


class NonExistingFile(object):
    """Validator class for files that do not exist. This will always result as
    invalid validation result.
    """

    def __init__(self, metadata_info):
        """Initialize object
        """
        self.metadata_info = metadata_info

    def validate(self):
        """No implementation
        """
        pass

    def result(self):
        """Return validation result
        """
        error_message = 'File %s does not exist' \
                        % self.metadata_info['filename']

        return {
            'is_valid': False,
            'messages': "",
            'errors': error_message}


def metadata_validation_results(metadata_info):
    """Validates the given metadata information with the given scraped object.

    :param metadata_info: Metadata entry that was parsed from mets.xml.
    :return: A generator to produce the validation results.
    """

    scraper_obj = Scraper(metadata_info['filename'],
                          **create_scraper_params(metadata_info))
    try:
        if metadata_info['format']['mimetype'] == _MIME_TEXT_PLAIN:
            # TODO: Make scraper conduct text/plain specific scraping
            pass
    except KeyError:
        # Can happen that "format" is missing due to file being invalid.
        pass
    scraper_obj.scrape()
    for info in itervalues(scraper_obj.info):
        if info['class'] in _FILE_SCRAPER_DETECTOR_CLASSES:
            continue
        yield {
            'is_valid': scraper_obj.well_formed,
            'messages': info['messages'],
            'errors': info['errors'],
        }
    for validator in iter_validators(metadata_info, scraper_obj):
        yield validator.result()
