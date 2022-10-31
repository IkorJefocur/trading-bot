from os import environ, path, makedirs
from asyncio import new_event_loop
from itertools import chain
from json import load
from dotenv import load_dotenv
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

traders_http = HTTPClient(config.get('traders_proxies', []))
bybit = Bybit(
	testnet = config.get('bybit_testnet', False),
	key = environ['BYBIT_KEY'],
	secret = environ['BYBIT_SECRET']
)

makedirs('db/traders', exist_ok = True)
trader_format = TraderFormat()
bybit_watch = BybitWatch(
	bybit,
	market = Market(),
	user = User(0)
)
bybit_copytrading_watch = BybitCopytradingWatch(
	bybit,
	market = Market(),
	user = User(0)
)

def make_trader_watch(uid, depo):
	dump = FileManager(
		path = f'db/traders/{uid}.json',
		formatter = trader_format
	)
	watch = BinanceTraderProfitableWatch(
		traders_http,
		trader = dump.load() or Trader(),
		uid = uid
	)
	copy = CopyTrade(
		bybit,
		market = bybit_watch.market,
		user = bybit_watch.user,
		trader = watch.trader,
		trading_strategy = TradingStrategy(
			config['leverage'],
			depo,
			config.get('copy_amount_portion')
		),
		allowed_symbols = config.get('traders_symbols')
	)
	copytrade = CopyCopytrade(
		bybit,
		market = bybit_copytrading_watch.market,
		user = bybit_copytrading_watch.user,
		trader = watch.trader,
		trading_strategy = CopytradingStrategy(
			config['leverage'],
			config.get('margin_deposit', None),
			config.get('margin_deposit_portion', 1),
			depo,
			config.get('copy_amount_portion')
		),
		allowed_symbols = config.get('traders_symbols')
	)

	watch.events.trader_fetched += lambda: dump.save(watch.trader)
	watch.events.position_updated += copy.copy_position
	watch.events.position_updated += copytrade.copy_position
	return [dump, copy, copytrade, watch]
traders_logic = [*chain.from_iterable(
	make_trader_watch(uid, depo) for uid, depo \
		in config.get('traders', {}).items()
)]

for plugin in [bybit_watch, bybit_copytrading_watch, *traders_logic]:
	plugin.start_lifecycle()
print('=== STARTED ===')
print(f'Perpetual balance: {bybit_watch.user.deposit} USDT')
print(f'Copytrading balance: {bybit_copytrading_watch.user.deposit} USDT')
new_event_loop().run_forever()