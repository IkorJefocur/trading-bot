from telethon import TelegramClient
from ..base import Service

class Telegram(Service):

	def __init__(self, api_id, api_hash, token = None):
		super().__init__(None)
		self.target = TelegramClient(None, api_id, api_hash, loop = self.loop)
		self.token = token

	def start_lifecycle(self):
		if not self.target._authorized:
			self.loop.run_until_complete(self.login())
		super().start_lifecycle()

	def run(self):
		self.target.run_until_disconnected()

	def stop(self):
		self.run_task_sync(self.disconnect())

	async def login(self):
		await self.target.start(bot_token = self.token)

	async def disconnect(self):
		await self.target.disconnect()