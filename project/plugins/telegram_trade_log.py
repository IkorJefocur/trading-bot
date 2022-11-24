from weakref import WeakKeyDictionary
from ..base import Plugin

class TelegramTradeLog(Plugin):

	def __init__(self, telegram_service, chat):
		super().__init__(telegram_service)
		self.messages = WeakKeyDictionary()

		self.chat_id = chat

	@Plugin.loop_bound
	async def log_position(self, position, trader, meta):
		message = await self.service.client.send_message(
			self.chat_id,
			self.format_position(position, trader, meta),
			reply_to = position.prev and self.messages.get(position.prev),
			link_preview = False
		)
		self.messages[position] = message.id

	def format_position(self, position, trader, meta):
		time_format = '%d-%m %H:%M:%S %Z'
		order = position.generate_order()

		return (
			f'[{meta.nickname}]({meta.binance_url}) ' + (
				'открыл позицию' if not position.prev
				else 'закрыл позицию' if position.closed
				else 'увеличил объем' if position.increased
				else 'уменьшил объем'
			) + '\n'
			+ ('LONG' if position.long else 'SHORT') +
			f' #{position.symbol} x{position.leverage}\n'
			f'Время открытия: {position.entry.time.strftime(time_format)}\n'
			+ (
				('Время закрытия' if position.closed else 'Время изменения') +
				f': {position.time.strftime(time_format)}\n'
					if position.prev else ''
			) + '\n'

			f'Цена открытия: {position.entry.price:g}\n'
			+ (
				('Цена закрытия' if position.closed else 'Цена изменения') +
				f': {position.price:g}\n'
					if position.prev else ''
			) + (
				f'Объем: {position.amount:g} {position.symbol.coin}' + (
					f' | {position.margin / trader.deposit * 100}% от депозита'
						if trader.deposit else ''
				) + '\n'
					if not position.closed else ''
			) + (
				f'Изменение объема: {order.amount:g} {position.symbol.coin} | '
				f'{order.amount / position.amount * 100}%' + (
					f' | {order.margin / trader.deposit * 100}% от депозита'
						if trader.deposit else ''
				) + '\n'
					if position.prev else ''
			) + '\n'

			f'Маржа: {position.margin:g}\n'
			f'PNL: {position.profit.pnl:g}\n'
			+ (
				f'Разница PNL: '
				f'{(position.profit.pnl - position.prev.profit.pnl):g}'
					if position.prev else ''
			) +
			f'ROE: {position.profit.roe}%'
		)