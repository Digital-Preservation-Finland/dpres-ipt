"""
This is an ImageMagick validator.
"""

from ipt.validator.basevalidator import BaseValidator

FORMAT_STRINGS = {
    'image/png': 'PNG',
    'image/jpeg': 'JPEG',
    'image/jp2': 'JP2',
    'image/tiff': 'TIFF',
}


class ImageMagick(BaseValidator):
    """
    ImageMagick validator
    """
    _supported_mimetypes = {
        "image/png": ["1.2"],
        "image/jpeg": ["1.00", "1.01", "1.02"],
        "image/jp2": [""],
        "image/tiff": ["6.0"],
    }

    def validate(self):
        """Check for the appropriate mimetype"""
        if self.scraper.mimetype != FORMAT_STRINGS[self.mimetype]:
            self.errors("File format does not match with MIME type.")
