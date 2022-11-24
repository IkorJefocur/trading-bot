from sys import exit
from os import environ, path, makedirs
from signal import signal, SIGINT, SIGTERM
from asyncio import new_event_loop
from traceback import print_exc
from yaml import load, CLoader
from dotenv import load_dotenv
from project.models.position import Symbol
from project.models.market import Market
from project.models.trader import Trader, User
from project.models.meta import TraderMeta
from project.models.strategy import TradingStrategy, CopytradingStrategy
from project.services.http_client import HTTPClient
from project.services.bybit import Bybit
from project.services.telegram import Telegram
from project.plugins.binance_trader_watch import BinanceTraderProfitableWatch
from project.plugins.user_sync import UserSync, CopytradingUserSync
from project.plugins.market_sync import MarketSync, CopytradingMarketSync
from project.plugins.copy_trade import CopyTrade, CopyCopytrade
from project.plugins.telegram_trade_log import TelegramTradeLog
from project.plugins.file_dump import FileDump

modes = ('perpetual', 'copytrading')
load_dotenv('.env')
config = {}
if path.isfile('config.yaml'):
	config = load(open('config.yaml', 'r'), CLoader)
plugins = []

public_bybit = Bybit(testnet = False)
perpetual_market = MarketSync(public_bybit, market = Market())
copytrading_market = CopytradingMarketSync(public_bybit, market = Market())
test_bybit = Bybit(testnet = True)
test_perpetual_market = MarketSync(test_bybit, market = Market())
test_copytrading_market = CopytradingMarketSync(test_bybit, market = Market())
plugins += [perpetual_market, copytrading_market]
plugins += [test_perpetual_market, test_copytrading_market]

fast_binance_http = HTTPClient(
	proxies = config.get('fast_binance_http_proxies', []),
	timeout = config.get('fast_binance_timeout', 10)
)
slow_binance_http = HTTPClient(
	proxies = config.get('binance_http_proxies', []),
	timeout = config.get('binance_timeout', 10)
)
traders_watch = {uid: False for uid in config['telegram_log_traders']}
for account in config['accounts'].values():
	for mode in modes:
		if mode in account:
			traders_watch.update({uid: True for uid in account[mode]['traders']})
for uid, fast in traders_watch.items():
	traders_watch[uid] = BinanceTraderProfitableWatch(
		fast_binance_http if fast else slow_binance_http,
		trader = Trader(),
		meta = TraderMeta(uid),
		check_rate = len(traders_watch) * config.get('binance_check_rate', 1)
	)

bybit_accounts = {}
allowed_symbols = [Symbol(val) for val in config['traders_symbols']] \
	if 'traders_symbols' in config else None

for tag, account in config['accounts'].items():
	testnet = account.get('testnet', False)
	bybit = Bybit(
		testnet = testnet,
		key = environ[f'BYBIT_KEY_{tag}'],
		secret = environ[f'BYBIT_SECRET_{tag}'],
		http_proxy = config['bybit_http_proxies'][len(bybit_accounts)],
		ws_proxy = config['bybit_websocket_proxies'][len(bybit_accounts)]
	)
	bybit_accounts[tag] = {}

	for mode in ('perpetual', 'copytrading'):
		if mode in account:
			user = UserSync(bybit, user = User(0)) if mode == 'perpetual' \
				else CopytradingUserSync(bybit, user = User(0))
			bybit_accounts[tag][mode] = user
			plugins += [user]

			for uid, trader in account[mode]['traders'].items():
				watch = traders_watch[uid]

				copy = CopyTrade(
					bybit,
					market = test_perpetual_market.market if testnet \
						else perpetual_market.market,
					user = user.user,
					trader = watch.trader,
					trading_strategy = TradingStrategy(
						account[mode].get('leverage'),
						trader['deposit_portion'],
						trader.get('copy_amount_portion')
					),
					allowed_symbols = allowed_symbols
				) if mode == 'perpetual' else CopyCopytrade(
					bybit,
					market = test_copytrading_market.market if testnet \
						else copytrading_market.market,
					user = user.user,
					trader = watch.trader,
					trading_strategy = CopytradingStrategy(
						account[mode].get('leverage'),
						account[mode].get('per_order_margin', None),
						account[mode].get('per_order_margin_portion', 1),
						trader['deposit_portion'],
						trader.get('copy_amount_portion')
					),
					allowed_symbols = allowed_symbols
				)

				watch.events.position_updated += copy.copy_position
				plugins += [copy]

if 'telegram_log_chat' in config:
	telegram = Telegram(
		api_id = environ['TELEGRAM_ID'],
		api_hash = environ['TELEGRAM_HASH'],
		token = environ.get('TELEGRAM_TOKEN')
	)
	telegram_log = TelegramTradeLog(
		telegram,
		chat = config['telegram_log_chat']
	)
	for uid in config['telegram_log_traders']:
		watch = traders_watch[uid]
		watch.events.position_updated += \
			lambda p, t = watch.trader, m = watch.trader_meta: \
				telegram_log.log_position(p, t, m)
	plugins += [telegram_log]

plugins += [*traders_watch.values()]

for plugin in plugins:
	plugin.start_lifecycle()
print('=== STARTED ===')
for tag, bybit in bybit_accounts.items():
	if 'perpetual' in bybit:
		depo = bybit['perpetual'].user.deposit
		print(f'Perpetual balance of {tag}: {depo} USDT')
	if 'copytrading' in bybit:
		depo = bybit['copytrading'].user.deposit
		print(f'Copytrading balance of {tag}: {depo} USDT')

def soft_exit(*_):
	for plugin in plugins:
		try:
			plugin.stop_lifecycle()
		except Exception:
			print_exc()
	exit(0)
signal(SIGINT, soft_exit)
signal(SIGTERM, soft_exit)
new_event_loop().run_forever()