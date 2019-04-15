import unicodedata
import string

from ipt.validator.basevalidator import BaseValidator


def sanitaze_string(dirty_string):
    """Strip non-printable control characters from unicode string"""
    sanitazed_string = "".join(
        char for char in dirty_string if unicodedata.category(char)[0] != "C"
        or char in string.printable)
    return sanitazed_string


class WarctoolsWARC(BaseValidator):
    """Implements WARC file format validator using Internet Archives warctools
    validator.

    .. seealso:: https://github.com/internetarchive/warctools
    """

    _supported_mimetypes = {
        'application/warc': ['0.17', '0.18', '1.0']
    }

    def validate(self):
        """No need for special implementation,
        file-scraper should have handled all.
        """
        pass


class WarctoolsARC(BaseValidator):
    _supported_mimetypes = {
        'application/x-internet-archive': ['1.0', '1.1']
    }

    def validate(self):
        """No need for special implementation,
        file-scraper should have handled all.
        """
        pass
