from datetime import timedelta, datetime
from pybit import InvalidRequestError
from ..base import Plugin
from ..models.strategy import TradingStrategy, CopytradingStrategy

class CopyTrade(Plugin):

	def __init__(
		self, bybit_service, market, user, trader, trading_strategy,
		allowed_symbols = None
	):
		super().__init__(bybit_service)

		self.strategy = trading_strategy
		self.market = market
		self.user = user
		self.trader = trader
		self.allowed_symbols = allowed_symbols and {*allowed_symbols}

	async def copy_position(self, base):
		if self.market.coin(base.symbol) and self.filter_position(base):
			await self.set_leverage(base.symbol, base.leverage)
			await self.copy_position_strategy(base)

	@Plugin.loop_bound
	async def copy_position_strategy(self, base):
		positions = self.strategy.copy_position(
			base, self.market, self.trader, self.user
		)

		for position in positions:
			constraint = self.market.coin(position.symbol).constraint

			self.service.usdt_perpetual.place_active_order(
				symbol = position.symbol.value,
				side = 'Buy' if position.long == position.increased else 'Sell',
				order_type = 'Market',
				qty = abs(constraint.float_fix(position.amount_diff)),
				time_in_force = 'GoodTillCancel',
				reduce_only = not position.increased,
				close_on_trigger = False
			)
			self.user.update_position(position)

	@Plugin.loop_bound
	async def set_leverage(self, symbol, leverage):
		not_modified_code = 34036
		try:
			self.service.usdt_perpetual.set_leverage(
				symbol = symbol.value,
				buy_leverage = leverage,
				sell_leverage = leverage
			)
		except InvalidRequestError as error:
			if error.status_code != not_modified_code:
				raise

	def filter_position(self, position):
		return not self.allowed_symbols \
			or position.symbol in self.allowed_symbols

class CopyCopytrade(CopyTrade):

	orders = {}

	@Plugin.loop_bound
	async def copy_position_strategy(self, base):
		positions = self.strategy.copy_position(
			base, self.market, self.trader, self.user
		)

		for position, order_to_close in positions:
			constraint = self.market.coin(position.symbol).constraint

			if order_to_close:
				self.user.close_order(order_to_close)
				self.user.update_position(position)
				self.service.target.post(
					'/contract/v3/private/copytrading/order/close',
					symbol = order_to_close.symbol.value,
					parent_order_id = self.orders.pop(order_to_close)
				)

			else:
				order = position.generate_order()
				self.orders[order] = self.service.target.post(
					'/contract/v3/private/copytrading/order/create',
					side = 'Buy' if order.long else 'Sell',
					symbol = order.symbol.value,
					order_type = 'Market',
					qty = str(constraint.float_fix(abs(order.amount)))
				)['result']['orderId']
				self.user.place_order(order)
				self.user.update_position(position)

	@Plugin.loop_bound
	async def set_leverage(self, symbol, leverage):
		not_modified_code = 34036
		try:
			self.service.target.post(
				'/contract/v3/private/copytrading/position/set-leverage',
				symbol = symbol.value,
				buy_leverage = str(leverage),
				sell_leverage = str(leverage)
			)
		except InvalidRequestError as error:
			if error.status_code != not_modified_code:
				raise