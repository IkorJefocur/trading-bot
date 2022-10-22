from .position import ReflectivePosition

class TradingStrategy:

	def copy_position(self, base, market, trader, user):
		amount = base.amount \
			* (user.deposit / trader.deposit if trader.deposit > 0 else 0)

		head = user.opened_position(base)
		full = ReflectivePosition(
			base.symbol, base.price, {trader: amount}, base.profit
		).chain(head)
		trader_part = amount - full.amount_diff
		
		for source in market.adjust_position(full):
			trader_part += source.amount_diff
			head = ReflectivePosition(
				source.symbol, source.price, {trader: trader_part}, source.profit
			).chain(head)
			yield head