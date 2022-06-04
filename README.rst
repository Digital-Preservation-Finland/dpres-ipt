Information Package Tools
=========================

This repository contains tools for validating Submission/Archival/Dissemination Information
Packages (SIP/AIP/DIP) based on Open Archival Information System (OAIS) standard.

The aim is to provide digital preservation services for culture and research to ensure
the access and use of materials long in the future. Documentation and specifications
for the digital preservation service can be found in: http://digitalpreservation.fi

Installation
------------

Installation and usage requires Python 2.7, or 3.6 or newer.
The software is tested with Python 3.6 on Centos 7.x release. Python 2.7 support will be removed in the future.

The following software is required for validation tools.

        * dpres-xml-schemas, see https://github.com/Digital-Preservation-Finland/dpres-xml-schemas
        * xml-helpers, see https://github.com/Digital-Preservation-Finland/xml-helpers
        * mets, see https://github.com/Digital-Preservation-Finland/mets
        * premis, see https://github.com/Digital-Preservation-Finland/premis
        * file-scraper, see https://github.com/Digital-Preservation-Finland/file-scraper
                * see file-scraper installation instructions for installing validators for individual file formats
        * libxml2 & libxslt / xmllint & xsltproc ( with exslt and Saxon line number extensions )
        * gcc
        * lxml
        * python-mimeparse
        * xml-common
        * Gzip

You can install the software listed in requirements_github.txt by following these instructions. Other software listed above needs to be installed separately.

For Python 3.6 or newer, create a virtual environment::
    
    python3 -m venv venv

For Python 2.7, get python-virtualenv software and create a virtual environment::

    sudo yum install python-virtualenv
    virtualenv venv

Run the following to activate the virtual environment::

    source venv/bin/activate

Install the required software with commands::

    pip install --upgrade pip==20.2.4 setuptools  # Only for Python 3.6 or newer
    pip install --upgrade pip setuptools          # Only for Python 2.7
    pip install -r requirements_github.txt
    pip install .

To deactivate the virtual environment, run ``deactivate``.
To reactivate it, run the ``source`` command above.

NOTE: Running unit tests requires the full installation of file-scraper with all its requirements.

Usage
-----

To validate a METS document::

        python ipt/scripts/check_xml_schema_features.py <METS document>
        python ipt/scripts/check_xml_schematron_features.py -s <schematron_file> <METS document>

See the schematron files from: https://github.com/Digital-Preservation-Finland/dpres-xml-schemas

To validate digital objects in an information package::

        python ipt/scripts/check_sip_digital_objects.py <package directory> <linking_type> <linking_value> [-c <catalog_path>]

Parameters <linking_type> and <linking_value> give values to PREMIS <relatedObjectIdentifierType> and
<relatedObjectIdentifierValues> elements in the output. If you are not planning to use these, you
may give random strings.

The option <catalog_path> can be given if local XML catalog files are to be used in the validation of
XML files.

To check fixity of digital objects in an information package::

        python ipt/scripts/check_sip_file_checksums.py <package directory>

To create local XML catalog file::

        python -m ipt/scripts/create_schema_catalog <mets_filepath> <sip_dirpath> <output_catalog_path> [-c <existing_catalog_path>]

The created local XML catalog file can be used together with
*check_sip_digital_objects*.

Copyright
---------
Copyright (C) 2018 CSC - IT Center for Science Ltd.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU Lesser General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option)
any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along
with this program. If not, see <https://www.gnu.org/licenses/>.
