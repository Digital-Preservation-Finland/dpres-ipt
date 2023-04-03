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
Group:          System Environment/Library
License:        LGPLv3+
URL:            https://www.digitalpreservation.fi
Source0:        %{file_prefix}-v%{file_version}%{?file_release_tag}-%{file_build_number}-g%{file_commit_ref}.%{file_ext}
BuildArch:      noarch

Requires: xml-common
Requires: libxslt unzip
# ClamAV installation requires these to work
Requires: clamav libtool-ltdl
# Do we need the following Requires, they are all our own Python packages?
Requires: dpres-xml-schemas python3-xml-helpers python3-mets python3-premis
Requires: python3-file-scraper-full

BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros
BuildRequires:  %{py3_dist pip}
BuildRequires:  %{py3_dist setuptools}
BuildRequires:  %{py3_dist wheel}
BuildRequires:  %{py3_dist pytest}

%py_provides python3-dpres-ipt

%description
Tools for KDKPAS SIP/AIP/DIP-handling.

%prep
find %{_sourcedir}
%autosetup -n %{file_prefix}-v%{file_version}%{?file_release_tag}-%{file_build_number}-g%{file_commit_ref}

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files ipt

%files -f %{pyproject_files}
%license LICENSE
%doc README.rst

# TODO: For now changelot must be last, because it is generated automatically
# from git log command. Appending should be fixed to happen only after %changelog macro
%changelog

