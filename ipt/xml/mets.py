"""
Module for national METS XML extensions
"""

FI_NS = 'http://digitalpreservation.fi/schemas/mets/fi-extensions'
FI_NS_KDK = 'http://www.kdk.fi/standards/mets/kdk-extensions'


def parse_spec_version(mets_root):
    """Parse specification version.
    :mets_root: METS root
    :returns: National specification version
    """
    attr = mets_root.attrib
    specification = attr.get(f"{{{FI_NS}}}CATALOG") \
        or attr.get(f"{{{FI_NS}}}SPECIFICATION") \
        or attr.get(f"{{{FI_NS_KDK}}}CATALOG") \
        or attr.get(f"{{{FI_NS_KDK}}}SPECIFICATION")
    if specification is None:
        return None
    return specification.strip()
