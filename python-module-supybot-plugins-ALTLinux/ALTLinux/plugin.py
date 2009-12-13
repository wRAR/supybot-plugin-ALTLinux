###
# Copyright (c) 2007-2009, Andrey Rahmatullin
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
###

import cPickle as pickle
import csv
from fnmatch import fnmatch
import mailbox
from operator import itemgetter
import os
import pyinotify
import re
import stat
import time
import urllib
from xml.etree.cElementTree import ElementTree

import supybot.conf as conf
import supybot.utils as utils
import supybot.world as world
from supybot.commands import wrap
import supybot.ircmsgs as ircmsgs
import supybot.callbacks as callbacks

class ALTLinux(callbacks.Plugin):
    """The plugin for ALT Linux channels."""

    def __init__(self, irc):
        self.__parent = super(ALTLinux, self)
        self.__parent.__init__(irc)
        self.irc = irc
        self.mboxIsOpen = False
        self.watchManager = pyinotify.WatchManager()
        self.notifier = pyinotify.Notifier(self.watchManager)
        self.notifyThread = None
        self._addMboxWatch()

    def die(self):
        self.__parent.die()
        self.notifier.stop()

    def _startWatching(self):
        """Runs the inotify thread, if it doesn't exist.
        """
        if not self.notifyThread is None:
            return
        self.notifyThread = world.SupyThread(target=self.notifier.loop)
        self.notifyThread.setDaemon(True)
        self.notifyThread.start()

    def _validateMboxPath(self, path):
        return path is not None and os.path.isfile(path)

    def _openMbox(self, path):
        """Opens and returns the mailbox.
        """
        if os.stat(path)[stat.ST_SIZE] == 0:
            return None
        mbox = mailbox.mbox(path, create=False)
        try:
            mbox.lock()
        except mailbox.ExternalClashError:
            mbox.close()
            return None
        self.mboxIsOpen = True
        return mbox

    def _getMsgs(self, mbox):
        while len(mbox):
            (_, message) = mbox.popitem()
            yield message

    def _closeMbox(self, mbox):
        mbox.close()
        self.mboxIsOpen = False

    def _handleMboxEvent(self, event):
        """Handles inotify events for the mailbox.
        """
        if event.mask == pyinotify.IN_IGNORED:
            # mbox.flush() recreates the file
            while not self._addMboxWatch():
                pass
        if event.mask != pyinotify.IN_CLOSE_WRITE:
            return
        if self.mboxIsOpen:
            return
        self._checkMbox(event.path)

    def _checkMbox(self, path):
        """Checks the mailbox for messages and makes announces.
        """
        mbox = self._openMbox(path)
        if mbox is None:
            return
        for message in self._getMsgs(mbox):
            if not message:
                continue
            subject = message.get('Subject', '')
            self.log.info('Received message with subject %q.',
                          subject)
            descr = message.get('X-git-description')
            if not descr or not descr.startswith('packages'):
                continue
            giturl = message.get('X-git-URL')
            if not giturl:
                continue
            gitdir = giturl[:giturl.find(';')]
            refname = message.get('X-git-refname')
            for channel in list(self.registryValue('gitaltMailChannels')):
                if channel in self.irc.state.channels:
                    s = 'Update of %s (%s)' % (gitdir, refname)
                    self.irc.queueMsg(ircmsgs.privmsg(channel, s))
        self._closeMbox(mbox)

    def _addMboxWatch(self):
        """Adds an inotify watch for the mailbox, then checks it for the messages.
        """
        path = self.registryValue('gitaltMboxPath')
        if not self._validateMboxPath(path):
            return False
        self.watchManager.add_watch(path,
                                    pyinotify.IN_CLOSE_WRITE,
                                    self._handleMboxEvent)
        self._startWatching()
        self._checkMbox(path)
        return True

