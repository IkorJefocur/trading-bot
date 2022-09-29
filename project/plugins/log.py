from asyncio import gather
from ..base import Plugin

class Log(Plugin):

	def __init__(self, telegram_service, chats):
		super().__init__(telegram_service)
		self.chats = chats

	def send_candle(self, candle):
		return self.send(
			f"{'BUY' if candle.buy else 'SELL'}\n" \
			+ f"Coin - {candle.coin}\n" \
			+ f"Time - {candle.time.strftime('%d.%m.%Y %H:%M:%S %Z')}\n" \
			+ f"Close - {candle.close:g}\n" \
			+ f"Low - {candle.low:g}\n" \
			+ f"High - {candle.high:g}\n" \
			+ f"TF - {candle.timeframe}"
		)

	@Plugin.loop_bound
	async def send(self, message):
		bot = self.service.target
		await gather(*(
			bot.send_message(chat_id, message) for chat_id in self.chats
		))