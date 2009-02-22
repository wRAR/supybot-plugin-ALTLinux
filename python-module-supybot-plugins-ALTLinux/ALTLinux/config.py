###
# Copyright (c) 2007-2008, Andrey Rahmatullin
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

import supybot.conf as conf
import supybot.registry as registry

def configure(advanced):
    conf.registerPlugin('ALTLinux', True)


ALTLinux = conf.registerPlugin('ALTLinux')
conf.registerGlobalValue(ALTLinux, 'channelEncoding',
    registry.String('koi8-r', """Determines the encoding used to encode and
    decode channel messages"""))
# git.alt mail announcements
conf.registerGlobalValue(ALTLinux, 'gitaltMailServer',
    registry.String('', """Determines what POP3 server to connect to in order
    to check for email."""))
conf.registerGlobalValue(ALTLinux, 'gitaltMailUser',
    registry.String('', """Determines what username to give to the POP3 server
    when connecting."""))
conf.registerGlobalValue(ALTLinux, 'gitaltMailPassword',
    registry.String('', """Determines what password to give to the POP3 server
    when connecting.""", private=True))
conf.registerGlobalValue(ALTLinux, 'gitaltMailPeriod',
    registry.PositiveInteger(60, """Determines how often the bot will check
    the POP3 server for new messages to announce."""))
conf.registerGlobalValue(ALTLinux, 'gitaltMailChannels',
    conf.SpaceSeparatedSetOfChannels([], """Determines to which channels the
    bot will send messages"""))
# git.alt repository list
conf.registerGlobalValue(ALTLinux, 'gitaltListRefreshPeriod',
    registry.PositiveInteger(14400, """Determines how often the bot will
    download git.alt repository list."""))


# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78