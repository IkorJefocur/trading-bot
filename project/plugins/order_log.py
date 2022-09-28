from asyncio import gather
from ..base import Plugin

class OrderLog(Plugin):

	def __init__(self, telegram_service, chats):
		super().__init__(telegram_service)
		self.chats = chats

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
		bot = self.service.target.bot
		message = self.format_message(order)

		await gather(*(
			bot.send_message(chat_id, message) for chat_id in self.chats
		))