from datetime import timedelta, datetime
from pybit import InvalidRequestError
from ..base import Plugin
from ..models.strategy import TradingStrategy

class CopyTrade(Plugin):

	def __init__(
		self, bybit_service, market, user, trader, allowed_symbols = None
	):
		super().__init__(bybit_service)
		self.strategy = TradingStrategy(5)
		self.leverage_updates = {}

		self.market = market
		self.user = user
		self.trader = trader
		self.allowed_symbols = allowed_symbols and {*allowed_symbols}

	@Plugin.loop_bound
	async def copy_position(self, base):
		if not self.filter_position(base):
			return
		positions = self.strategy.copy_position(
			base, self.market, self.trader, self.user
		)

		for position in positions:
			self.set_leverage(position.symbol)

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

	def set_leverage(self, symbol):
		if (
			symbol.value in self.leverage_updates
			and datetime.now() < \
				self.leverage_updates[symbol.value] + timedelta(minutes = 1)
		):
			return

		not_modified_code = 34036
		try:
			self.service.usdt_perpetual.set_leverage(
				symbol = symbol.value,
				buy_leverage = self.strategy.leverage,
				sell_leverage = self.strategy.leverage
			)
		except InvalidRequestError as error:
			if error.status_code != not_modified_code:
				raise

		self.leverage_updates[symbol.value] = datetime.now()

	def filter_position(self, position):
		return not self.allowed_symbols \
			or position.symbol.value in self.allowed_symbols