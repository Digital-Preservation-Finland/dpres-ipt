"""
This is a DPX validator
"""

from ipt.validator.basevalidator import BaseValidator


class DPXv(BaseValidator):
    """
    DPX validator
    """
    _supported_mimetypes = {
        "image/x-dpx": ["1.0", "2.0"]
    }

    _check_version = None

    def validate(self):
        """No need for special implementation,
        file-scraper should have handled all.
        """
        pass


class DPXvError(Exception):
    """DPX validator error."""
    pass
