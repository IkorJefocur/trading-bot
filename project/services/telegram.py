from telethon import TelegramClient
from ..base import Service

class Telegram(Service):

	def __init__(self, api_id, api_hash):
		super().__init__(TelegramClient(None, api_id, api_hash))

	def login(self, **params):
		self.loop.run_until_complete(self.target.start(**params))
		return self

	def run(self):
		while True:
			self.target.run_until_disconnected()