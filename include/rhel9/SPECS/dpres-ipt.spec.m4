# vim:ft=spec

%define file_prefix M4_FILE_PREFIX
%define file_ext M4_FILE_EXT

%define file_version M4_FILE_VERSION
%define file_release_tag %{nil}M4_FILE_RELEASE_TAG
%define file_release_number M4_FILE_RELEASE_NUMBER
%define file_build_number M4_FILE_BUILD_NUMBER
%define file_commit_ref M4_FILE_COMMIT_REF

Name:           dpres-ipt
Version:        %{file_version}
Release:        %{file_release_number}%{file_release_tag}.%{file_build_number}.git%{file_commit_ref}%{?dist}
Summary:        Tools for KDKPAS SIP/AIP/DIP-handling
License:        LGPLv3+
URL:            https://www.digitalpreservation.fi
Source0:        %{file_prefix}-v%{file_version}%{?file_release_tag}-%{file_build_number}-g%{file_commit_ref}.%{file_ext}
BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros
BuildRequires:  %{py3_dist pip}
BuildRequires:  %{py3_dist setuptools}
BuildRequires:  %{py3_dist wheel}
BuildRequires:  %{py3_dist pytest}

%global _description %{expand:
Tools for KDKPAS SIP/AIP/DIP-handling.
}

%description %_description

%package -n python3-dpres-ipt
Summary: %{summary}
Requires: xml-common
Requires: libxslt
Requires: unzip
Requires: %{py3_dist xml-helpers}
Requires: %{py3_dist mets}
Requires: %{py3_dist premis}
Requires: %{py3_dist file-scraper}
Requires: dpres-xml-schemas
# Require the full version of file-scraper manually just in case dnf would
# install the minimal version automatically.
Requires: python3-file-scraper-full
# ClamAV installation requires these two
Requires: clamav
Requires: libtool-ltdl


%description -n python3-dpres-ipt %_description

%prep
find %{_sourcedir}
%autosetup -n %{file_prefix}-v%{file_version}%{?file_release_tag}-%{file_build_number}-g%{file_commit_ref}

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files ipt

cp -a %{buildroot}%{_bindir}/bagit-util %{buildroot}%{_bindir}/bagit-util-3
cp -a %{buildroot}%{_bindir}/check-sip-digital-objects %{buildroot}%{_bindir}/check-sip-digital-objects-3
cp -a %{buildroot}%{_bindir}/check-sip-file-checksums %{buildroot}%{_bindir}/check-sip-file-checksums-3
cp -a %{buildroot}%{_bindir}/check-xml-schema-features %{buildroot}%{_bindir}/check-xml-schema-features-3
cp -a %{buildroot}%{_bindir}/check-xml-schematron-features %{buildroot}%{_bindir}/check-xml-schematron-features-3
cp -a %{buildroot}%{_bindir}/create-schema-catalog %{buildroot}%{_bindir}/create-schema-catalog-3
cp -a %{buildroot}%{_bindir}/premis2html %{buildroot}%{_bindir}/premis2html-3

%files -n python3-dpres-ipt -f %{pyproject_files}
%license LICENSE
%doc README.rst
%{_bindir}/bagit-util*
%{_bindir}/check-sip-digital-objects*
%{_bindir}/check-sip-file-checksums*
%{_bindir}/check-xml-schema-features*
%{_bindir}/check-xml-schematron-features*
%{_bindir}/create-schema-catalog*
%{_bindir}/premis2html*

# TODO: For now changelot must be last, because it is generated automatically
# from git log command. Appending should be fixed to happen only after %changelog macro
%changelog

