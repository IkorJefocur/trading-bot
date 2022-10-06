from os import environ, path, makedirs
from asyncio import new_event_loop
from json import load
from dotenv import load_dotenv
from project.models.trader import Trader
from project.services.http_client import HTTPClient
from project.services.flask_server import FlaskServer
from project.services.telegram import Telegram
from project.plugins.tradingview_server import TradingviewServer
from project.plugins.binance_traders_watch import BinanceTradersWatch
from project.plugins.trade import Trade
from project.plugins.file_manager import FileManager, TraderFormat
from project.plugins.log import Log

load_dotenv('.env')
config = {}
if path.isfile('config.json'):
	config = load(open('config.json', 'r'))

makedirs('db/traders', exist_ok = True)
trader_format = TraderFormat()
traders_dumps = {
	uid: FileManager(f'db/traders/{uid}.json', trader_format)
		for uid in config.get('traders')
}

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

tv = TradingviewServer(
	flask
)
traders = BinanceTradersWatch(
	HTTPClient(config.get('traders_proxies', [])),
	[
		traders_dumps[uid].load() or Trader(uid)
			for uid in config.get('traders', [])
	]
)
trade = Trade(
	endpoint = 'https://api-testnet.bybit.com',
	key = environ['BYBIT_KEY'],
	secret = environ['BYBIT_SECRET']
)
log = Log(
	telegram,
	chats = config.get('telegram_chats', [])
)

def dump_trader(_, trader):
	traders_dumps[trader.id].save(trader)
traders.events.performance_updated += dump_trader
traders.events.position_opened += dump_trader
traders.events.position_updated += dump_trader
traders.events.position_closed += dump_trader

tv.events.candle_created += trade.make_order
tv.events.candle_created += log.send_candle

for plugin in (tv, traders, trade, log):
	plugin.start_lifecycle()
new_event_loop().run_forever()