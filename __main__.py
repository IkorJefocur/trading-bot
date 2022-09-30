from os import environ, path
from asyncio import new_event_loop, gather
from json import load
from dotenv import load_dotenv
from project.services.flask_server import FlaskServer
from project.services.telegram import Telegram
from project.plugins.tradingview_server import TradingviewServer
from project.plugins.trade import Trade
from project.plugins.log import Log

load_dotenv('.env')
config = {}
for config_file in ('config.json', 'config.personal.json'):
	if path.isfile(config_file):
		config.update(load(open(config_file, 'r')))

tv = TradingviewServer(
	FlaskServer(
		name = __name__,
		local = config.get('local_server', False)
	)
)
trade = Trade(
	endpoint = 'https://api-testnet.bybit.com',
	key = environ['BYBIT_KEY'],
	secret = environ['BYBIT_SECRET']
)
log = Log(
	Telegram(
		api_id = environ['TELEGRAM_ID'],
		api_hash = environ['TELEGRAM_HASH']
	).login(
		bot_token = environ['TELEGRAM_TOKEN']
	),
	chats = config.get('telegram_chats', [])
)

async def candle_created(candle):
	await gather(trade.make_order(candle), log.send_candle(candle))
tv.events.candle_created += candle_created

for plugin in (tv, trade, log):
	plugin.start_lifecycle()
new_event_loop().run_forever()