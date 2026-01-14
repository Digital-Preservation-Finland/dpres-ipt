from setuptools import setup, find_packages

def main():
    """Install dpres-ipt Python libraries"""
    setup(
        name='ipt',
        packages=find_packages(exclude=['tests', 'tests.*']),
        setup_requires=["setuptools-scm"],
        use_scm_version={
            "write_to": "ipt/_version.py"
        },
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
            'lxml'
        ]
    )


if __name__ == '__main__':
    main()
