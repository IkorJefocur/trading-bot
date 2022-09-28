from aiogram import executor, Dispatcher, Bot
from ..base import Service

class Telegram(Service):

	def __init__(self, token):
		super().__init__(Dispatcher(Bot(token = token)))

	def run(self):
		executor.start_polling(self.target)