from datetime import timedelta, datetime
from flask import Flask, request, abort
from .order import Order

class Server:

	def __init__(
		self,
		local = False,
		allowed_ips = None,
		name = __name__,
		**flask_params
	):
		self.receivers = set()
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

	def add_receiver(self, receiver):
		self.receivers.add(receiver)

	def remove_receiver(self, reciever):
		self.recievers.remove(receiver)

	def run(self, *args, host = None, port = None, **kwargs):
		self.app.run(
			*args,
			host = host or (None if self.local else '0.0.0.0'),
			port = port or (3000 if self.local else 80),
			**kwargs
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
			for receiver in self.receivers:
				receiver(order)
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