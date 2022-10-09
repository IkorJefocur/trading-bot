from os import environ, path, makedirs
from asyncio import new_event_loop
from itertools import chain
from json import load
from dotenv import load_dotenv
from project.models.trader import Trader
from project.services.http_client import HTTPClient
from project.services.flask_server import FlaskServer
from project.services.telegram import Telegram
from project.services.bybit import Bybit
from project.plugins.tradingview_server import TradingviewServer
from project.plugins.binance_traders_watch import BinanceTradersWatch
from project.plugins.trade import Trade
from project.plugins.file_manager import FileManager, TraderFormat
from project.plugins.log import Log

load_dotenv('.env')
config = {}
if path.isfile('config.json'):
	config = load(open('config.json', 'r'))

traders_http = HTTPClient(config.get('traders_proxies', []))
flask = FlaskServer(
	name = __name__,
	local = config.get('local_server', False)
)
telegram = Telegram(
	api_id = environ['TELEGRAM_ID'],
	api_hash = environ['TELEGRAM_HASH']
).login(
	bot_token = environ.get('TELEGRAM_TOKEN')
)
bybit = Bybit(
	testnet = True,
	key = environ['BYBIT_KEY'],
	secret = environ['BYBIT_SECRET']
)

trade = Trade(
	bybit
)
log = Log(
	telegram,
	chats = config.get('telegram_chats', [])
)

tv = TradingviewServer(
	flask
)
tv.events.candle_created += trade.make_order
tv.events.candle_created += log.send_candle

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
	watch.events.trader_fetched += lambda: dump.save(watch.trader)
	return [dump, watch]
traders_watch = [*chain.from_iterable(
	make_trader_watch(uid) for uid in config.get('traders', [])
)]

for plugin in [trade, log, tv, *traders_watch]:
	plugin.start_lifecycle()
new_event_loop().run_forever()