"""Module for validating files with pngcheck validator"""

from ipt.validator.basevalidator import BaseValidator


class Pngcheck(BaseValidator):
    """ Initializes pngcheck validator and set ups everything so that
        methods from base class (BaseValidator) can be called, such as
        validate() for file validation.


    .. seealso:: http://www.libpng.org/pub/png/apps/pngcheck.html
    """

    _supported_mimetypes = {
        'image/png': ['1.2']
    }

    def validate(self):
        """No need for special implementation,
        file-scraper should have handled all.
        """
        pass
