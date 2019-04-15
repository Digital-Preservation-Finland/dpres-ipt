"""
This is an Office validator.
"""

from ipt.validator.basevalidator import BaseValidator


class Office(BaseValidator):
    """
    Office validator
    """
    _supported_mimetypes = {
        'application/vnd.oasis.opendocument.text': ['1.0', '1.1', '1.2'],
        'application/vnd.oasis.opendocument.spreadsheet':
            ['1.0', '1.1', '1.2'],
        'application/vnd.oasis.opendocument.presentation':
            ['1.0', '1.1', '1.2'],
        'application/vnd.oasis.opendocument.graphics': ['1.0', '1.1', '1.2'],
        'application/vnd.oasis.opendocument.formula': ['1.0', '1.1', '1.2'],
        'application/msword': ['8.0', '8.5', '9.0', '10.0', '11.0'],
        'application/vnd.ms-excel': ['8.0', '9.0', '10.0', '11.0'],
        'application/vnd.ms-powerpoint': ['8.0', '9.0', '10.0', '11.0'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.'
        'document': ['12.0', '14.0', '15.0'],
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
            ['12.0', '14.0', '15.0'],
        'application/vnd.openxmlformats-officedocument.presentationml.'
        'presentation': ['12.0', '14.0', '15.0']
    }

    def validate(self):
        """No need for special implementation,
        file-scraper should have handled all.
        """
        pass
