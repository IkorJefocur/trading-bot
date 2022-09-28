from datetime import timedelta, datetime
from threading import Thread
from flask import Flask, request, abort
from events import Events
from .base import Plugin
from .order import Order

class Server(Plugin):

	def __init__(
		self,
		local = False,
		allowed_ips = None,
		name = __name__,
		**flask_params
	):
		super().__init__()
		self.events = Events(('order_added'), loop = self.loop)
		self.local = local

		self.allowed_ips = allowed_ips or ([
			'127.0.0.1'
		] if local else [
			'52.89.214.238',
			'34.212.75.30',
			'54.218.53.128',
			'52.32.178.7'
		])

		self.app = Flask(name, **flask_params)
		self.app.route('/', methods=['POST'])(self.handle_webhook)

	def start_lifecycle(self):
		super().start_lifecycle()
		Thread(target = self.run_server).start()

	def run_server(self):
		self.app.run(
			host = None if self.local else '0.0.0.0',
			port = 3000 if self.local else 80,
			load_dotenv = False
		)

	def handle_webhook(self):
		if request.remote_addr not in self.allowed_ips:
			abort(403)
		if not request.is_json:
			abort(400)

		try:
			order = self.parse_order(request.json)
		except TypeError:
			abort(400)

		else:
			self.events.order_added(order)
			return '', 204

	def parse_order(self, data):
		try:
			side = data['side'].lower()
			coin = data['coin']
			time = datetime.fromisoformat(data['time'].replace('Z', '+00:00'))
			close = float(data['close'])
			low = float(data['low'])
			high = float(data['high'])
			tf = timedelta(minutes = int(data['TF']))

			if not (
				(side == 'buy' or side == 'sell')
				and type(coin) == str
				and close > 0
				and low > 0
				and high > 0
				and tf > timedelta()
			):
				raise Exception()

			return Order(side, coin, time, close, low, high, tf)

		except Exception as e:
			raise TypeError('Incorrect order json')