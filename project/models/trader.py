from datetime import timedelta, date, datetime

class Profit:

	def __init__(self, roe, pnl):
		self.roe = roe
		self.pnl = pnl

	@property
	def roi(self):
		return self.roe

	@property
	def deposit(self):
		return self.pnl / self.roe if self.roe != 0 else 0

class Position:

	def __init__(self, time, symbol, price, amount, profit):
		self.prev = None
		self.time = time
		self.symbol = symbol
		self.price = price
		self.amount = amount
		self.profit = profit

	@property
	def total_price(self):
		return self.price * self.amount

	@property
	def long(self):
		return self.amount > 0

	@property
	def entry(self):
		return self.prev.entry if self.prev else self

	@property
	def increased(self):
		return abs(self.amount) > abs(self.prev.amount) if self.prev else True

	def chain(self, other):
		if not other:
			return self
		if self.time > other.time:
			self.prev = other
		if self.time == other.time:
			self.prev = other.prev
		return self

class PositionStats:

	def __init__(
		self, symbol, last_position = None,
		min_pnl_profit = None, max_pnl_profit = None,
		min_roe_profit = None, max_roe_profit = None
	):
		self.symbol = symbol
		self.last_position = last_position

		self.min_pnl_profit = min_pnl_profit or Profit(0, float('inf'))
		self.max_pnl_profit = max_pnl_profit or Profit(0, float('-inf'))
		self.min_roe_profit = min_roe_profit or Profit(float('inf'), 0)
		self.max_roe_profit = max_roe_profit or Profit(float('-inf'), 0)

	def update(self, position):
		self.last_position = position
		if not position:
			return

		if position.profit.pnl < self.min_pnl_profit.pnl:
			self.min_pnl_profit = position.profit
		if position.profit.pnl > self.max_pnl_profit.pnl:
			self.max_pnl_profit = position.profit
		if position.profit.roe < self.min_roe_profit.roe:
			self.min_roe_profit = position.profit
		if position.profit.roe > self.max_roe_profit.roe:
			self.max_roe_profit = position.profit

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

		self.current_profit = current_profit or Profit(0, 0)
		self.min_deposit_profit = min_deposit_profit or Profit(1, float('inf'))
		self.max_deposit_profit = max_deposit_profit or Profit(0, float('-inf'))
		self.average_deposit = average_deposit

	@property
	def timedelta(self):
		return self.periods[self.period]

	def update(self, profit, day = None):
		if not day:
			day = date.today()

		if day >= self.current_date:
			self.current_profit = profit
		self.current_date = day
		self.total_records += 1

		if profit.deposit < self.min_deposit_profit.deposit:
			self.min_deposit_profit = profit
		if profit.deposit > self.max_deposit_profit.deposit:
			self.max_deposit_profit = profit
		self.average_deposit += \
			(profit.deposit - self.average_deposit) / self.total_records

class Trader:

	def __init__(self, uid, performance = [], positions = []):
		self.id = uid
		self.all_periods_performance = {
			**{period: Performance(period) for period in Performance.periods},
			**{perf.period: perf for perf in performance}
		}
		self.positions_stats = {stats.symbol: stats for stats in positions}

	def performance(self, period = None):
		return self.all_periods_performance[period] if period \
			else self.all_periods_performance.values()

	def valuable_performance(self):
		return next(
			(perf for perf in self.performance.values() if perf.total_records > 0),
			None
		)

	def position_stats(self, symbol = None):
		if not symbol:
			return self.positions_stats.values()
		if symbol not in self.positions_stats:
			self.positions_stats[symbol] = PositionStats(symbol)
		return self.positions_stats[symbol]