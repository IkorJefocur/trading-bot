from events import Events
from pybit import usdt_perpetual
from ..base import Service

class Bybit(Service):

	def __init__(self, key, secret, testnet = False):
		super().__init__(None)

		endpoint = 'https://api-testnet.bybit.com' if testnet \
			else 'https://api.bybit.com'
		auth = {'api_key': key, 'api_secret': secret}

		self.usdt_perpetual = usdt_perpetual.HTTP(
			endpoint = endpoint, **auth
		)
		self.usdt_perpetual_ws = WebSocketProxy(usdt_perpetual.WebSocket(
			test = testnet, **auth
		))

class WebSocketProxy:

	def __init__(self, original):
		self.original = original

	def __getattr__(self, key):
		topic = getattr(self.original, key, None)
		if not callable(topic):
			raise AttributeError(f'WebSocket has no topic {key}')
		proxy = WebSocketTopic(topic)
		setattr(self, key, proxy)
		return proxy

class WebSocketTopic:

	kwd_mark = object()

	def __init__(self, original):
		self.original = original
		self.handlers = {}

	def __call__(self, handler, *args, **kwargs):
		key = args + (self.kwd_mark,) + tuple(sorted(kwargs.items()))
		if key not in self.handlers:
			self.handlers[key] = Events('packet')
			self.original(self.handlers[key].packet, *args, **kwargs)
		self.handlers[key].packet += handler