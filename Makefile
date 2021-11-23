MOCK_CONFIG=stable-7-x86_64
ROOT=/
PREFIX=/usr
PYTHONDIR=${PREFIX}/lib/python2.7/site-packages
SHELLDIR=${PREFIX}/bin

MODULES=fileutils mets schematron sip xml xmllint

all: info

info:
	@echo
	@echo "PAS dpres-ipt"
	@echo
	@echo "Usage:"
	@echo "  make install		- Install dpres-ipt"
	@echo

install:
	# Cleanup temporary files
	rm -f INSTALLED_FILES

	# write version module
	python version.py > "ipt/version.py"

	# Use Python setuptools
	python setup.py build ; python ./setup.py install -O1 --prefix="${PREFIX}" --root="${ROOT}" --record=INSTALLED_FILES

	# setup.py seems to be unable to create directories,
	# create them here if needed

install3:
	# Cleanup temporary files
	rm -f INSTALLED_FILES

	# write version module
	python3 version.py > "ipt/version.py"

	# Use Python setuptools
	python3 setup.py build ; python3 ./setup.py install -O1 --prefix="${PREFIX}" --root="${ROOT}" --record=INSTALLED_FILES

	# setup.py seems to be unable to create directories,
	# create them here if needed

clean: clean-rpm
	find . -iname '*.pyc' -type f -delete
	find . -iname '__pycache__' -exec rm -rf '{}' \; | true

clean-rpm:
	rm -rf rpmbuild

rpm-sources:
	create-archive.sh
	preprocess-spec-m4-macros.sh include/rhel7

rpm: clean-rpm rpm-sources
	build-rpm.sh ${MOCK_CONFIG}
