from random import randint
from aiohttp import ClientSession
from ..base import Service

class HTTPClient(Service):

	def __init__(self, proxies = []):
		super().__init__(None)
		self.proxies = proxies

	def run(self):
		self.loop.run_until_complete(self.update_session())
		super().run()

	def stop(self):
		self.run_task_sync(self.target.close())
		super().stop()

	def get_proxy(self):
		return self.proxies[randint(0, len(self.proxies) - 1)] \
			if len(self.proxies) > 0 else None

	async def update_session(self):
		self.target = ClientSession()