from math import floor
from itertools import chain
from .position import Order, ReflectivePosition

class Strategy:

	def __init__(self, leverage, depo_portion = 1, amount_portion = None):
		self.leverage = leverage
		self.deposit_portion = depo_portion
		self.copy_amount_portion = amount_portion

	def deposit_relative_reflection(self, base, trader, user):
		amount = base.amount * self.depo_portion * (
			self.copy_amount_portion if self.copy_amount_portion \
				else user.deposit / trader.deposit if trader.deposit > 0 \
				else 0
		)
		return ReflectivePosition(base.symbol, base.price, {trader: amount})

class TradingStrategy(Strategy):

	def copy_position(self, base, market, trader, user):
		head = user.opened_position(base)
		full = self.deposit_relative_reflection(base, trader, user).chain(head)

		for order in market.adjust_position(full):
			head = ReflectivePosition.add_order(head, order, trader)
			yield head

class CopytradingStrategy(Strategy):

	def __init__(
		self, leverage,
		margin_depo = None, margin_depo_portion = 1,
		depo_portion = 1, amount_portion = None
	):
		super().__init__(leverage, depo_portion, amount_portion)
		self.margin_deposit = margin_depo
		self.margin_deposit_portion = margin_depo_portion

	def copy_position(self, base, market, trader, user):
		head = user.opened_position(base)
		full = self.deposit_relative_reflection(base, trader, user).chain(head)

		if full.increased:
			margin = abs(full.amount_diff) * full.price / self.leverage
			margin_depo = (self.margin_deposit or user.deposit) \
				/ self.margin_deposit_portion
			orders_count = floor(margin / margin_depo)
			if orders_count == 0:
				return
			order_size = full.amount_diff / orders_count

			for index in range(orders_count):
				with_order = ReflectivePosition.add_order(head, Order(
					full.symbol, full.price, order_size
				), trader)
				for order in market.adjust_position(with_order):
					head = ReflectivePosition.add_order(head, order, trader)
					yield head, None

		else:
			profit = {
				order.profit(full.price).pnl: order \
					for order in user.opened_orders if order.long == full.long
			}
			orders = [profit[pnl] for pnl in chain(
				sorted(pnl for pnl in profit if pnl > 0),
				sorted(pnl for pnl in profit if pnl <= 0)
			)]

			while abs(head.amount) > abs(full.amount) and len(orders) > 0:
				order = orders.pop(0)
				head = ReflectivePosition \
					.add_order(head, order.compensate(), trader)
				yield head, order