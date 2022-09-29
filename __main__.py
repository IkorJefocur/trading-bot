from os import environ
from asyncio import new_event_loop, gather
from dotenv import load_dotenv
from project import \
	FlaskServer, Telegram, \
	TradingviewServer, Trade, Log

load_dotenv('.env')
load_dotenv('.prod.env')

tv = TradingviewServer(
	FlaskServer(
		name = __name__,
		local = True if 'LOCAL_SERVER' in environ else False
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
	chats = [int(chat_id) for chat_id in environ['TELEGRAM_CHATS'].split(',')]
)

async def candle_created(candle):
	await gather(trade.make_order(candle), log.send_candle(candle))
tv.events.candle_created += candle_created

for plugin in (tv, trade, log):
	plugin.start_lifecycle()
new_event_loop().run_forever()