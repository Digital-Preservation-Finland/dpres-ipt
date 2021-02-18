# vim:ft=spec

%define file_prefix M4_FILE_PREFIX
%define file_ext M4_FILE_EXT

%define file_version M4_FILE_VERSION
%define file_release_tag %{nil}M4_FILE_RELEASE_TAG
%define file_release_number M4_FILE_RELEASE_NUMBER
%define file_build_number M4_FILE_BUILD_NUMBER
%define file_commit_ref M4_FILE_COMMIT_REF

Name:           python3-dpres-ipt
Version:        %{file_version}
Release:        %{file_release_number}%{file_release_tag}.%{file_build_number}.git%{file_commit_ref}%{?dist}
Summary:        Tools for KDKPAS SIP/AIP/DIP-handling
Group:          System Environment/Library
License:        LGPLv3+
URL:            https://www.digitalpreservation.fi
Source0:        %{file_prefix}-v%{file_version}%{?file_release_tag}-%{file_build_number}-g%{file_commit_ref}.%{file_ext}
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch

Requires: python3 python36-mimeparse python36-six xml-common
Requires: libxslt unzip python36-lxml
# ClamAV installation requires these to work
Requires: clamav libtool-ltdl
Requires: dpres-xml-schemas python3-xml-helpers python3-mets python3-premis
Requires: python3-file-scraper-full
BuildRequires: python3-setuptools python36-pytest
# We could also add a Provides but that's unnecessary, we should fix the
# dependencies that get broken by this Obsoletes. The release number here is
# intentionally 5 so that it would always be higher than what i-p-t had.
Obsoletes: information-package-tools <= 0.44-5

%description
Tools for KDKPAS SIP/AIP/DIP-handling.

%prep
find %{_sourcedir}
%setup -n %{file_prefix}-v%{file_version}%{?file_release_tag}-%{file_build_number}-g%{file_commit_ref}

%build
# do nothing

%install
make install3 PREFIX="%{_prefix}" ROOT="%{buildroot}"

# Rename executables to prevent naming collision with Python 2 RPM
sed -i 's/\/bin\/bagit-util$/\/bin\/bagit-util-3/g' INSTALLED_FILES
sed -i 's/\/bin\/check-sip-digital-objects$/\/bin\/check-sip-digital-objects-3/g' INSTALLED_FILES
sed -i 's/\/bin\/check-sip-file-checksums$/\/bin\/check-sip-file-checksums-3/g' INSTALLED_FILES
sed -i 's/\/bin\/check-xml-schema-features$/\/bin\/check-xml-schema-features-3/g' INSTALLED_FILES
sed -i 's/\/bin\/check-xml-schematron-features$/\/bin\/check-xml-schematron-features-3/g' INSTALLED_FILES
sed -i 's/\/bin\/create-schema-catalog$/\/bin\/create-schema-catalog-3/g' INSTALLED_FILES
sed -i 's/\/bin\/premis2html$/\/bin\/premis2html-3/g' INSTALLED_FILES
mv %{buildroot}%{_bindir}/bagit-util %{buildroot}%{_bindir}/bagit-util-3
mv %{buildroot}%{_bindir}/check-sip-digital-objects %{buildroot}%{_bindir}/check-sip-digital-objects-3
mv %{buildroot}%{_bindir}/check-sip-file-checksums %{buildroot}%{_bindir}/check-sip-file-checksums-3
mv %{buildroot}%{_bindir}/check-xml-schema-features %{buildroot}%{_bindir}/check-xml-schema-features-3
mv %{buildroot}%{_bindir}/check-xml-schematron-features %{buildroot}%{_bindir}/check-xml-schematron-features-3
mv %{buildroot}%{_bindir}/create-schema-catalog %{buildroot}%{_bindir}/create-schema-catalog-3
mv %{buildroot}%{_bindir}/premis2html %{buildroot}%{_bindir}/premis2html-3

echo "-- INSTALLED_FILES"
cat INSTALLED_FILES
echo "--"

%clean

%files -f INSTALLED_FILES
%defattr(-,root,root,-)

# TODO: For now changelot must be last, because it is generated automatically
# from git log command. Appending should be fixed to happen only after %changelog macro
%changelog

