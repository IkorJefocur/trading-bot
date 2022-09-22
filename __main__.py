from os import environ
from dotenv import load_dotenv
from project import run, Server, Trade, Bot

load_dotenv('.env')
load_dotenv('.prod.env')

run(
	Server(
		local = True if 'LOCAL_SERVER' in environ else False
	),
	Trade(
		endpoint = 'https://api-testnet.bybit.com',
		key = environ['BYBIT_KEY'],
		secret = environ['BYBIT_SECRET']
	),
	Bot(
		token = environ['TELEGRAM_TOKEN'],
		chats = environ['TELEGRAM_CHATS'].split(',')
	)
)