""" Class for XML file validation with Xmllint. """

import os
import subprocess
import tempfile
from lxml import etree

from ipt.validator.basevalidator import BaseValidator

XSI = 'http://www.w3.org/2001/XMLSchema-instance'
XS = '{http://www.w3.org/2001/XMLSchema}'

SCHEMA_TEMPLATE = """<?xml version = "1.0" encoding = "UTF-8"?>
    <xs:schema xmlns="http://dummy"
    targetNamespace="http://dummy"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    version="1.0"
    elementFormDefault="qualified"
    attributeFormDefault="unqualified">
    </xs:schema>"""


class Xmllint(BaseValidator):
    """This class implements a plugin interface for validator module and
    validates XML files using Xmllint tool.

    .. seealso:: http://xmlsoft.org/xmllint.html
    """

    _supported_mimetypes = {
        'text/xml': ['1.0']
    }

    def validate(self):
        """No need for special implementation,
        file-scraper should have handled all.
        """
        pass
