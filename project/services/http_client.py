from asyncio import gather
from random import randint
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector
from ..base import Service

class HTTPClient(Service):

	def __init__(self, proxies = []):
		super().__init__()
		self.http_proxies = \
			[proxy for proxy in proxies if proxy.startswith('http')]
		self.socks_proxies = \
			[proxy for proxy in proxies if proxy.startswith('socks')]
		self.proxy_sessions = []

	@property
	def proxies_count(self):
		return len(self.socks_proxies) or len(self.http_proxies)

	def run(self):
		self.loop.run_until_complete(self.update_session())
		super().run()

	def stop(self):
		self.run_task_sync(self.close_session())
		super().stop()

	def get_session(self):
		return self.proxy_sessions[randint(0, len(self.proxy_sessions) - 1)] \
			if len(self.proxy_sessions) > 0 \
			else self.main_session

	def get_proxy(self):
		return self.http_proxies[randint(0, len(self.http_proxies) - 1)] \
			if len(self.http_proxies) > 0 else None

	async def update_session(self):
		self.main_session = ClientSession()
		self.proxy_sessions = [
			ClientSession(connector = ProxyConnector.from_url(url)) \
				for url in self.socks_proxies
		]

	async def close_session(self):
		await gather(
			self.main_session.close(),
			*(session.close() for session in self.proxy_sessions)
		)