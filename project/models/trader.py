from .statistics import PositionStats, Performance

class TradingAccount:

	def __init__(self, deposit):
		self.deposit = deposit
		self.opened_positions = {}

	def opened_position(self, matcher = None):
		if not matcher:
			return [*self.opened_positions.values()]
		return self.opened_positions.get(self.position_category(matcher))

	def has_position(self, position):
		return position == self.opened_position(position)

	def update_position(self, position):
		category = self.position_category(position)
		if position.closed:
			if category in self.opened_positions:
				del self.opened_positions[category]
		else:
			self.opened_positions[category] = position

	def position_category(self, position):
		return f"{'LONG' if position.long else 'SHORT'}-{position.symbol.value}"

class Trader(TradingAccount):

	def __init__(self, performance = [], positions = {}):
		super().__init__(0)
		self.all_periods_performance = {
			**{period: Performance(period) for period in Performance.periods},
			**{perf.period: perf for perf in performance}
		}
		self.positions_stats = {
			category: stats for category, stats in positions.items()
		}

	@property
	def deposit(self):
		return self.valuable_performance().current_profit.deposit
	@deposit.setter
	def deposit(self, value): pass

	def add_position(self, position):
		position = super().add_position(position)
		self.position_stats(position).last_position = position
		return position

	def performance(self, period = None):
		return self.all_periods_performance[period] if period \
			else self.all_periods_performance.values()

	def valuable_performance(self):
		return next(
			(perf for perf in self.performance() if perf.total_records > 0),
			[*self.performance()][0]
		)

	def position_stats(self, position = None):
		if not position:
			return self.positions_stats.items()

		category = self.position_category(position)
		if category not in self.positions_stats:
			self.positions_stats[category] = PositionStats()
		return self.positions_stats[category]

class User(TradingAccount):
	pass