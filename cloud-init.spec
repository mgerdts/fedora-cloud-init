Name:           cloud-init
Version:        0.7.9
Release:        4%{?dist}
Summary:        Cloud instance init scripts
License:        GPLv3
URL:            http://launchpad.net/cloud-init

Source0:        https://launchpad.net/cloud-init/trunk/%{version}/+download/%{name}-%{version}.tar.gz
Source1:        cloud-init-fedora.cfg
Source2:        cloud-init-README.fedora
Source3:        cloud-init-tmpfiles.conf

Patch0:         cloud-init-0.7.8-fedora.patch

# Fix rsyslog log filtering
# https://code.launchpad.net/~gholms/cloud-init/rsyslog-programname/+merge/186906
Patch1:         cloud-init-0.7.5-rsyslog-programname.patch

# Add 3 ecdsa-sha2-nistp* ssh key types now that they are standardized
# https://bugzilla.redhat.com/show_bug.cgi?id=1151824
# https://bugs.launchpad.net/cloud-init/+bug/1658174
# https://git.launchpad.net/cloud-init/commit/?id=853df0a0e85002582694b88db886f206f64b23c7
Patch3:         cloud-init-0.7.9-ecdsa.patch

# Use dnf instead of yum when available
# https://bugzilla.redhat.com/show_bug.cgi?id=1194451
Patch7:         cloud-init-0.7.8-dnf.patch

# Skip apt-source tests that are sensitive to the system's hostname
# https://bugs.launchpad.net/cloud-init/+bug/1629149
Patch8:         cloud-init-0.7.8-apt-dns-test.patch

# Do not write NM_CONTROLLED=no in generated interface config files
# https://bugzilla.redhat.com/show_bug.cgi?id=1385172
Patch11:        cloud-init-0.7.8-nm-controlled.patch

# Disable tests that require pylxd
Patch12:        cloud-init-0.7.9-disable-lxd-tests.patch

# Fix calls to hostnamectl occurring before dbus is up
# https://bugzilla.redhat.com/show_bug.cgi?id=1417025
# Fix systemd dependency cycle with cloud-init and multi-user.target
# https://bugzilla.redhat.com/show_bug.cgi?id=1428492
# https://bugzilla.redhat.com/show_bug.cgi?id=1430511
Patch13:        cloud-init-0.7.9-systemd-cloud-init.patch

# Fix systemd dependency cycle with cloud-final and os-collect-config
# https://bugzilla.redhat.com/show_bug.cgi?id=1420946
# https://bugzilla.redhat.com/show_bug.cgi?id=1428492
Patch14:        cloud-init-0.7.9-systemd-cloud-final.patch

# Fix errors in network sysconfig handling
# https://bugzilla.redhat.com/show_bug.cgi?id=1389530
# https://bugs.launchpad.net/cloud-init/+bug/1665441
# https://git.launchpad.net/cloud-init/commit/?id=f81d6c7bde2af206d449de593b35773068270c84
Patch15:        cloud-init-0.7.9-sysconfig-iface.patch

# Make > 3 name servers a warning, not a fatal error
# This is useful when both IPv4 and IPv6 name servers are present.
# https://bugs.launchpad.net/cloud-init/+bug/1670052
# https://git.launchpad.net/cloud-init/commit/?id=657fd40f9ee692a817ec4614cd0d6cb0539ffabf
Patch16:        cloud-init-0.7.9-gt3-nameservers.patch

# Fix IPv6 gateways in network sysconfig
# https://bugs.launchpad.net/cloud-init/+bug/1669504
# https://git.launchpad.net/cloud-init/commit/?id=1d751a6f46f044e3c3827f3cef0e4a2e71d50fe7
Patch17:        cloud-init-0.7.9-ipv6-gateway.patch

BuildArch:      noarch

BuildRequires:  pkgconfig(systemd)
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  systemd

# For tests
BuildRequires:  iproute
BuildRequires:  python3-configobj
BuildRequires:  python3-httpretty
BuildRequires:  python3-jinja2
BuildRequires:  python3-jsonpatch
BuildRequires:  python3-mock
BuildRequires:  python3-nose
BuildRequires:  python3-oauthlib
BuildRequires:  python3-prettytable
BuildRequires:  python3-pyserial
BuildRequires:  python3-PyYAML
BuildRequires:  python3-requests
BuildRequires:  python3-six
BuildRequires:  python3-unittest2

