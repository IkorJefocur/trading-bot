from os import environ
from asyncio import new_event_loop, gather
from dotenv import load_dotenv
from project import Server, Trade, Bot

load_dotenv('.env')
load_dotenv('.prod.env')

server = Server(
	local = True if 'LOCAL_SERVER' in environ else False
)
trade = Trade(
	endpoint = 'https://api-testnet.bybit.com',
	key = environ['BYBIT_KEY'],
	secret = environ['BYBIT_SECRET']
)
bot = Bot(
	token = environ['TELEGRAM_TOKEN'],
	chats = environ['TELEGRAM_CHATS'].split(',')
)

async def order_added(order):
	await gather(trade.make_order(order), bot.send(order))
server.events.order_added += order_added

for plugin in (server, trade, bot):
	plugin.start_lifecycle()
new_event_loop().run_forever()