from concurrent.futures import ThreadPoolExecutor
from pybit import usdt_perpetual
from ..base import Service

class Bybit(Service):

	def __init__(self, endpoint, key, secret):
		super().__init__(None)
		self.executor = ThreadPoolExecutor()

		self.usdt_perpetual = usdt_perpetual.HTTP(
			endpoint = endpoint,
			api_key = key,
			api_secret = secret
		)

	def send_sync_task(self, fn):
		return self.loop.run_in_executor(fn(), self.executor)