# libfprint + the experimental EgisTec EH575 (1c7a:0575) driver.
# Research project: https://github.com/cosct/libfprint-egis0575
# Release CI builds this spec with --define "version <driver-version>".
%define drvver %{?version}%{!?version:0.2.3}
%define debug_package %{nil}
# libfprint base bundled with the driver (root meson.build version:)
%define lfver 1.94.100

Name:           libfprint-egis0575
Version:        %{drvver}
Release:        1%{?dist}
Summary:        libfprint with the experimental EgisTec EH575 (1c7a:0575) driver
License:        LGPL-2.1-or-later
URL:            https://github.com/edi194/libfprint-egis0575
Source0:        %{url}/archive/refs/tags/egis0575-v%{drvver}.tar.gz
ExclusiveArch:  x86_64

BuildRequires:  meson ninja-build gcc gcc-c++
BuildRequires:  glib2-devel libgusb-devel pixman-devel libusb1-devel
BuildRequires:  systemd-devel openssl-devel libgudev-devel

Provides:       libfprint = %{lfver}
Provides:       libfprint%{?_isa} = %{lfver}
Provides:       libfprint-2.so.2()(64bit)
Conflicts:      libfprint%{?_isa}
# the package also ships the libfprint headers/pkgconfig files
Conflicts:      libfprint-devel%{?_isa}

%description
libfprint plus the egis0575 press-snapshot driver with a Windows-engine
matcher port, for the EgisTec EH575 (1c7a:0575) fingerprint sensor.
Replaces the distribution libfprint for devices that need this driver.

%prep
# single-repo layout: the tag tarball extracts to libfprint-egis0575-<tag>/
# with the libfprint meson tree in a subdirectory
%setup -q -n libfprint-egis0575-egis0575-v%{drvver}

%build
cd libfprint
# udev_hwdb=enabled: meson's auto mode drops the autosuspend hwdb when
# systemd >= 248 ships one, but systemd's list lacks the out-of-tree EH575.
%meson -D introspection=false -D doc=false -D installed-tests=false \
  -D gtk-examples=false \
  -D udev_rules_dir=/usr/lib/udev/rules.d \
  -D udev_hwdb=enabled -D udev_hwdb_dir=/usr/lib/udev/hwdb.d
%meson_build

%install
cd libfprint
%meson_install

%post
/sbin/ldconfig
# apply the udev rules and rebuild the hwdb database right away
udevadm control --reload || :
udevadm hwdb --update || :

%postun
/sbin/ldconfig
udevadm hwdb --update || :

%files
%license libfprint/COPYING
%{_libdir}/libfprint-2.so
%{_libdir}/libfprint-2.so.*
%{_libdir}/pkgconfig/libfprint-2.pc
%{_includedir}/libfprint-2/
/usr/lib/udev/rules.d/70-libfprint-2.rules
/usr/lib/udev/hwdb.d/60-autosuspend-libfprint-2.hwdb
%{_datadir}/metainfo/org.freedesktop.libfprint.metainfo.xml

%changelog
* Sun Oct 11 2026 edi194 <edi194@users.noreply.github.com> - 0.2.3-1
- Fork release (F1 + F1r2): run the full calibration chain on every
  claim instead of the upload-only re-arm (bare POST_RESET+upload left
  the sensor imaging dead after a Linux-style session teardown: all-0xFF
  frames, coverage=0, first claim per fprintd process only), stash the
  previous session's validated calibration block and adopt it in the
  broken-read recovery ladder (saves enroll, which has no
  template-embedded fallback), and raise the re-read budget 7 -> 20.
  Validated on an Acer Swift SF314-42 (EgisTec EH575), Fedora 44,
  kernel 6.19.10-300.fc44.x86_64, fprintd 1.94.5.
* Sun Sep 13 2026 cosct-ci <cosct@outlook.com> - 0.2.2-1
- Released via the release workflow (tag egis0575-v0.2.2).

* Sun Sep 13 2026 cosct <cosct@outlook.com> - 0.2.1-1
- v0.2.1: enrollment same-spot rejection (threshold 650), host-side
  calibration cache surviving close, two-tier idle polling.

* Sun Sep 13 2026 cosct <cosct@outlook.com> - 0.2.0-1
- Initial packaging of the egis0575 experimental driver (libfprint 1.94.100 + EH575).
