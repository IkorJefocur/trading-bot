from os import environ
from project import run, Server, Trade, Bot

run(
	Server(),
	Trade(
		endpoint = 'https://api-testnet.bybit.com',
		key = environ['BYBIT_KEY'], secret = environ['BYBIT_SECRET']
	),
	Bot(token = environ['TELEGRAM_TOKEN'], chats = ['-1001600368898'])
)