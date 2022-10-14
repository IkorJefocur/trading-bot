from datetime import timedelta, datetime

class Symbol:

	existing_currencies = {
		'USDT'
	}

	def __init__(self, value):
		try:
			self.currency = next(
				cur for cur in self.existing_currencies if cur in value
			)
		except StopIteration:
			raise ValueError(f'Currency for symbol {value} does not exists')
		self.coin = value[: value.find(self.currency)]

	@property
	def value(self):
		return f'{self.coin}{self.currency}'

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

	def __init__(self, symbol, price, amount, profit, time = None):
		self.prev = None
		self.time = time or datetime.now()
		self.symbol = symbol
		self.price = price
		self.amount = amount
		self.profit = profit

	@property
	def entry(self):
		return self.prev.entry if self.prev else self

	@property
	def total_price(self):
		return self.price * self.amount

	@property
	def amount_diff(self):
		return self.amount - (self.prev.amount if self.prev else 0)

	@property
	def closed(self):
		return self.amount == 0

	@property
	def long(self):
		return self.amount > 0 if not self.closed \
			else self.prev.long if self.prev \
			else False

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

	def chain_equal(self, other):
		return bool(other) and self.time == other.time

	def close(self):
		return Position(
			self.symbol, self.price, 0, self.profit
		).chain(self)

class TradingAccount:

	def __init__(self, deposit):
		self.deposit = deposit
		self.opened_positions = {}

	def opened_position(self, matcher = None):
		if not matcher:
			return [*self.opened_positions.values()]
		return self.opened_positions.get(self.position_category(matcher))

	def has_position(self, position):
		return position.chain_equal(self.opened_position(position))

	def add_position(self, position):
		category = self.position_category(position)
		position = position.chain(self.opened_positions.get(category))

		if position.closed:
			if category in self.opened_positions:
				del self.opened_positions[category]
		else:
			self.opened_positions[category] = position

		return position

	def position_category(self, position):
		return f"{'LONG' if position.long else 'SHORT'}-{position.symbol.value}"