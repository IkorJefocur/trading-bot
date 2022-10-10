from os import environ, path, makedirs
from asyncio import new_event_loop
from itertools import chain
from json import load
from dotenv import load_dotenv
from project.models.trader import Trader
from project.services.http_client import HTTPClient
from project.services.bybit import Bybit
from project.plugins.binance_traders_watch import BinanceTradersWatch
from project.plugins.copy_trade import CopyTrade
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
def make_trader_watch(uid):
	dump = FileManager(
		path = f'db/traders/{uid}.json',
		formatter = trader_format
	)
	watch = BinanceTradersWatch(
		traders_http,
		trader = dump.load() or Trader(uid)
	)
	copy = CopyTrade(
		bybit,
		trader = watch.trader,
		allowed_symbols = config.get('traders_symbols')
	)
	watch.events.trader_fetched += lambda: dump.save(watch.trader)
	watch.events.position_updated += copy.copy_position
	return [dump, watch, copy]
traders_watch = [*chain.from_iterable(
	make_trader_watch(uid) for uid in config.get('traders', [])
)]

for plugin in [*traders_watch]:
	plugin.start_lifecycle()
print('=== STARTED ===')
new_event_loop().run_forever()