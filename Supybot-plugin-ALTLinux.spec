Name: Supybot-plugin-ALTLinux
Version: 0.1
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
* Wed Mar 07 2007 Andrey Rahmatullin <wrar@altlinux.ru> 0.1-alt1
- initial, based on Mailbox plugin

