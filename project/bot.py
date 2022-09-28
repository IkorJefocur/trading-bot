from asyncio import gather
from aiogram import Bot as TelegramBot, Dispatcher, executor
from .base import Plugin

class Bot(Plugin):

	def __init__(self, chats, **telegram_params):
		super().__init__()
		self.chats = chats

		self.dispatcher = Dispatcher(TelegramBot(**telegram_params))

	def format_message(self, order):
		return \
			f"{'BUY' if order.buy else 'SELL'}\n" \
			+ f"Coin - {order.coin}\n" \
			+ f"Time - {order.time.strftime('%d.%m.%Y %H:%M:%S %Z')}\n" \
			+ f"Close - {order.close:g}\n" \
			+ f"Low - {order.low:g}\n" \
			+ f"High - {order.high:g}\n" \
			+ f"TF - {order.tf}"

	@Plugin.loop_bound
	async def send(self, order):
		bot = self.dispatcher.bot
		message = self.format_message(order)

		await gather(*(
			bot.send_message(chat_id, message) for chat_id in self.chats
		))

	def run(self, *args, **kwargs):
		executor.start_polling(self.dispatcher, *args, **kwargs)