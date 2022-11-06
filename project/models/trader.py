from .statistics import PositionStats, Performance

class TradingAccount:

	def __init__(self, deposit, positions = []):
		self.deposit = deposit
		self.opened_positions = {}
		for position in positions:
			self.update_position(position)

	def opened_position(self, matcher = None):
		if not matcher:
			return [*self.opened_positions.values()]
		return self.opened_positions.get(self.deal_category(matcher))

	def has_position(self, position):
		return position == self.opened_position(position)

	def update_position(self, position):
		category = self.deal_category(position)
		if position.closed:
			if category in self.opened_positions:
				del self.opened_positions[category]
		else:
			self.opened_positions[category] = position

	def deal_category(self, deal):
		return f"{'LONG' if deal.long else 'SHORT'}-{deal.symbol}"

class Trader(TradingAccount):

	def __init__(self, positions = [], performance = [], positions_stats = {}):
		self.all_periods_performance = {
			**{period: Performance(period) for period in Performance.periods},
			**{perf.period: perf for perf in performance}
		}
		self.positions_stats = {
			category: stats for category, stats in positions_stats.items()
		}
		super().__init__(0, positions)

	@property
	def deposit(self):
		return self.valuable_performance().current_profit.deposit
	@deposit.setter
	def deposit(self, value): pass

	def update_position(self, position):
		super().update_position(position)
		self.position_stats(position).last_position = position

	def performance(self, period = None):
		return self.all_periods_performance[period] if period \
			else self.all_periods_performance.values()

	def valuable_performance(self):
		return next(
			(perf for perf in self.performance() if perf.total_records > 0),
			next(self.performance())
		)

	def position_stats(self, position = None):
		if not position:
			return self.positions_stats.items()

		category = self.deal_category(position)
		if category not in self.positions_stats:
			self.positions_stats[category] = PositionStats()
		return self.positions_stats[category]

class User(TradingAccount):

	def __init__(self, deposit, positions = []):
		self.opened_orders = set()
		super().__init__(deposit, positions)

	def orders(self, matcher = None):
		category = self.deal_category(matcher) if matcher else None
		for order in self.opened_orders:
			if not category or self.deal_category(order) == category:
				yield order

	def has_order(self, order):
		return order in self.opened_orders

	def place_order(self, order):
		self.opened_orders.add(order)

	def close_order(self, order):
		self.opened_orders.remove(order)

	def update_position(self, position, with_order = False):
		super().update_position(position)
		if with_order:
			order = position.generate_order()
			self.add_order(order)
			return order