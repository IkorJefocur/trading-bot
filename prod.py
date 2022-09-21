from os import environ
from project import run, Server, Trade, Bot

class ParametrizedServer(Server):
	def run(self):
		super().run(host = '0.0.0.0', port = 80)

run(
	ParametrizedServer(),
	Trade(
		endpoint = 'https://api-testnet.bybit.com',
		key = environ['BYBIT_KEY'], secret = environ['BYBIT_SECRET']
	),
	Bot(token = environ['TELEGRAM_TOKEN'], chats = ['-1001600368898'])
)