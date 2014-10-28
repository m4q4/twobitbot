#!/usr/bin/env python

from twisted.internet import defer, threads
#from twisted.application import service

import logging
import datetime

from twobitbot import utils, flair

log = logging.getLogger(__name__)

# todo remove 'in' if someone misuses !time as !time in china


class BotResponder(object):
    def __init__(self, config, exchange_watcher):
        self.config = config
        self.exchange_watcher = exchange_watcher
        try:
            self.name = self.config['botname']
        except KeyError:
            self.name = None
        self.flair = flair.Flair(self.exchange_watcher, flair_db=self.config['flair_db'])

        if self.config['wolfram_alpha_api_key']:
            import wolframalpha
            self.wolframalpha = wolframalpha.Client(self.config['wolfram_alpha_api_key'])
        else:
            self.wolframalpha = False
            """:type: wolframalpha.Client"""

    def set_name(self, nickname):
        self.name = nickname

    def dispatch(self, msg, user=''):
        """ Handle a received message, dispatching it to the appropriate command responder.
        Parameters:
            msg - received message (string)
            user - who sent the message
        Return value: response message (string/deferred)"""
        # dispatching inspired by https://twistedmatrix.com/documents/current/core/examples/stdiodemo.py
        msg = msg.strip()

        # all commands are delegated to methods starting with cmd_
        if msg.startswith(self.config['command_prefix']):
            args = msg.split()
            # remove the prefix
            args[0] = args[0][len(self.config['command_prefix']):]

            cmd = args[0]
            args = args[1:]

            try:
                cmd_method = getattr(self, 'cmd_' + cmd)
            except AttributeError as e:
                log.warn('Invalid command {0} used by {1} with arguments {2}'.format(cmd, user, args))
            else:
                try:
                    return cmd_method(user, *args)
                except TypeError as e:
                    log.warn('Issue dispatching {0} for {1} (cmd={2}, args={3}'.format(cmd_method, user, cmd, args))

    def cmd_donate(self, user=None):
        return "Bitcoin donations accepted at %s." % (self.config['btc_donation_addr'])

    def cmd_help(self, user=None):
        return "Commands: {0}time <location>, {0}flair <bear|bull>, {0}flair status [user], {0}flair top".format(
            self.config['command_prefix'])

    @defer.inlineCallbacks
    def cmd_time(self, user, *msg):
        #results = re.search('!time\s+(.+?)\s*$', msg)
        #if results is not None:
        #    location = results.group(1)
        location = ' '.join(msg)
        if len(location) <= 1:
            defer.returnValue(None)
        log.info("Looking up current time in '%s' for %s" % (location, user))

        localized = yield utils.lookup_localized_time(location, datetime.datetime.utcnow(),
                                                      self.config['google_api_key'])
        if localized:
            defer.returnValue("The time in %s is %s" %
                              (localized['location'],
                               utils.format_time(localized['time'])))
        else:
            defer.returnValue("Invalid location.")

    @defer.inlineCallbacks
    def cmd_math(self, user, *msg):
        # todo:
        # - fucks up unicode (try "!math price of 1 bitcoin")
        # - messes up multi line output (try "!math licks to get to the center of a tootsie pop")
        # - unicode encoding error (try "!math size of new york city in square feet")
        # - works on website but not API (try "!math price of gas in portland oregon")
        if not self.wolframalpha:
            # todo return silently instead?
            defer.returnValue("Sorry, this command is not available because no Wolfram Alpha API key is set.")
        else:
            user_query = ' '.join(msg)
            log.info("Querying Wolfram Alpha with '{}' for '{}'".format(user_query, user))
            response = yield threads.deferToThread(self.wolframalpha.query, user_query)

            answer = next(response.results, '')
            answer = answer.text.strip() if answer else "I don't know what you mean."
            # todo replace this unicode literal with unicode_literal future import
            defer.returnValue(u"{}: {}".format(user, answer))

    def cmd_wolfram(self, user, *msg):
        return self.cmd_math(user, *msg)

    def cmd_flair(self, user, *msg):
        if len(msg) == 0:
            log.info("No flair subcommand specified, so returning %s's flair stats." % (user))
            return self.flair.status(user)

        cmd = msg[0]
        if cmd == 'bull' or cmd == 'bear':
            log.info("Attempting to change %s's flair to %s" % (user, cmd))
            return self.flair.change(user, cmd)
        elif cmd == 'status':
            target = user
            if len(msg) > 1:
                target = msg[1]
                log.info("Returning %s's flair stats for %s" % (target, user))
            else:
                log.info("Returning %s's flair stats" % (user))
            return self.flair.status(target)
        elif cmd == 'top':
            log.info("Returning top flair user statistics for %s" % (user))
            return self.flair.top()