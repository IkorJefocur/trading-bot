from ..base import Plugin

class CopyTrade(Plugin):

	def __init__(self, bybit_service, user, trader, allowed_symbols = None):
		super().__init__(bybit_service)
		self.user = user
		self.trader = trader
		self.allowed_symbols = allowed_symbols and {*allowed_symbols}

	@Plugin.loop_bound
	async def copy_position(self, base):
		if not self.filter_position(base):
			return
		position = self.user.add_position(self.user.copy_position(
			base, self.trader
		))

		self.service.usdt_perpetual.place_active_order(
			symbol = position.symbol.value,
			side = 'Buy' if position.long == position.increased else 'Sell',
			order_type = 'Market',
			qty = abs(position.amount_diff),
			time_in_force = 'GoodTillCancel',
			reduce_only = not position.increased,
			close_on_trigger = False
		)

	def filter_position(self, position):
		return not self.allowed_symbols \
			or position.symbol.value in self.allowed_symbols