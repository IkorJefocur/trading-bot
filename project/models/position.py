from datetime import datetime

class Symbol:

	existing_currencies = {
		'USD',
		'USDT'
	}

	@classmethod
	def valid(cls, value):
		return bool(next(
			(cur for cur in cls.existing_currencies if value.endswith(cur)),
			False
		))

	def __init__(self, value):
		try:
			self.currency = next(
				cur for cur in self.existing_currencies if value.endswith(cur)
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

	def __init__(self, symbol, price, amount, profit):
		self.prev = None
		self.symbol = symbol
		self.price = price
		self.amount = amount
		self.profit = profit

	def __eq__(self, other):
		return (
			isinstance(other, Position)
			and self.symbol == other.symbol
			and self.price == other.price
			and self.amount == other.amount
		)

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
		if other:
			self.prev = other.prev if self == other else other
		return self

	def close(self):
		return Position(
			self.symbol, self.price, 0, self.profit
		).chain(self)

class PlacedPosition(Position):

	def __init__(self, symbol, price, amount, profit, time = None):
		super().__init__(symbol, price, amount, profit)
		self.time = time or datetime.now()

	def __eq__(self, other):
		return self.time == other.time if isinstance(other, PlacedPosition) \
			else super().__eq__(other)

class ReflectivePosition(Position):

	def __init__(self, symbol, price, parts, profit):
		super().__init__(symbol, price, 0, profit)
		self.parts = parts

	@property
	def amount(self):
		return sum(self.parts_chain.values())
	@amount.setter
	def amount(self, value): pass

	@property
	def parts_chain(self):
		prev = self.prev.parts_chain \
			if isinstance(self.prev, ReflectivePosition) else {}
		return {**prev, **self.parts}

	def part(self, key):
		return self.parts.get(key, 0)

	def part_diff(self, key):
		return self.part(key) - self.prev.part(key) \
			if isinstance(self.prev, ReflectivePosition) \
			else self.part(key)