from datetime import timedelta, date
from .position import Profit, TradingAccount

class PositionStats:

	def __init__(
		self, last_position = None,
		min_pnl_profit = None, max_pnl_profit = None,
		min_roe_profit = None, max_roe_profit = None
	):
		self.last_position_val = last_position

		self.min_pnl_profit = min_pnl_profit or Profit(0, float('inf'))
		self.max_pnl_profit = max_pnl_profit or Profit(0, float('-inf'))
		self.min_roe_profit = min_roe_profit or Profit(float('inf'), 0)
		self.max_roe_profit = max_roe_profit or Profit(float('-inf'), 0)

	@property
	def last_position(self):
		return self.last_position_val

	@last_position.setter
	def last_position(self, value):
		self.last_position_val = value
		if not value:
			return None

		if value.profit.pnl < self.min_pnl_profit.pnl:
			self.min_pnl_profit = value.profit
		if value.profit.pnl > self.max_pnl_profit.pnl:
			self.max_pnl_profit = value.profit
		if value.profit.roe < self.min_roe_profit.roe:
			self.min_roe_profit = value.profit
		if value.profit.roe > self.max_roe_profit.roe:
			self.max_roe_profit = value.profit

class Performance:

	periods = {
		'all': None,
		'daily': timedelta(days = 1),
		'weekly': timedelta(days = 7),
		'monthly': timedelta(days = 30),
		'yearly': timedelta(days = 365)
	}

	def __init__(
		self, period,
		current_date = None, total_records = 0,
		current_profit = None,
		min_deposit_profit = None,
		max_deposit_profit = None,
		average_deposit = 0
	):
		self.period = period

		self.current_date = current_date or date.fromtimestamp(0)
		self.total_records = total_records

		self.current_profit_val = current_profit or Profit(0, 0)
		self.min_deposit_profit = min_deposit_profit or Profit(1, float('inf'))
		self.max_deposit_profit = max_deposit_profit or Profit(0, float('-inf'))
		self.average_deposit = average_deposit

	@property
	def timedelta(self):
		return self.periods[self.period]

	@property
	def current_profit(self):
		return self.current_profit_val
	@current_profit.setter
	def current_profit(self, value):
		day = date.today()

		if day >= self.current_date:
			self.current_profit_val = value
		self.current_date = day
		self.total_records += 1

		if value.deposit < self.min_deposit_profit.deposit:
			self.min_deposit_profit = value
		if value.deposit > self.max_deposit_profit.deposit:
			self.max_deposit_profit = value
		self.average_deposit += \
			(value.deposit - self.average_deposit) / self.total_records

class Trader(TradingAccount):

	def __init__(self, uid, performance = [], positions = {}):
		self.id = uid
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