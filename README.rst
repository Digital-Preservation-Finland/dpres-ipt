Information Package Tools
=========================

This repository contains tools for validating Submission/Archival/Dissemination Information
Packages (SIP/AIP/DIP) based on Open Archival Information System (OAIS) standard.

The aim is to provide digital preservation services for culture and research to ensure
the access and use of materials long in the future. Documentation and specifications
for the digital preservation service can be found in: http://digitalpreservation.fi

Requirements
------------

Installation and usage requires Python 3.9 or newer.
The software is tested with Python 3.9 on AlmaLinux 9 release.

Installation using RPM packages (preferred)
-------------------------------------------

Installation on Linux distributions is done by using the RPM Package Manager.
See how to `configure the PAS-jakelu RPM repositories`_ to setup necessary software sources.

.. _configure the PAS-jakelu RPM repositories: https://www.digitalpreservation.fi/user_guide/installation_of_tools 

After the repository has been added, the package can be installed by running the following command::

    sudo dnf install python3-dpres-ipt

Usage
-----

To validate a METS document::

    check-xml-schema-features <METS document>
    check-xml-schematron-features -s <schematron_file> <METS document>

See the schematron files from: https://github.com/Digital-Preservation-Finland/dpres-xml-schemas

To validate digital objects in an information package::

    check-sip-digital-objects <package directory> <linking_type> <linking_value> [-c <catalog_path>]

Parameters <linking_type> and <linking_value> give values to PREMIS <relatedObjectIdentifierType> and
<relatedObjectIdentifierValues> elements in the output. If you are not planning to use these, you
may give random strings.

The option <catalog_path> can be given if local XML catalog files are to be used in the validation of
XML files.

To check fixity of digital objects in an information package::

    check-sip-file-checksums <package directory>

To create local XML catalog file::

    create-schema-catalog <mets_filepath> <sip_dirpath> <output_catalog_path> [-c <existing_catalog_path>]

The created local XML catalog file can be used together with
``check-sip-digital-objects``.

Installation using Python Virtualenv for development purposes
-------------------------------------------------------------

The following software is required for validation tools.

* dpres-xml-schemas, see https://github.com/Digital-Preservation-Finland/dpres-xml-schemas
* See the README from file-scraper repository for additional installation requirements:
  https://github.com/Digital-Preservation-Finland/file-scraper/blob/master/README.rst

Create a virtual environment::
    
    python3 -m venv venv

Run the following to activate the virtual environment::

    source venv/bin/activate

Install the required software with commands::

    pip install --upgrade pip==20.2.4 setuptools
    pip install -r requirements_github.txt
    pip install .

To deactivate the virtual environment, run ``deactivate``.
To reactivate it, run the ``source`` command above.

NOTE: Running unit tests requires the full installation of file-scraper with all its requirements.

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
