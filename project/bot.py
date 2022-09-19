from asyncio import gather
from aiogram import Bot as TelegramBot, Dispatcher, executor

class Bot:

	def __init__(self, chats, **telegram_params):
		self.chats = chats

		self.dispatcher = Dispatcher(TelegramBot(**telegram_params))

	def format_message(self, data):
		return \
			f"{data['side']}\n" \
			+ f"Time - {data['time']}\n" \
			+ f"Coin - {data['coin']}\n" \
			+ f"Close - {data['close']}\n" \
			+ f"High - {data['high']}, Low - {data['low']}\n" \
			+ f"TF - {data['TF']}"

	async def send(self, data):
		bot = self.dispatcher.bot
		message = self.format_message(data)

		await gather(*(
			bot.send_message(chat_id, message) for chat_id in self.chats
		))

	def run(self, *args, **kwargs):
		executor.start_polling(self.dispatcher, *args, **kwargs)