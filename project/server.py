from flask import Flask, request, abort

class Server:

	def __init__(
		self,
		allowed_ips = [
			'52.89.214.238',
			'34.212.75.30',
			'54.218.53.128',
			'52.32.178.7'
		],
		name = __name__,
		**flask_params
	):
		self.receivers = set()
		self.allowed_ips = allowed_ips

		self.app = Flask(name, **flask_params)
		self.app.route('/', methods=['POST'])(self.handle_webhook)

	def add_receiver(self, receiver):
		self.receivers.add(receiver)

	def remove_receiver(self, reciever):
		self.recievers.remove(receiver)

	def run(self, *args, **kwargs):
		self.app.run(*args, **kwargs)

	def handle_webhook(self):
		if request.remote_addr not in self.allowed_ips:
			abort(403)
		if not request.is_json:
			abort(400)

		data = request.json
		for receiver in self.receivers:
			receiver(data)

		return '', 204