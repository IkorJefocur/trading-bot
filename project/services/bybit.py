from concurrent.futures import ThreadPoolExecutor
from pybit import usdt_perpetual
from ..base import Service

class Bybit(Service):

	def __init__(self, key, secret, testnet = False):
		super().__init__(None)

		self.usdt_perpetual = usdt_perpetual.HTTP(
			endpoint = 'https://api-testnet.bybit.com' if testnet \
				else 'https://api.bybit.com',
			api_key = key,
			api_secret = secret
		)