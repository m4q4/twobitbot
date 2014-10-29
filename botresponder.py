#!/usr/bin/env python

from twisted.internet import defer, threads

import logging
import datetime
from decimal import Decimal

from twobitbot import utils, flair
from exchangelib import bitfinex

log = logging.getLogger(__name__)


class BotResponder(object):
    def __init__(self, config, exchange_watcher):
        self.config = config
        self.exchange_watcher = exchange_watcher
        try:
            self.name = self.config['botname']
        except KeyError:
            self.name = None
        self.flair = flair.Flair(self.exchange_watcher, db=self.config['flair_db'],
                                 change_delay=self.config['flair_change_delay'])

        if self.config['wolfram_alpha_api_key']:
            import wolframalpha
            self.wolframalpha = wolframalpha.Client(self.config['wolfram_alpha_api_key'])
        else:
            self.wolframalpha = False
            """:type: wolframalpha.Client"""

        self.forex = utils.ForexConverter()

        self.bfx_swap_data = dict()
        self.bfx_swap_data_time = None

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

            cmd = args[0].lower()
            args = args[1:]

            try:
                cmd_method = getattr(self, 'cmd_' + cmd)
            except AttributeError as e:
                log.debug('Invalid command {0} used by {1} with arguments {2}'.format(cmd, user, args))
            else:
                try:
                    return cmd_method(user, *args)
                except TypeError as e:
                    log.warn('Issue dispatching {0} for {1} (cmd={2}, args={3}'.format(cmd_method, user, cmd, args))

    def cmd_donate(self, user=None):
        return "Bitcoin donations accepted at %s." % (self.config['btc_donation_addr'])

    def cmd_help(self, user=None):
        return ("Commands: {0}time <location>, {0}flair <bear|bull>, {0}flair status [user], {0}flair top, "
                "{0}forex <conversion>, {0}wolfram <query>, {0}swaps").format(self.config['command_prefix'])

    @defer.inlineCallbacks
    def cmd_time(self, user, *msg):
        # small usability change since users sometimes misuse this
        # command as "!time in X" instead of "!time X"
        if len(msg) >= 2 and msg[0] == 'in':
            msg = tuple(msg[1:])

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
        # - works on website but not API (try "!math price of gas in portland oregon")
        if not self.wolframalpha:
            log.warn("Could not respond to a !math or !wolfram command because no Wolfram Alpha API key is set")
            defer.returnValue(None)
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

    def cmd_forex(self, user, *msg):
        amount = from_currency = to_currency = None
        if len(msg) == 1:
            # has to be an invocation like !forex cnyusd
            if len(msg[0]) != 6:
                return
            else:
                amount = 1
                from_currency = msg[0][:3]
                to_currency = msg[0][3:]
        elif len(msg) == 2:
            # has to be an invocation like !forex 2345 eurusd
            if len(msg[1]) != 6:
                return
            else:
                amount = msg[0]
                from_currency = msg[1][:3]
                to_currency = msg[1][3:]
        elif len(msg) == 4 and msg[2].lower == 'to':
            # has to be an invocation like !forex 123 cny to usd
            amount = msg[0]
            from_currency = msg[1]
            to_currency = msg[3]
        elif len(msg) == 0:
            # spit out help message
            return ("ECB forex rates, updated daily. Usage: "
                    "{0}forex cnyusd, {0}forex 5000 mxneur, {0}forex 9001 eur to usd.").format(
                        self.config['command_prefix'])
        else:
            # unsupported usage
            return

        if from_currency == to_currency:
            return

        converted = self.forex.convert(amount, from_currency, to_currency)
        def handle(converted):
            if converted <= 1e-4 or converted >= 1e20:
                # These are arbitrary but at least the upper cap is 100% required to avoid situations like
                # !forex 10e23892348 RUBUSD which DDoS the bot and then the channel once it finally prints it.
                return None
            amount_str = utils.truncatefloat(Decimal(amount), decimals=5, commas=True)
            converted_str = utils.truncatefloat(converted, decimals=5, commas=True)
            return "{} {} is {} {}".format(amount_str, from_currency.upper(), converted_str, to_currency.upper())
        def err(error):
            """:type error: twisted.python.failure.Failure"""
            # todo spit out an error message instead of silently doing nothing?
            error.trap(ValueError, TypeError)
        return converted.addCallbacks(handle, errback=err)

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
            return self.flair.top(count=self.config['flair_top_list_size'])

    @defer.inlineCallbacks
    def cmd_swaps(self, user, *msg):
        if not self.bfx_swap_data_time or utils.now_in_utc_secs() - self.bfx_swap_data_time > 5*30:
            self.bfx_swap_data = dict()
            # 2 for loops here so all 3 requests get sent ASAP
            for currency in ('usd', 'btc', 'ltc'):
                self.bfx_swap_data[currency] = bitfinex.lends(currency)
            for c, d in self.bfx_swap_data.iteritems():
                self.bfx_swap_data[c] = yield d
            self.bfx_swap_data_time = utils.now_in_utc_secs()
        swap_data = {}
        swap_data_strs = list()
        for currency in self.bfx_swap_data.iterkeys():
            swap_data[currency] = Decimal(self.bfx_swap_data[currency][0]['amount_lent'])
            swap_data_strs.append('{} {}'.format(currency.upper(), utils.truncatefloat(swap_data[currency], commas=True)))
        defer.returnValue("Bitfinex open swaps: {}".format(', '.join(reversed(swap_data_strs))))