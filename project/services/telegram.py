from telethon import TelegramClient
from ..base import Service

class Telegram(Service):

	def __init__(self, api_id, api_hash):
		super().__init__(TelegramClient(None, api_id, api_hash))

	def login(self, **params):
		async def async_login():
			await self.target.start(**params)
		self.loop.run_until_complete(async_login())
		return self

	def run(self):
		while True:
			self.target.run_until_disconnected()