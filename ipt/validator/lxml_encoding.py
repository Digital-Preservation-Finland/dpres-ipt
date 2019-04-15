"""class for XML and HTML5 header encoding check with lxml. """

from ipt.validator.basevalidator import BaseValidator


class XmlEncoding(BaseValidator):
    """
    Character encoding validator for HTML5 and XML files
    """

    # We use JHOVE for HTML4 and XHTML files.
    _supported_mimetypes = {
        'text/xml': ['1.0'],
        'text/html': ['5.0']
    }

    def validate(self):
        """Additional logic to check the XML's charset with the metadata is
        required.
        """
        charset = self.scraper.streams[0]['charset']
        if charset == self.metadata_info['format']['charset']:
            self.messages('Encoding metadata match found.')
        else:
            self.errors(' '.join(
                ['Encoding metadata mismatch:',
                 charset, 'was found, but',
                 self.metadata_info['format']['charset'], 'was expected.']))
