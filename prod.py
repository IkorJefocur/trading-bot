from os import environ
from project import run, Server, Bot

class ParametrizedServer(Server):
	def run(self):
		super().run(host = '0.0.0.0', port = 80)

run(
	ParametrizedServer(),
	Bot(token = environ['TELEGRAM_TOKEN'], chats = ['-1001600368898'])
)