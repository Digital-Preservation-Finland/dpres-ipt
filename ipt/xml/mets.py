"""
Module for national METS XML extensions
"""

from xml_helpers.utils import decode_utf8

FI_NS = 'http://digitalpreservation.fi/schemas/mets/fi-extensions'
FI_NS_KDK = 'http://www.kdk.fi/standards/mets/kdk-extensions'

def parse_spec_version(mets_root):
    """Parse specification version.
    :mets_root: METS root
    :returns: National specification version
    """
    attr = mets_root.attrib
    return attr["{%s}CATALOG" % FI_NS].strip() \
        or attr["{%s}SPECIFICATION" % FI_NS].strip() \
        or attr["{%s}CATALOG" % FI_NS_KDK].strip() \
        or attr["{%s}SPECIFICATION" % FI_NS_KDK].strip()
