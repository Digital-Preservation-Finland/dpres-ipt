"""Module for validating files with Jhove validator"""
import os
import lxml.etree

from ipt.validator.basevalidator import BaseValidator, Shell
from ipt.utils import parse_mimetype, handle_div, find_max_complete, \
    compare_lists_of_dicts

NAMESPACES = {'j': 'http://hul.harvard.edu/ois/xml/ns/jhove',
              'aes': 'http://www.aes.org/audioObject'}
JHOVE_HOME = '/usr/share/java/jhove'
EXTRA_JARS = os.path.join(JHOVE_HOME, 'bin/JhoveView.jar')
CP = os.path.join(JHOVE_HOME, 'bin/jhove-apps-1.18.1.jar') + ':' + EXTRA_JARS


class JHoveBase(BaseValidator):
    """Base class for Jhove file format validator"""

    _supported_mimetypes = ['']

    def validate(self):
        """Check for various values set in metadata."""
        stream_data = self.scraper.streams[0]
        stream_data['mimetype'] = self.scraper.mimetype
        for key in self.metadata_info['format']:
            if key in ('alt-format', 'version'):
                # Alt-format and version are the data JHove can't discover
                continue
            try:
                if self.metadata_info['format'][key] == stream_data[key]:
                    self.messages('Validation %s check OK' % key)
                else:
                    self.errors(
                        'Metadata mismatch: found %s "%s", expected "%s"' %
                        (key,
                         stream_data[key],
                         self.metadata_info['format'][key]))
            except KeyError:
                self.errors(
                    'The [%s] information could not be found from the ' % key)


class JHoveGif(JHoveBase):
    """JHove GIF file format validator"""

    _supported_mimetypes = {
        'image/gif': ['1987a', '1989a']
    }


class JHoveHTML(JHoveBase):
    """Jhove HTML file format validator"""

    _supported_mimetypes = {
        'text/html': ['4.01'],
        'application/xhtml+xml': ['1.0', '1.1']
    }


class JHoveJPEG(JHoveBase):
    """JHove validator for JPEG"""

    _supported_mimetypes = {
        'image/jpeg': [''],
    }

    @classmethod
    def is_supported(cls, metadata_info):
        return metadata_info['format']['mimetype'] in cls._supported_mimetypes


class JHoveTiff(JHoveBase):
    """JHove validator for tiff"""

    _supported_mimetypes = {
        'image/tiff': ['6.0']
    }


class JHovePDF(JHoveBase):
    """JHove validator for PDF"""

    _supported_mimetypes = {
        'application/pdf': ['1.2', '1.3', '1.4', '1.5', '1.6']
    }


class JHoveTextUTF8(JHoveBase):
    """JHove validator for text/plain UTF-8."""

    _supported_mimetypes = {
        'text/csv': [''],
        'text/plain': [''],
        'text/xml': ['1.0'],
        'text/html': ['4.01', '5.0'],
        'application/xhtml+xml': ['1.0', '1.1']
    }

    @classmethod
    def is_supported(cls, metadata_info):
        """
        Check suported mimetypes.
        :metadata_info: metadata_info
        """
        if metadata_info['format']['mimetype'] in cls._supported_mimetypes:

            if 'charset' not in metadata_info['format']:
                return False
            elif metadata_info['format']['charset'] != 'UTF-8':
                return False
        return super(JHoveTextUTF8, cls).is_supported(metadata_info)


class JHoveWAV(JHoveBase):
    """JHove validator for WAV and BWF audio data."""

    _supported_mimetypes = {
        'audio/x-wav': ['', '2']
    }

    def validate(self):
        """Using scraper's stream as a base, adds the elements to the
        stream_data dict. Then removes keys from dicts
        missing in either dict before comparing the dicts.

        If the dicts match the metadata is valid."""

        (metadata, stream_data) = find_max_complete(
            [self.metadata_info], [self.scraper.streams[0]],
            ['format', 'mimetype', 'version']
        )

        match = compare_lists_of_dicts(metadata, stream_data)

        if match is False:
            self.errors("Audio metadata in %s are not what is "
                        "described in metadata. Found %s, expected %s" % (
                            self.metadata_info["filename"],
                            stream_data, self.metadata_info))
        if match is True:
            self.messages('Validation audio metadata check OK')
