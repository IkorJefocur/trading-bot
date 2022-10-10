from ..base import Plugin

class CopyTrade(Plugin):

	def __init__(self, bybit_service, trader, allowed_symbols = None):
		super().__init__(bybit_service)
		self.trader = trader
		self.allowed_symbols = allowed_symbols and {*allowed_symbols}

	@Plugin.loop_bound
	async def copy_position(self, position):
		if not self.filter_position(position):
			return
		self.service.usdt_perpetual.place_active_order(
			symbol = position.symbol.value,
			side = 'Buy' if position.long == position.increased else 'Sell',
			order_type = 'Market',
			qty = await self.relative_quantity(position),
			time_in_force = 'GoodTillCancel',
			reduce_only = not position.increased,
			close_on_trigger = False
		)

	@Plugin.loop_bound
	async def relative_quantity(self, position):
		limits = next(
			symbol_stats['lot_size_filter'] for symbol_stats
				in self.service.usdt_perpetual.query_symbol()['result']
				if symbol_stats['name'] == position.symbol.value
		)
		qty = abs(position.amount_diff) * await self.deposit_ratio()
		qty = min(max(qty, limits['min_trading_qty']), limits['max_trading_qty'])
		return round(qty / limits['qty_step']) * limits['qty_step']

	@Plugin.loop_bound
	async def deposit_ratio(self):
		deposit = self.service.usdt_perpetual.get_wallet_balance(
			coin = 'USDT'
		)['result']['USDT']['wallet_balance']
		return deposit / self.trader.deposit if self.trader.deposit > 0 else 0

	def filter_position(self, position):
		return not self.allowed_symbols \
			or position.symbol.value in self.allowed_symbols