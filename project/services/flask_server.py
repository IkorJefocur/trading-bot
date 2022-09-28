from threading import Thread
from flask import Flask
from ..base import Service

class FlaskServer(Service):

	def __init__(self, name, local = False):
		super().__init__(Flask(name))
		self.local = local

	def start_lifecycle(self):
		super().start_lifecycle()
		Thread(target = self.run_server).start()

	def run_server(self):
		self.target.run(
			host = None if self.local else '0.0.0.0',
			port = 3000 if self.local else 80,
			load_dotenv = False
		)