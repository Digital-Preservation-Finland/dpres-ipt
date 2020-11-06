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
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch

Requires: python3 python3-mimeparse python3-six xml-common
Requires: libxslt unzip python3-lxml
# ClamAV installation requires these to work
Requires: clamav libtool-ltdl
Requires: dpres-xml-schemas xml-helpers mets premis
Requires: file-scraper-full
BuildRequires: python3-setuptools python3-pytest
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
echo "-- INSTALLED_FILES"
cat INSTALLED_FILES
echo "--"

%clean

%files -f INSTALLED_FILES
%defattr(-,root,root,-)

# TODO: For now changelot must be last, because it is generated automatically
# from git log command. Appending should be fixed to happen only after %changelog macro
%changelog

