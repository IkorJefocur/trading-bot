from sys import exit
from os import environ, path, makedirs
from signal import signal, SIGINT, SIGTERM
from asyncio import new_event_loop
from itertools import chain
from json import load
from traceback import print_exc
from dotenv import load_dotenv
from project.models.position import Symbol
from project.models.market import Market
from project.models.trader import Trader, User
from project.models.strategy import TradingStrategy, CopytradingStrategy
from project.services.http_client import HTTPClient
from project.services.bybit import Bybit
from project.plugins.binance_trader_watch import BinanceTraderProfitableWatch
from project.plugins.bybit_watch import BybitWatch, BybitCopytradingWatch
from project.plugins.copy_trade import CopyTrade, CopyCopytrade
from project.plugins.file_manager import FileManager, TraderFormat

load_dotenv('.env')
config = {}
if path.isfile('config.json'):
	config = load(open('config.json', 'r'))
plugins = []

bybit_accounts = {}
for env in environ:
	tag = env.replace('BYBIT_KEY_', '', 1)
	if env.startswith('BYBIT_KEY_') and f'BYBIT_SECRET_{tag}' in environ:
		service = Bybit(
			testnet = config.get('bybit_testnet', False),
			key = environ[env],
			secret = environ[f'BYBIT_SECRET_{tag}'],
			http_proxy = config['http_proxies'][len(bybit_accounts)],
			ws_proxy = config['socks_proxies'][len(bybit_accounts)]
		)
		perpetual = BybitWatch(
			service,
			market = Market(),
			user = User(0)
		)
		copytrading = BybitCopytradingWatch(
			service,
			market = Market(),
			user = User(0)
		)
		bybit_accounts[tag] = {
			'service': service, 'perpetual': perpetual, 'copytrading': copytrading
		}
		plugins += [perpetual, copytrading]

traders_http = HTTPClient(config.get('http_proxies', []))
makedirs('db/traders', exist_ok = True)
trader_format = TraderFormat()

for uid, trader_config in config.get('traders', {}).items():
	dump = FileManager(
		path = f'db/traders/{uid}.json',
		formatter = trader_format
	)
	watch = BinanceTraderProfitableWatch(
		traders_http,
		trader = dump.load() or Trader(),
		uid = uid
	)
	watch.events.trader_fetched += lambda s = dump.save, t = watch.trader: s(t)

	for bybit in bybit_accounts.values():
		copy = CopyTrade(
			bybit['service'],
			market = bybit['perpetual'].market,
			user = bybit['perpetual'].user,
			trader = watch.trader,
			trading_strategy = TradingStrategy(
				config['leverage'],
				trader_config['deposit_portion'],
				trader_config.get('copy_amount_portion')
			),
			allowed_symbols = [Symbol(val) for val in config['traders_symbols']]
		)
		copytrade = CopyCopytrade(
			bybit['service'],
			market = bybit['copytrading'].market,
			user = bybit['copytrading'].user,
			trader = watch.trader,
			trading_strategy = CopytradingStrategy(
				config['leverage'],
				config.get('per_order_margin', None),
				config.get('per_order_margin_portion', 1),
				trader_config['deposit_portion'],
				trader_config.get('copy_amount_portion')
			),
			allowed_symbols = [Symbol(val) for val in config['traders_symbols']]
		)
		watch.events.position_updated += copy.copy_position
		watch.events.position_updated += copytrade.copy_position
		plugins += [copy, copytrade]

	plugins += [dump, watch]

for plugin in plugins:
	plugin.start_lifecycle()
print('=== STARTED ===')
for tag, bybit in bybit_accounts.items():
	perpetual_depo = bybit['perpetual'].user.deposit
	copytrading_depo = bybit['copytrading'].user.deposit
	print(f'Perpetual balance of {tag}: {perpetual_depo} USDT')
	print(f'Copytrading balance of {tag}: {copytrading_depo} USDT')

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