Two Bit Bot
=======
Twobitbot is an IRC bot built using Twisted in Python 2.7.

It has an arsenal of features aimed at Bitcoin and cryptocurrency traders, such as paper trading and whale alerts.

With a configuration file set up, it can be started with `python bot.py`.

Currently version 1.03, find up-to-date source at https://github.com/socillion/twobitbot

Features
=======
* Alerts on large orders executed on exchanges (currently limited to Bitstamp BTCUSD)
* Simple paper-trading via buy/sell chat commands
* Various other handy functions

Commands
=======
* `!time <location>`
    * Looks up the current time in a given location - use it to convert between timezones
* `!flair <bear|bull>`, `!flair status <username (optional)>`, `!flair top`
    * Flair is a paper-trading feature bound to IRC nicknames. This sacrifices some security due to users
    being able to 'steal' nicknames, but makes it a more usable feature than if it required logging in.
* `!wolfram <query>`
    * Use Wolfram Alpha to do math and get information
* `!forex <amount> <pair>`, `!forex <pair>`, `!forex amount <one currency> to <another currency>`
    * Convert between currencies using up to date forex rates.
* `!help` for a list of commands

Configuration
=======
Twobitbot is configured via INI files in the main directory - `bot.ini`, with a fallback to `default.ini`.
See `default.ini` for an explanation of available configuration options.

NOTE: currently the bot must be restarted for configuration changes to be applied.

License
=======
Twobitbot is licensed under the MIT License except where otherwise noted.
The complete text is located in `./LICENSE`.

Files & Modules
=======
* `bot` handles IRC connections and events, and is the main file.
* `termbot` an alternate interface via terminal.
* `botresponder` handles responding to user commands/events.
* `flair` encapsulates logic for the flair paper-trading game.
* `bitstampwatcher` handles interfacing with the Bitstamp exchange and is responsible for Bitstamp activity alerts.
* `utils` is a package of various utility functions.
    * `misc` contains random helpers and is imported into the package.
    * `googleapis` module with functions to interface with Google APIs, currently limited to timezone/geolocation.
    * `ratelimit` provides tools to limit the rate at which users can access services.
    * `unicodeconsole` is a fix to make unicode possible on Windows terminals.
* `flair.db` is an sqlite3 database containing flair state.
* `confspec.ini` is the INI template that `default.ini` and `bot.ini` are checked against.


Requirements
=======
Twobitbot currently can only be installed manually.
It depends on:

* `python27`
* `sqlite3`
* `configobj`
* `twisted`
* `treq`
* `pyopenssl`

* `exchangelib` at https://github.com/socillion/exchangelib
    * `autobahn`
    * `twistedpusher` at https://github.com/socillion/twistedpusher


Note: `pyopenssl` depends on `cryptography`, which can be annoying to install.
See instructions here: https://github.com/pyca/cryptography/blob/master/docs/installation.rst

Future features
=======
* Exchange wall alerts
* Support for alerts on additional exchanges, including Bitfinex, BTC-e, and Huobi
* User commands to list exchange prices, volume, etc
* Mining difficulty command?
* Competitive elements added to the flair paper-trading, such as a scoreboard. In addition, allow users to see
current sentiment (ratio of bull vs bear).
* bitfinex hidden wall detection
* change flair bear to short instead of fiat?
* last seen feature

Other Todo
=======
* rethink volume alert system
* clean up callbacks
* refactor how configuration is used and add some more options
    * rate limiting (flair and bot)
    * log file (bot.log currently hardcoded)
* finish converting all code to use Decimals (sqlite3 converter/adapter)
* possibly change flair to use BTC value instead of USD
* add telnet/web/similar interface in addition to terminal+irc?
* make auxiliary classes into twisted services
* convert to an application for use with twistd
* testing
* packaging
* add wall tracking
* add better live_orders support and Bitstamp HTTP API
* rethink logging
* Add throttle time setting again?
* finish switching BitstampWatcher to BitstampAlerter
* case insensitive commands
* add !translate command
    * not sure of feasibility, google translate is only available as a paid service
* missing: the paavo alias. Server-local patch for this?
* add alerts to twobitbot that have the different names (like zerogox/others, kraken/mobydick/etc)

* throttle flair changes based on hostname and not nick
* optional freenode username verification
* reload config file without restarting
* add swap/price formerly nickbot commands (also other nickbot stuff???)
* add small betsChange flairs:
Future flair changes:
1. remove separate btc/usd database fields
2. change buy/sell field to -1/0/1 to add shorting. Nomenclature?
3. add a tiebreaker for flair ranks to deal with 50 people having the exact same
4. Fix P/L for fiat, looks like its currently 2x e.g. 600->300 = +100%

* Maybe more easily extensible command system?
* fix repo line endings - mixed CRLF/LF. Even 1 CR somehow.
* convert string literals to unicode, experiencing bugs in situations like "{}".format(u"something")
    where the interpolated string is user input
    `from __future__ import unicode_literals`
* decide on whether to put defaults in confspec, initializers, or where. BitstampWatcher threshold, flair defaults, etc

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

Changelog
=======
v1.04
* Added commands:
    * !math and !wolfram commands via Wolfram Alpha
    * !forex conversions using ECB rates
* Updated to current exchangelib version
* Add config options: volume_alert_threshold, max_command_usage_delay, 
    flair_change_delay, flair_top_list_size, wolfram_alpha_api_key

v1.03 Apr 7, 2014
* switch bitstamp api code to twisted using TwistedPusher
* convert flair and api code to use Decimals
* improved logging
* abstract rate limiting to ratelimit.py, switch to exponential delay, and add rate limit to switching flair.
* change exchange APIs to return consistent objects
* add ban list
* split API into separate repo
* command dispatch QOL change, including arbitrary command prefixes

v1.02 Apr 2, 2014
* Fix timezone googleapi to reflect DST, encode urls properly, and return location name
* change !time to return the location name that was looked up
* clean up config reading, add google api key support
* change now_in_utc_secs to actually return UTC times
* added command !flair top
* track bitstamp orderbook age to avoid using stale data
* fix day field in format_timedelta

v1.01 Mar 26, 2014
* fixed !help, removed ping command
* converted lookup_localized_time to async (twisted/treq)
* use more config file values (server, server_port, donation_addr, bot_usage_delay)
* fix flair capitalization bug (user should be case-insensitive)
* switch to inlineCallbacks (so much more readable!)