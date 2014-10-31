Future features & Todo
=======
* Exchange wall alerts
* Support for alerts on additional exchanges, including Bitfinex, BTC-e, and Huobi
* User commands to list exchange prices, volume, etc
* Mining difficulty command?
* Competitive elements added to the flair paper-trading, such as a scoreboard. In addition, allow users to see
current sentiment (ratio of bull vs bear).
* bitfinex hidden wall detection
* last seen feature

Other Todo
=======
* refactor how configuration is used and add some more options
    * log file (bot.log is currently hardcoded)
* finish converting all code to use Decimals (sqlite3 converter/adapter)
* add telnet/web/similar interface in addition to terminal+irc?
* finish converting to an application for use with twistd (ircbot.tac)
    * reload config file without restarting
    * make auxiliary classes into twisted services
* testing
* packaging
* add better live_orders support and Bitstamp HTTP API
* rethink logging
* finish switching BitstampWatcher to BitstampAlerter
* add !translate command
    * not sure of feasibility, google translate is only available as a paid service
* missing: the paavo alias. Server-local patch for this?
* change !forex and future pair-related commands to use X/Y in addition to XY?

* throttle flair changes based on hostname and not nick
* optional freenode username verification
* add swap/price formerly nickbot commands (also other nickbot stuff???)
* add small bets

Future flair changes:
1. remove separate btc/usd database fields
2. change buy/sell field to -1/0/1 to add shorting. Nomenclature?
3. add a tiebreaker for flair ranks to deal with 50 people having the exact same
4. Fix P/L for fiat, looks like its currently 2x e.g. 600->300 = +100%
5. possibly change flair to use BTC value instead of USD

* Maybe more easily extensible command system?
* fix repo line endings - mixed CRLF/LF. Even 1 CR somehow.
* convert string literals to unicode, experiencing bugs in situations like "{}".format(u"something")
    where the interpolated string is user input
    `from __future__ import unicode_literals`
* decide on whether to put defaults in confspec, initializers, or where. BitstampWatcher threshold, flair defaults, etc

* make it easier to start twobitbot, need to add .. to path to run from inside the dir right now... Maybe not needed.

<eoar> think we could get the bot to tell us transactions with like >200k days destroyed or something? http://btc.blockr.io/documentation/api
<eoar> or maybe just blocks >500k?

* add volume-differentiated alerts to twobitbot 
100-250 BTC Tuna alert
250-500 BTC Dolphin alert
500-1,000 BTC Manatee alert
1,000-2,000 BTC Orca alert
2,000-5,000 BTC Whale alert
5,000-10,000 BTC Mobidick alert
10,000-50,000 BTC Leviathan alert
50,000-100,000 BTC Poseidon alert
100,000-200,000 BTC Kraken alert
200,000+ BTC Satoshi alert
