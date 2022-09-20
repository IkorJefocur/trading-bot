from asyncio import gather
from aiogram import Bot as TelegramBot, Dispatcher, executor

class Bot:

	def __init__(self, chats, **telegram_params):
		self.chats = chats

		self.dispatcher = Dispatcher(TelegramBot(**telegram_params))

	def format_message(self, order):
		return \
			f"{'BUY' if order.buy else 'SELL'}\n" \
			+ f"Coin - {order.coin}\n" \
			+ f"Time - {order.time}\n" \
			+ f"Close - {order.close}\n" \
			+ f"Low - {order.low}\n" \
			+ f"High - {order.high}\n" \
			+ f"TF - {order.tf}"

	async def send(self, order):
		bot = self.dispatcher.bot
		message = self.format_message(order)

		await gather(*(
			bot.send_message(chat_id, message) for chat_id in self.chats
		))

	def run(self, *args, **kwargs):
		executor.start_polling(self.dispatcher, *args, **kwargs)