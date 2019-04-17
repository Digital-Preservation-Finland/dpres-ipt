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
        if self.mimetype != self.scraper.mimetype:
            self.errors("Mimetype [%s] does not match with expected [%s]" % (
                self.scraper.mimetype, self.mimetype))
