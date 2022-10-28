from os import environ, path, makedirs
from asyncio import new_event_loop
from itertools import chain
from json import load
from dotenv import load_dotenv
from project.models.market import Market
from project.models.trader import Trader, User
from project.models.strategy import CopytradingStrategy
from project.services.http_client import HTTPClient
from project.services.bybit import Bybit
from project.plugins.binance_traders_watch import BinanceTradersWatch
from project.plugins.bybit_watch import BybitCopytradingWatch
from project.plugins.copy_trade import CopyCopytrade
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
bybit_watch = BybitCopytradingWatch(
	bybit,
	market = Market(),
	user = User(0)
)
def make_trader_watch(uid):
	dump = FileManager(
		path = f'db/traders/{uid}.json',
		formatter = trader_format
	)
	watch = BinanceTradersWatch(
		traders_http,
		trader = dump.load() or Trader(),
		uid = uid
	)
	copy = CopyCopytrade(
		bybit,
		market = bybit_watch.market,
		user = bybit_watch.user,
		trader = watch.trader,
		trading_strategy = CopytradingStrategy(
			config['leverage'],
			config['deposit_portion']
		),
		allowed_symbols = config.get('traders_symbols')
	)
	watch.events.trader_fetched += lambda: dump.save(watch.trader)
	watch.events.position_updated += copy.copy_position
	return [dump, copy, watch]
traders_logic = [*chain.from_iterable(
	make_trader_watch(uid) for uid in config.get('traders', [])
)]

for plugin in [bybit_watch, *traders_logic]:
	plugin.start_lifecycle()
print('=== STARTED ===')
print(f'Balance: {bybit_watch.user.deposit} USDT')
new_event_loop().run_forever()