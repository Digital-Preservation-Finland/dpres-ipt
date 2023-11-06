from setuptools import setup, find_packages
from version import get_version


def main():
    """Install dpres-ipt Python libraries"""
    setup(
        name='ipt',
        packages=find_packages(exclude=['tests', 'tests.*']),
        version=get_version(),
        entry_points={
            'console_scripts': [
                'bagit-util = ipt.scripts.bagit_util:main',
                'check-sip-digital-objects = ipt.scripts.check_sip_digital_objects:main',
                'check-sip-file-checksums = ipt.scripts.check_sip_file_checksums:main',
                'check-xml-schema-features = ipt.scripts.check_xml_schema_features:main',
                'check-xml-schematron-features = ipt.scripts.check_xml_schematron_features:main',
                'create-schema-catalog = ipt.scripts.create_schema_catalog:main',
                'premis2html = ipt.scripts.premis2html:main'
            ],
        },
        install_requires=[
            'python-mimeparse',
            'six',
            'lxml'
        ]
    )


if __name__ == '__main__':
    main()
