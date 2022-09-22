from os import environ
from dotenv import load_dotenv
from project import run, Server, Trade, Bot

load_dotenv()

run(
	Server(local = True),
	Trade(
		endpoint = 'https://api-testnet.bybit.com',
		key = environ['BYBIT_KEY'], secret = environ['BYBIT_SECRET']
	),
	Bot(
		token = environ['TELEGRAM_TOKEN'],
		chats = environ['TELEGRAM_CHATS'].split(',')
	)
)