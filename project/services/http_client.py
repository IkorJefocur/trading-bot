from random import randint
from aiohttp import ClientSession
from ..base import Service

class HTTPClient(Service):

	def __init__(self, proxies = []):
		super().__init__(None)
		self.proxies = proxies
		self.loop.run_until_complete(self.update_session())

	def __del__(self):
		self.loop.run_until_complete(self.target.close())

	def get_proxy(self):
		return self.proxies[randint(0, len(self.proxies) - 1)] \
			if len(self.proxies) > 0 else None

	async def update_session(self):
		self.target = await self.create_session()

	async def create_session(self):
		return ClientSession()