from os import environ, path
from asyncio import new_event_loop
from json import load
from dotenv import load_dotenv
from project.services.flask_server import FlaskServer
from project.services.telegram import Telegram
from project.plugins.tradingview_server import TradingviewServer
from project.plugins.traders_watch import TradersWatch
from project.plugins.trade import Trade
from project.plugins.log import Log
from project.models.trader import Trader, Profit

load_dotenv('.env')
config = {}
if path.isfile('config.json'):
	config = load(open('config.json', 'r'))

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
traders = TradersWatch(
	telegram,
	traders = [Trader(
		uid,
		{days: Profit(
			profit['roe'] / 100,
			profit['pnl']
		) for days, profit in performance.items()}
	) for uid, performance in config.get('traders', {}).items()]
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

tv.events.candle_created += trade.make_order
tv.events.candle_created += log.send_candle
traders.events.order_made += print

for plugin in (tv, traders, trade, log):
	plugin.start_lifecycle()
new_event_loop().run_forever()