Name: Supybot-plugin-ALTLinux
Version: 0.2
Release: alt1

Summary: IRC bot written in Python - ALTLinux plugin
License: BSD
Group: Networking/IRC
Url: http://altlinux.ru/

Packager: Andrey Rahmatullin <wrar@altlinux.ru>

Source0: %name-%version.tar.bz2

BuildPreReq: python-dev

%description
Supybot is a flexible IRC bot written in python.
It features many plugins, is easy to extend and to use.

This package contains a plugin for ALT Linux channels.

%prep
%setup

%build
mkdir -p buildroot
CFLAGS="%optflags" %__python setup.py \
    install --optimize=2 \
    --root=`pwd`/buildroot \
    --record=INSTALLED_FILES

%install
cp -pr buildroot %buildroot
unset RPM_PYTHON

%files -f INSTALLED_FILES

%changelog
* Sun Sep 14 2008 Andrey Rahmatullin <wrar@altlinux.ru> 0.2-alt1
- add interaction with ALT Linux Bugzilla (search and bug info)

* Fri Sep 12 2008 Andrey Rahmatullin <wrar@altlinux.ru> 0.1.3-alt1
- second try to port to email module

* Thu Sep 11 2008 Andrey Rahmatullin <wrar@altlinux.ru> 0.1.2-alt1
- use email module instead of obsolete rfc822

* Sun Aug 24 2008 Andrey Rahmatullin <wrar@altlinux.ru> 0.1.1-alt1
- use X-git-URL instead of X-git-dir, process only packages/ dir (raorn@)

* Sat Apr 21 2007 Andrey Rahmatullin <wrar@altlinux.ru> 0.1-alt2
- print repo gitweb URL

* Wed Mar 07 2007 Andrey Rahmatullin <wrar@altlinux.ru> 0.1-alt1
- initial, based on Mailbox plugin