# Bugzilla
    bugzillaRoot = 'https://bugzilla.altlinux.org/'

    def altbug(self, irc, msg, args, bugno):
        """<bug number>

        Shows information about specified bug from ALT Linux bugzilla.
        """
        def _formatEmail(e):
            if e.get('name'):
                return '%s <%s>' % (self._encode(e.get('name')), e.text)
            return e.text

        try:
            bugXML = utils.web.getUrlFd(self.bugzillaRoot +
                    'show_bug.cgi?ctype=xml&excludefield=attachmentdata&'
                    'excludefield=long_desc&excludefield=attachment&id=' +
                    str(bugno))
        except utils.web.Error, err:
            irc.error(err.message)
            return
        etree = ElementTree(file=bugXML)
        bugRoot = etree.find('bug')
        buginfo = {
                'bug_id':               bugRoot.find('bug_id').text,
                'summary':              self._encode(bugRoot.find('short_desc').text),
                'creation_time':        bugRoot.find('creation_ts').text,
                'last_change_time':     bugRoot.find('delta_ts').text,
                'bug_severity':         bugRoot.find('bug_severity').text,
                'bug_status':           bugRoot.find('bug_status').text,
                'resolution':           ' ' + bugRoot.find('resolution').text
                                            if bugRoot.find('resolution') != None
                                            else '',
                'product':              self._encode(bugRoot.find('product').text),
                'component':            bugRoot.find('component').text,
                'reporter':             _formatEmail(bugRoot.find('reporter')),
                'assigned_to':          _formatEmail(bugRoot.find('assigned_to')),
                }
        irc.reply('%(bug_id)s: %(bug_severity)s, %(bug_status)s'
                '%(resolution)s; %(product)s - %(component)s; created on '
                '%(creation_time)s by %(reporter)s, assigned to '
                '%(assigned_to)s, last changed on %(last_change_time)s; '
                'summary: "%(summary)s"' % buginfo)
        bugXML.close()
    altbug = wrap(altbug, [('id', 'bug')])

    def searchbug(self, irc, msg, args, terms):
        """<search terms>

        Searches ALT Linux bugzilla for specified terms and shows bugs found.
        """
        try:
            bugsCSV = utils.web.getUrlFd(self.bugzillaRoot +
                    'buglist.cgi?query_format=specific&order=relevance+desc&'
                    'bug_status=__all__&ctype=csv&content=' +
                    urllib.quote_plus(self._decode(terms).encode('utf-8')))
        except utils.web.Error, err:
            irc.error(err.message)
            return
        reader = csv.DictReader(bugsCSV)
        reply = []
        for record in reader:
            record = dict([(k, v.decode('utf-8')) for k, v in
                record.iteritems()])
            reply.append('%(bug_id)s %(bug_status)s %(resolution)s "%(short_desc)s"' %
                    record)
        bugsCSV.close()
        if reply:
            irc.reply(self._encode('; '.join(reply)))
    searchbug = wrap(searchbug, ['text'])

# git.altlinux.org
    _gitaltCacheFilename = conf.supybot.directories.data.dirize(
            'ALTLinux.gitalt.cache')
    _gitaltCacheTimestamp = None
    _gitaltCache = None

    def gitalt(self, irc, msg, args, pattern):
        """<name or search pattern>

        Shows git.altlinux.org repositories for package specified. Package
        name can contain fnmatch-style wildcards.
        """
        packages = self._getGitaltList()
        if packages is None:
            return
        found = []
        if pattern in packages:
            found.extend([(pattern, p, t) for p, t in
                packages[pattern].iteritems()])
        else:
            for package, packagers in packages.iteritems():
                if fnmatch(package, pattern):
                    found.extend([(package, p, t) for p, t in
                        packagers.iteritems()])
        reply = []
        for package, packager, tm in sorted(found, key=itemgetter(2),
                reverse=True):
            reply.append('/people/%s/packages/%s: %s' % (packager, package,
                    time.strftime('%Y-%m-%d', time.gmtime(tm))))
        irc.reply('; '.join(reply) if reply else 'Nothing found')
    gitalt = wrap(gitalt, ['somethingWithoutSpaces'])

    def _getGitaltList(self):
        """Returns parsed git.alt packages list.
        """
        if self._gitaltCacheTimestamp is None or (time.time() - self._gitaltCacheTimestamp >
                self.registryValue('gitaltListRefreshPeriod')):
            self._updateGitaltCache()
        return self._gitaltCache

    def _updateGitaltCache(self):
        """Updates git.alt packages list caches, if needed.
        """
        if os.path.exists(self._gitaltCacheFilename):
            lastUpdated = os.stat(self._gitaltCacheFilename)[stat.ST_MTIME]
            if time.time() - lastUpdated < self.registryValue('gitaltListRefreshPeriod'):
                if self._gitaltCacheTimestamp is None:
                    fd = open(self._gitaltCacheFilename, 'rb')
                    self._gitaltCache = pickle.load(fd)
                    self._gitaltCacheTimestamp = lastUpdated
                    fd.close()
                return
        try:
            gitaltList = utils.web.getUrlFd(
                    'http://git.altlinux.org/people-packages-list')
        except utils.web.Error, err:
            self.irc.error(err.message)
            return
        r = re.compile(
                r'^/people/(?P<packager>[a-z0-9_]+)/packages/(?P<package>.*?)\.git\t(?P<time>\d+)$')
        packages = {}
        for line in gitaltList:
            match = r.match(line)
            packages.setdefault(match.group('package'), {})[
                    match.group('packager')] = int(match.group('time'))
        gitaltList.close()
        self._gitaltCache = packages
        self._gitaltCacheTimestamp = time.time()

        fd = utils.file.AtomicFile(self._gitaltCacheFilename, 'wb')
        pickle.dump(packages, fd, -1)
        fd.close()

    def _encode(self, s):
        return s.encode(self.registryValue('channelEncoding'))
    def _decode(self, s):
        return s.decode(self.registryValue('channelEncoding'))

Class = ALTLinux

# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78:
