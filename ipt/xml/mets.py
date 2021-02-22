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
    specification = attr.get("{%s}CATALOG" % FI_NS) \
        or attr.get("{%s}SPECIFICATION" % FI_NS) \
        or attr.get("{%s}CATALOG" % FI_NS_KDK) \
        or attr.get("{%s}SPECIFICATION" % FI_NS_KDK)
    if specification is None:
        return None
    return specification.strip()
