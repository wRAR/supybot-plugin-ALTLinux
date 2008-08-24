###
# Copyright (c) 2007, Andrey Rahmatullin
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

import time
import rfc822
import poplib
import textwrap
from cStringIO import StringIO as sio

import supybot.utils as utils
import supybot.world as world
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

from supybot.utils.iter import all

class ALTLinux(callbacks.Privmsg):
    """Add the help for "@help ALTLinux" here
    This should describe *how* to use this plugin."""
    threaded = True
    lastCheck = 0
    def _checkServer(self, irc):
        user = self.registryValue('user')
        server = self.registryValue('server')
        password = self.registryValue('password')
        if not server:
            raise callbacks.Error, 'There is no configured POP3 server.'
        if not user:
            raise callbacks.Error, 'There is no configured POP3 user.'
        if not password:
            raise callbacks.Error, 'There is no configured POP3 password.'
        return (server, user, password)

    def _connect(self, server, user, password):
        pop = poplib.POP3(server)
        pop.user(user)
        pop.pass_(password)
        return pop

    def _getPop(self, irc):
        return self._connect(*self._checkServer(irc))

    def _getMsgs(self, pop):
        n = len(pop.list()[1])
        for i in range(1, n+1):
            (_, lines, _) = pop.retr(i)
            yield (i, '\r\n'.join(lines))
        
    def _quit(self, pop, delete=True):
        if delete:
            n = len(pop.list()[1])
            for i in range(1, n+1):
                pop.dele(i)
        pop.quit()

    def __call__(self, irc, msg):
        now = time.time()
        if now - self.lastCheck > self.registryValue('period'):
            try:
                try:
                    t = world.SupyThread(target=self._checkForAnnouncements,
                                         args=(irc,))
                    t.setDaemon(True)
                    t.start()
                finally:
                    # If there's an error, we don't want to be checking every
                    # message.
                    self.lastCheck = now
            except callbacks.Error, e:
                self.log.warning('Couldn\'t check mail: %s', e)
            except Exception:
                self.log.exception('Uncaught exception checking for new mail:')

    def _checkForAnnouncements(self, irc):
        start = time.time()
        self.log.info('Checking mailbox for announcements.')
        pop = self._getPop(irc)
        i = None
        for (i, msg) in self._getMsgs(pop):
            message = rfc822.Message(sio(msg))
            if not message:
                continue
            subject = message.get('Subject', '')
            self.log.info('Received message with subject %q.',
                          subject)
            descr = message.get('X-git-description')
            if not descr.startswith('packages'):
                continue
            giturl = message.get('X-git-URL')
            if not giturl:
                continue
            gitdir = giturl[:giturl.find(';')]
            refname = message.get('X-git-refname')
            channels = list(self.registryValue('defaultChannels'))
            self.log.info('Making announcement to %L.', channels)
            for channel in channels:
                if channel in irc.state.channels:
                    s = 'Update of %s (%s)' % (gitdir, refname)
                    irc.queueMsg(ircmsgs.privmsg(channel, s))
        self._quit(pop)
        self.log.info('Finished checking mailbox, time elapsed: %s',
                      utils.timeElapsed(time.time() - start))

Class = ALTLinux


# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78:
