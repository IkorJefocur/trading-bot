import re
from events import Events
from pybit import usdt_perpetual, _http_manager, _websocket_stream
from ..base import Service

class Bybit(Service):

	@staticmethod
	def ws_proxy_params(proxy_str):
		match = re.match(r"""^
			(http|socks4|socks4a|socks5|socks5h)://
			((\w+):(\w+)@)?
			([\d.]+):(\d+)
		$""", proxy_str, re.X)
		return {
			'proxy_type': match[1],
			'http_proxy_auth': (match[3], match[4]) if match[2] else None,
			'http_proxy_host': match[5],
			'http_proxy_port': match[6]
		} if match else {}

	def __init__(
		self, key = None, secret = None, testnet = False,
		http_proxy = '', ws_proxy = ''
	):
		super().__init__()

		http_params = {
			'endpoint': 'https://api-testnet.bybit.com' if testnet \
				else 'https://api.bybit.com',
			'api_key': key, 'api_secret': secret,
			'proxies': {'https': http_proxy} if http_proxy else {}
		}
		ws_params = {
			'test': testnet,
			'api_key': key, 'api_secret': secret,
			**self.ws_proxy_params(ws_proxy)
		}

		self.http = HTTP(**http_params)
		self.ws_public = WebSocketProxy(WebSocket(**ws_params))
		self.ws_private = WebSocketProxy(WebSocket(True, **ws_params))
		self.usdt_perpetual = usdt_perpetual.HTTP(**http_params)
		self.usdt_perpetual_ws = \
			WebSocketProxy(usdt_perpetual.WebSocket(**ws_params))

class HTTP(_http_manager._HTTPManager):

	def request(self, method = None, path = None, **query):
		return self._submit_request(
			method = method,
			path = f'{self.endpoint}{path}',
			auth = 'private' in path,
			query = query
		)

	def get(self, path = None, **query):
		return self.request('GET', path, **query)

	def post(self, path = None, **query):
		return self.request('POST', path, **query)

class WebSocket(_websocket_stream._FuturesWebSocketManager):

	def __init__(self, private = False, **kwargs):
		super().__init__('ANY', **kwargs)
		self.private = private
		self.private_topics = set()

	def subscribe(self, topic, callback, symbol = None):
		if self.private:
			self.private_topics.add(topic)
		if not self.is_connected() and not self.attempting_connection:
			self._connect(
				'wss://{SUBDOMAIN}.{DOMAIN}.com/realtime_private' \
					if self.private \
					else 'wss://{SUBDOMAIN}.{DOMAIN}.com/realtime_public'
			)
		super().subscribe(topic, callback, symbol)

class WebSocketProxy:

	def __init__(self, original):
		self.original = original
		self.topics = {}

	def __getattr__(self, key):
		topic = getattr(self.original, key, None)
		if not callable(topic):
			raise AttributeError(f'WebSocket has no topic {key}')
		proxy = WebSocketTopic(topic)
		setattr(self, key, proxy)
		return proxy

	def subscribe(self, topic, *args, **kwargs):
		if not topic in self.topics:
			topic_fn = lambda *args: self.original.subscribe(topic, *args)
			self.topics[topic] = WebSocketTopic(topic_fn)
		self.topics[topic](*args, **kwargs)

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