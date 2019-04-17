"""
This is an PDF/A validator.
"""

from ipt.validator.basevalidator import BaseValidator


class VeraPDF(BaseValidator):
    """
    PDF/A validator
    """
    _supported_mimetypes = {
        "application/pdf": ['A-1a', 'A-1b', 'A-2a', 'A-2b', 'A-2u', 'A-3a',
                            'A-3b', 'A-3u']
    }

    def validate(self):
        """Validate the mimetype."""
        self.validate_mimetype()
