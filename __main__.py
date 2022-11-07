from sys import exit
from os import environ, path, makedirs
from signal import signal, SIGINT, SIGTERM
from asyncio import new_event_loop
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

public_bybit = Bybit(testnet = config.get('bybit_testnet', False))
perpetual_market = MarketSync(public_bybit, market = Market())
copytrading_market = CopytradingMarketSync(public_bybit, market = Market())
plugins += [perpetual_market, copytrading_market]

http = HTTPClient(config.get('http_proxies', []))

traders_watch = {}
bybit_accounts = {}

for tag, account in config['accounts'].items():
	bybit = Bybit(
		testnet = account.get('testnet', False),
		key = environ[f'BYBIT_KEY_{tag}'],
		secret = environ[f'BYBIT_SECRET_{tag}'],
		http_proxy = config['http_proxies'][len(bybit_accounts)],
		ws_proxy = config['socks_proxies'][len(bybit_accounts)]
	)
	perpetual = UserSync(bybit, user = User(0))
	copytrading = CopytradingUserSync(bybit, user = User(0))
	bybit_accounts[tag] = {'perpetual': perpetual, 'copytrading': copytrading}
	plugins += [perpetual, copytrading]

	for uid, trader in account['traders'].items():
		if uid not in traders_watch:
			watch = BinanceTraderProfitableWatch(
				http,
				trader = file_dump.dump.follow(f'trader.{uid}') or Trader(),
				uid = uid
			)
			file_dump.dump.assoc(f'trader.{uid}', watch.trader)
			watch.events.trader_fetched += \
				lambda s = file_dump.save, t = watch.trader: s(t)
			traders_watch[uid] = watch
		watch = traders_watch[uid]

		copy = CopyTrade(
			bybit,
			market = perpetual_market.market,
			user = perpetual.user,
			trader = watch.trader,
			trading_strategy = TradingStrategy(
				account.get('leverage'),
				trader['deposit_portion'],
				trader.get('copy_amount_portion')
			),
			allowed_symbols = [Symbol(val) for val in config['traders_symbols']]
		)
		copytrade = CopyCopytrade(
			bybit,
			market = copytrading_market.market,
			user = copytrading.user,
			trader = watch.trader,
			trading_strategy = CopytradingStrategy(
				account.get('leverage'),
				account.get('per_order_margin', None),
				account.get('per_order_margin_portion', 1),
				trader['deposit_portion'],
				trader.get('copy_amount_portion')
			),
			allowed_symbols = [Symbol(val) for val in config['traders_symbols']]
		)
		watch.events.position_updated += copy.copy_position
		watch.events.position_updated += copytrade.copy_position

		plugins += [copy, copytrade]
plugins += [*traders_watch.values()]

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