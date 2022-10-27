from math import floor
from .position import ReflectivePosition

class Strategy:

	def __init__(self, leverage):
		self.leverage = leverage

	def deposit_relative_reflection(self, base, trader, user):
		amount = base.amount \
			* (user.deposit / trader.deposit if trader.deposit > 0 else 0)
		return ReflectivePosition(base.symbol, base.price, {trader: amount})

class TradingStrategy(Strategy):

	def copy_position(self, base, market, trader, user):
		head = user.opened_position(base)
		full = self.deposit_relative_reflection(base, trader, user).chain(head)

		for order in market.adjust_position(full):
			head = ReflectivePosition.add_order(head, order, trader)
			yield head