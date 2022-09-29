from telethon import TelegramClient
from ..base import Service

class Telegram(Service):

	def __init__(self, api_id, api_hash, token = None):
		super().__init__(TelegramClient(None, api_id, api_hash))
		self.token = token

	def run(self):
		self.target.start(bot_token = self.token)
		super().run()