Requires:       e2fsprogs
Requires:       iproute
Requires:       libselinux-python3
Requires:       net-tools
Requires:       policycoreutils-python3
Requires:       procps
Requires:       python3-configobj
Requires:       python3-jinja2
Requires:       python3-jsonpatch
Requires:       python3-oauthlib
Requires:       python3-prettytable
Requires:       python3-pyserial
Requires:       python3-PyYAML
Requires:       python3-requests
Requires:       python3-six
Requires:       shadow-utils
Requires:       util-linux
Requires:       xfsprogs

%{?systemd_requires}


%description
Cloud-init is a set of init scripts for cloud instances.  Cloud instances
need special scripts to run during initialization to retrieve and install
ssh keys and to let the user run various scripts.


%prep
%autosetup -p1

# Change shebangs
sed -i -e 's|#!/usr/bin/env python|#!/usr/bin/env python3|' \
       -e 's|#!/usr/bin/python|#!/usr/bin/python3|' tools/* cloudinit/ssh_util.py

cp -p %{SOURCE2} README.fedora


%build
%{__python3} setup.py build


%install
%{__python3} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT --init-system=systemd

# Don't ship the tests
rm -r $RPM_BUILD_ROOT%{python3_sitelib}/tests

mkdir -p $RPM_BUILD_ROOT/var/lib/cloud

# /run/cloud-init needs a tmpfiles.d entry
mkdir -p $RPM_BUILD_ROOT/run/cloud-init
mkdir -p $RPM_BUILD_ROOT/%{_tmpfilesdir}
cp -p %{SOURCE3} $RPM_BUILD_ROOT/%{_tmpfilesdir}/%{name}.conf

# We supply our own config file since our software differs from Ubuntu's.
cp -p %{SOURCE1} $RPM_BUILD_ROOT/%{_sysconfdir}/cloud/cloud.cfg

mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/rsyslog.d
cp -p tools/21-cloudinit.conf $RPM_BUILD_ROOT/%{_sysconfdir}/rsyslog.d/21-cloudinit.conf


%check
# python-httpretty-0.8.14 broke several GCE tests
# https://github.com/gabrielfalcao/HTTPretty/issues/316
nosetests-%{python3_version} tests/unittests/ \
    -e test_instance_level_keys_replace_project_level_keys \
    -e test_instance_level_ssh_keys_are_used \
    -e test_metadata_encoding


%post
%systemd_post cloud-config.service cloud-config.target cloud-final.service cloud-init.service cloud-init.target cloud-init-local.service


%preun
%systemd_preun cloud-config.service cloud-config.target cloud-final.service cloud-init.service cloud-init.target cloud-init-local.service


%postun
%systemd_postun


%files
%license LICENSE
%doc ChangeLog README.fedora
%doc doc/*
%config(noreplace) %{_sysconfdir}/cloud/cloud.cfg
%dir               %{_sysconfdir}/cloud/cloud.cfg.d
%config(noreplace) %{_sysconfdir}/cloud/cloud.cfg.d/*.cfg
%doc               %{_sysconfdir}/cloud/cloud.cfg.d/README
%dir               %{_sysconfdir}/cloud/templates
%config(noreplace) %{_sysconfdir}/cloud/templates/*
%dir               %{_sysconfdir}/rsyslog.d
%config(noreplace) %{_sysconfdir}/rsyslog.d/21-cloudinit.conf
%{_sysconfdir}/NetworkManager/dispatcher.d/hook-network-manager
/lib/udev/rules.d/66-azure-ephemeral.rules
%{_unitdir}/cloud-config.service
%{_unitdir}/cloud-final.service
%{_unitdir}/cloud-init.service
%{_unitdir}/cloud-init-local.service
%{_unitdir}/cloud-config.target
%{_unitdir}/cloud-init.target
/usr/lib/systemd/system-generators/cloud-init-generator
%{_tmpfilesdir}/%{name}.conf
%{python3_sitelib}/*
%{_libexecdir}/%{name}
%{_bindir}/cloud-init*
%dir /run/cloud-init
%dir /var/lib/cloud


%changelog
* Tue Mar 14 2017 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.9-4
- Fixed systemd dependency cycle with cloud-final and os-collect-config [RH:1420946, RH:1428492]
- Fixed systemd dependency cycle with cloud-init and multi-user.target [RH:1428492, RH:1430511]
- Fixed errors in network sysconfig handling [RH:1389530, LP:1665441]
- Made > 3 name servers a warning, not a fatal error, unbreaking IPv6 setups [LP:1670052]
- Fixed IPv6 gateways in network sysconfig [LP:1669504]

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.7.9-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Fri Jan 27 2017 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.9-2
- Fixed hostnamectl running before dbus is up [RH:1417025]

* Fri Jan 27 2017 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.8-5
- Re-applied rsyslog configuration fixes
- Disabled GCE tests broken by python-httpretty-0.8.14-1.20161011git70af1f8
- Fixed systemd dependency loop for cloud-init.target [RH:1393094]

* Fri Jan 20 2017 Colin Walters <walters@verbum.org> - 0.7.9-1
- New upstream version [RH:1393094]

* Tue Dec 13 2016 Charalampos Stratakis <cstratak@redhat.com> - 0.7.8-4
- Rebuild for Python 3.6

* Tue Oct 25 2016 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.8-3
- Enabled the DigitalOcean metadata provider by default [RH:1388568]

* Fri Oct 14 2016 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.8-2
- Stopped writing NM_CONTROLLED=no to interface config files [RH:1385172]

* Thu Sep 29 2016 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.8-1
- Updated to 0.7.8
- Dropped run-parts dependency [RH:1355917]
- Ordered cloud-init-local before NetworkManager
- Backported DigitalOcean network configuration support [RH:1380489]
- Added xfsprogs dependency for Fedora Server's default filesystem

* Tue Aug 30 2016 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.7-1
- Updated to 0.7.7

* Tue Jul 19 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.7.6-10.20160622bzr1245
- https://fedoraproject.org/wiki/Changes/Automatic_Provides_for_Python_RPM_Packages

* Wed Jul  6 2016 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.6-20160622bzr1245
- Updated to bzr snapshot 1245

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 0.7.6-8.20150813bzr1137
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Tue Nov 10 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.7.6-7.20150813bzr1137
- Rebuilt for https://fedoraproject.org/wiki/Changes/python3.5

* Thu Aug 13 2015 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.6-6.20150813bzr1137
- Updated to bzr snapshot 1137

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.7.6-5.20140218bzr1060
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Sat Feb 21 2015 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.6-4.20140218bzr1060
- Updated to bzr snapshot 1060 for python 3 support
- Switched to python 3 [RH:1024357]
- Added %%check
- Dropped dmidecode dependency, switched back to noarch

* Thu Feb 19 2015 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.6-3
- Stopped depending on git to build
- Stopped implicitly listing doc files twice
- Added recognition of 3 ecdsa-sha2-nistp* ssh key types [RH:1151824]
- Fixed handling of user group lists that contain spaces [RH:1126365 LP:1354694]
- Changed network.target systemd deps to network-online.target [RH:1110731 RH:1112817 RH:1147613]
- Fixed race condition between cloud-init.service and the login prompt
- Stopped enabling services in %%post (now done by kickstart) [RH:850058]
- Switched to dnf instead of yum when available [RH:1194451]

* Fri Nov 14 2014 Colin Walters <walters@redhat.com> - 0.7.6-2
- New upstream version [RH:974327]
- Drop python-cheetah dependency (same as above bug)

* Fri Nov  7 2014 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.5-8
- Dropped python-boto dependency [RH:1161257]
- Dropped rsyslog dependency [RH:986511]

* Sat Aug 16 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.7.5-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Thu Jun 12 2014 Dennis Gilmore <dennis@ausil.us> - 0.7.5-6
- fix typo in settings.py preventing metadata being fecthed in ec2

* Mon Jun  9 2014 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.5-5
- Stopped calling ``udevadm settle'' with --quiet since systemd 213 removed it

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.7.5-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Mon Jun  2 2014 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.5-3
- Make dmidecode dependency arch-dependent [RH:1025071 RH:1067089]

* Mon Jun  2 2014 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.2-9
- Write /etc/locale.conf instead of /etc/sysconfig/i18n [RH:1008250]
- Add tmpfiles.d configuration for /run/cloud-init [RH:1103761]
- Use the license rpm macro
- BuildRequire python-setuptools, not python-setuptools-devel

* Fri May 30 2014 Matthew Miller <mattdm@fedoraproject.org> - 0.7.5-2
- add missing python-jsonpatch dependency [RH:1103281]

* Tue Apr 29 2014 Sam Kottler <skottler@fedoraproject.org> - 0.7.5-1
- Update to 0.7.5 and remove patches which landed in the release

* Sat Jan 25 2014 Sam Kottler <skottler@fedoraproject.org> - 0.7.2-8
- Remove patch to the Puppet service unit nane [RH:1057860]

* Tue Sep 24 2013 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.2-7
- Dropped xfsprogs dependency [RH:974329]

* Tue Sep 24 2013 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.2-6
- Added yum-add-repo module

* Fri Sep 20 2013 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.2-5
- Fixed puppet agent service name [RH:1008250]
- Let systemd handle console output [RH:977952 LP:1228434]
- Fixed restorecon failure when selinux is disabled [RH:967002 LP:1228441]
- Fixed rsyslog log filtering
- Added missing modules [RH:966888]

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.7.2-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Sat Jun 15 2013 Matthew Miller <mattdm@fedoraproject.org> - 0.7.2-3
- switch ec2-user to "fedora" --  see bugzilla #971439. To use another
  name, use #cloud-config option "users:" in userdata in cloud metadata
  service
- add that user to systemd-journal group

* Fri May 17 2013 Steven Hardy <shardy@redhat.com> - 0.7.2
- Update to the 0.7.2 release

* Thu May 02 2013 Steven Hardy <shardy@redhat.com> - 0.7.2-0.1.bzr809
- Rebased against upstream rev 809, fixes several F18 related issues
- Added dependency on python-requests

* Sat Apr  6 2013 Orion Poplawski <orion@cora.nwra.com> - 0.7.1-4
- Don't ship tests

* Wed Feb 13 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.7.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Thu Dec 13 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.1-2
- Added default_user to cloud.cfg (this is required for ssh keys to work)

* Wed Nov 21 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.1-1
- Rebased against version 0.7.1
- Fixed broken sudoers file generation
- Fixed "resize_root: noblock" [LP:1080985]

* Tue Oct  9 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.0-1
- Rebased against version 0.7.0
- Fixed / filesystem resizing

* Sat Sep 22 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.0-0.3.bzr659
- Added dmidecode dependency for DataSourceAltCloud

* Sat Sep 22 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.0-0.2.bzr659
- Rebased against upstream rev 659
- Fixed hostname persistence
- Fixed ssh key printing
- Fixed sudoers file permissions

* Mon Sep 17 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.0-0.1.bzr650
- Rebased against upstream rev 650
- Added support for useradd --selinux-user

* Thu Sep 13 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.3-0.5.bzr532
- Use a FQDN (instance-data.) for instance data URL fallback [RH:850916 LP:1040200]
- Shut off systemd timeouts [RH:836269]
- Send output to the console [RH:854654]

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.3-0.4.bzr532
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Wed Jun 27 2012 Pádraig Brady <P@draigBrady.com> - 0.6.3-0.3.bzr532
- Add support for installing yum packages

* Sat Mar 31 2012 Andy Grimm <agrimm@gmail.com> - 0.6.3-0.2.bzr532
- Fixed incorrect interpretation of relative path for
  AuthorizedKeysFile (BZ #735521)

* Mon Mar  5 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.3-0.1.bzr532
- Rebased against upstream rev 532
- Fixed runparts() incompatibility with Fedora

* Thu Jan 12 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.2-0.8.bzr457
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Wed Oct  5 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.7.bzr457
- Disabled SSH key-deleting on startup

* Wed Sep 28 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.6.bzr457
- Consolidated selinux file context patches
- Fixed cloud-init.service dependencies
- Updated sshkeytypes patch
- Dealt with differences from Ubuntu's sshd

* Sat Sep 24 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.5.bzr457
- Rebased against upstream rev 457
- Added missing dependencies

* Fri Sep 23 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.4.bzr450
- Added more macros to the spec file

* Fri Sep 23 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.3.bzr450
- Fixed logfile permission checking
- Fixed SSH key generation
- Fixed a bad method call in FQDN-guessing [LP:857891]
- Updated localefile patch
- Disabled the grub_dpkg module
- Fixed failures due to empty script dirs [LP:857926]

* Fri Sep 23 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.2.bzr450
- Updated tzsysconfig patch

* Wed Sep 21 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.1.bzr450
- Initial packaging
