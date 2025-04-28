Release notes
=============

Version 0.106
-------------

Change checksum comparison to be character size independent

Version 0.105
-------------

Update deprecated timezone calls.

Version 0.104
-------------

Installation instructions for AlmaLinux 9 using RPM packages

Version 0.103
-------------

Code cleanups and syntax fixes.

Version 0.102
-------------

Accept unsupported formats for bit-level preservation when submitted with supported formats.

Version 0.101
-------------

Add RHEL9 RPM spec file

Fix Python package build

Version 0.100
-------------

Python 2.7 support officially removed.

Adapt to API change of PREMIS library.

Version 0.99
------------

Update requirements.

Version 0.98
------------

Update installation guide for Python 3.6 in README.rst and requirements in
setup files.

Version 0.97
------------

Fixed character encoding issue in bagit manifest.

Version 0.96
------------

Added file-scraper's grading support in METS validation.
Terminology prefix change to fi-dpres.

Version 0.95
------------

Encountering an error when checking waw files generated a very compact error
message that was hard to read. The error message is now more human readable.

Version 0.94
------------

Remove hard coded MS Office file format versions from known unav versions list.

Version 0.93
------------

Build rhel7 python3 rpm for dpres-ipt.

Version 0.92
------------

Support for updated term for marking files to bit-level preservation.

Version 0.91
------------

NEW:
Support for local schema files and catalogs in XML validation. New option --catalog_path
is added to check-sip-digital-objects script to support this.

Support to create local schema catalogs with create-schema-catalog script.
The created local schema catalog can be used for check-sip-digital-objects script.


Version 0.84
------------

Makes use of ISO Schematron XSLT1 instead of dpres-xml-schemas
for XSLT related conversion tool.
Uses file-scraper for all file validation and metadata scraping.
Can be run under Python 3.6.


Version 0.77
------------

Adds support for WAV and BWF audio files.


Version 0.76
------------

Supports PREMIS containers and bitstreams in SIP technical metadata.
Adds support for PDF/A-2 documents and HTML5 documents.
The following file formats are handled differently with new tools:
DPX files, UTF-8 text files, XHTML documents, PDFs, PDF/A-1 files, CSV files
Character encoding validation has been updated.
Separate text validation for files reported as text/plain in the SIP metadata.
Updates to MPEG audio and video validation.


Version 0.53
------------

XML/Schematron catalogs and signature code moved to dpres-xml-schemas and
dpres-signature repositories, respectively.


Version 0.41
------------

The XML catalogs are all now under /etc/xml/information-package-tools
The RPM post script should configure the centralized /etc/xml/catalog
correctly. In case that does not happen, the catalog file should have the
following lines in it:

<nextCatalog catalog="/etc/xml/information-package-tools/digital-object-catalog/digital-object-catalog.xml"/>
<nextCatalog catalog="/etc/xml/information-package-tools/kdk-mets-catalog/catalog-local.xml"/>
<nextCatalog catalog="/etc/xml/information-package-tools/private-catalog/private-catalog.xml"/>


Version 0.39
------------

FIX: Unsupported mimetype error fixed

NEW: Add support for warc 0.18

NEW: Refactored validator code and mets parsing.


Version 0.35
------------

NEW:
Implemented arc/warc validation with Warctools. Jhove2 is no more used for this.

Configuration changes: validators.json has to be updated.

warctools rpm has to be updated, since this release is using version 4.8.3.
Warctools update also fixes the incorrect trailing newline bug with some
warcs.

NEW:
HTML valdiation implemented with jhove.

FIX:
xmllint huge-parameter added to make large file validation work.
