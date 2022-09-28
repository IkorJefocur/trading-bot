from os import environ
from asyncio import new_event_loop, gather
from dotenv import load_dotenv
from project import \
	FlaskServer, Telegram, \
	TradingviewServer, Trade, OrderLog

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
log = OrderLog(
	Telegram(
		token = environ['TELEGRAM_TOKEN']
	),
	chats = environ['TELEGRAM_CHATS'].split(',')
)

async def order_added(order):
	await gather(trade.make_order(order), log.send(order))
tv.events.order_added += order_added

for plugin in (tv, trade, log):
	plugin.start_lifecycle()
new_event_loop().run_forever()