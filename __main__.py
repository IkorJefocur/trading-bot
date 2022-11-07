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
from project.plugins.user_sync import UserSync, CopytradingUserSync
from project.plugins.market_sync import MarketSync, CopytradingMarketSync
from project.plugins.copy_trade import CopyTrade, CopyCopytrade
from project.plugins.file_dump import FileDump

load_dotenv('.env')
config = {}
if path.isfile('config.json'):
	config = load(open('config.json', 'r'))
plugins = []

makedirs('db', exist_ok = True)
file_dump = FileDump(
	path = 'db/dump.json',
	readable = config.get('human_readable_dump', False)
)
file_dump.load()
plugins += [file_dump]

bybit = Bybit(testnet = config.get('bybit_testnet', False))
perpetual_market = MarketSync(bybit, market = Market())
copytrading_market = CopytradingMarketSync(bybit, market = Market())

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
		perpetual = UserSync(service, user = User(0))
		copytrading = CopytradingUserSync(service, user = User(0))
		bybit_accounts[tag] = {
			'service': service, 'perpetual': perpetual, 'copytrading': copytrading
		}
		plugins += [perpetual, copytrading]

traders_http = HTTPClient(config.get('http_proxies', []))

for uid, trader_config in config.get('traders', {}).items():
	watch = BinanceTraderProfitableWatch(
		traders_http,
		trader = file_dump.dump.follow(f'trader.{uid}') or Trader(),
		uid = uid
	)
	file_dump.dump.assoc(f'trader.{uid}', watch.trader)
	watch.events.trader_fetched += \
		lambda s = file_dump.save, t = watch.trader: s(t)

	for bybit in bybit_accounts.values():
		copy = CopyTrade(
			bybit['service'],
			market = perpetual_market.market,
			user = bybit['perpetual'].user,
			trader = watch.trader,
			trading_strategy = TradingStrategy(
				trader_config['deposit_portion'],
				trader_config.get('copy_amount_portion')
			),
			allowed_symbols = [Symbol(val) for val in config['traders_symbols']]
		)
		copytrade = CopyCopytrade(
			bybit['service'],
			market = copytrading_market.market,
			user = bybit['copytrading'].user,
			trader = watch.trader,
			trading_strategy = CopytradingStrategy(
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

	plugins += [watch]

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