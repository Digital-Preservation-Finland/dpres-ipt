"""
This is a PDF 1.7 valdiator implemented with ghostscript.
"""

from ipt.validator.basevalidator import BaseValidator, Shell


class GhostScript(BaseValidator):
    """
    Ghostscript pdf validator
    """
    _supported_mimetypes = {
        'application/pdf': ['1.7', 'A-1a', 'A-1b', 'A-2a', 'A-2b', 'A-2u',
                            'A-3a', 'A-3b', 'A-3u']
    }

    def validate(self):
        """Check the version is correct."""
        if self.version in ['A-1a', 'A-1b', 'A-2a', 'A-2b', 'A-2u', 'A-3a',
                            'A-3b', 'A-3u']:
            return

        if self.version != self.scraper.version:
            self.errors("wrong file version. Expected PDF %s, found%s"
                        % (self.version, self.scraper.version))
