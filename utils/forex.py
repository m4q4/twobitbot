#!/usr/bin/env python

import logging
import treq
from decimal import Decimal, InvalidOperation

from twisted.internet import defer

from twobitbot.utils import now_in_utc_secs

log = logging.getLogger(__name__)


class ForexConverter(object):
    def __init__(self):
        self.rates = dict()
        self.rates_last_updated = None
        self._update_rates()

    @defer.inlineCallbacks
    def convert(self, amount, from_currency, to_currency):
        """
        Convert an amount of 1 currency to the equivalent of another currency using current forex rates.
        Returns a Decimal value of the amount in the new currency.
        :type amount: int or float or Decimal
        :type from_currency: str or unicode
        :type to_currency: str or unicode
        """
        yield self._update_rates()
        try:
            from_currency = from_currency.upper()
            to_currency = to_currency.upper()
        except SyntaxError:
            raise TypeError("A currency name was not a string: '{}' and '{}'".format(from_currency, to_currency))
        try:
            amount = Decimal(amount)
        except InvalidOperation:
            raise ValueError("invalid currency amount")

        if from_currency not in self.rates:
            raise ValueError("unknown currency '{}'".format(from_currency))
        elif to_currency not in self.rates:
            raise ValueError("unknown currency '{}'".format(to_currency))
        elif amount <= 0:
            raise ValueError("invalid currency amount")
        else:
            converted = amount / self.rates[from_currency] * self.rates[to_currency]
            defer.returnValue(converted)

    @defer.inlineCallbacks
    def _update_rates(self):
        """Returns True if the data is successfully updated, otherwise False."""
        if self.rates_last_updated and now_in_utc_secs() - self.rates_last_updated < 24*60*60:
            # conversion rates table is less than 24 hours old. No need to update them
            # since the ECB/Fixer.io only updates every 24 hours.
            defer.returnValue(False)
        res = yield treq.get(url='https://api.fixer.io/latest?base=USD')
        if res and res.code == 200:
            data = yield treq.json_content(res)
            """:type: dict"""
            if 'rates' in data:
                self.rates = data['rates']
                """:type: dict"""
               # convert the floats returned to Decimals
                for k, v in self.rates.iteritems():
                    self.rates[k] = Decimal(v)
                self.rates['USD'] = Decimal(1)
                self.rates_last_updated = now_in_utc_secs()
                defer.returnValue(True)
            else:
                log.warn("Unusable response from Fixer.io forex data lookup - data returned is '{}'".format(data))
        else:
            log.warn("Bad response from Fixer.io forex data lookup, HTTP code {}".format(res.code))
        defer.returnValue(False)
