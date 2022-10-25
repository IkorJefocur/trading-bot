from math import floor
from .position import ReflectivePosition

class Strategy:

	def __init__(self, leverage):
		self.leverage = leverage

	def deposit_relative_amount(self, position, trader, user):
		return base.amount \
			* (user.deposit / trader.deposit if trader.deposit > 0 else 0)

	def adjust_reflection(self, full, trader, market):
		head = full.prev
		trader_part = full.amount - full.part_diff(trader)

		for source in market.adjust_position(full):
			trader_part += source.amount_diff
			head = ReflectivePosition(
				source.symbol, source.price, {trader: trader_part}, source.profit
			).chain(head)
			yield head

class TradingStrategy(Strategy):

	def copy_position(self, base, market, trader, user):
		amount = self.deposit_relative_amount(base, trader, user)

		position = ReflectivePosition(
			base.symbol, base.price, {trader: amount}, base.profit
		).chain(user.opened_position(base))
		yield from self.adjust_reflection(position, trader, market)