"""
This is an PSPP validator.
"""

from ipt.validator.basevalidator import BaseValidator

PSPP_PATH = '/usr/bin/pspp-convert'
SPSS_PORTABLE_HEADER = "SPSS PORT FILE"


class PSPP(BaseValidator):
    """
    PSPP validator
    """
    _supported_mimetypes = {
        "application/x-spss-por": [""],
    }

    def validate(self):
        """No need for special implementation,
        file-scraper should have handled all.
        """
        pass
