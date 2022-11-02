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

	def __hash__(self):
		return hash(self.value)

	def __eq__(self, other):
		return isinstance(other, Symbol) and self.value == other.value

	def __str__(self):
		return self.value

	@property
	def value(self):
		return f'{self.coin}{self.currency}'

class Profit:

	@staticmethod
	def by_diff(less, more, multiplier = 1):
		return Profit((more / less) - 1, (more - less) * multiplier)

	def __init__(self, roe, pnl):
		self.roe = roe
		self.pnl = pnl

	@property
	def roi(self):
		return self.roe

	@property
	def deposit(self):
		return self.pnl / self.roe if self.roe != 0 else 0

class Deal:

	def __init__(self, symbol, price, amount):
		self.symbol = symbol
		self.price = price
		self.amount = amount

	@property
	def total_price(self):
		return self.price * self.amount

	@property
	def closed(self):
		return self.amount == 0

	@property
	def long(self):
		return self.amount > 0

class Order(Deal):

	@property
	def place_amount(self):
		return abs(self.amount)

	def profit(self, current_price):
		prices = (self.price, current_price) if self.long \
			else (current_price, self.price)
		return Profit.by_diff(*prices, self.amount)

	def compensate(self):
		return Order(self.symbol, self.price, -self.amount)

class Position(Deal):

	@staticmethod
	def add_order(position, order):
		return Position(
			order.symbol, order.price,
			(position.amount if position else 0) + order.amount
		).chain(position)

	def __init__(self, symbol, price, amount):
		super().__init__(symbol, price, amount)
		self.prev = None

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
	def amount_diff(self):
		return self.amount - (self.prev.amount if self.prev else 0)

	@property
	def long(self):
		return super().long if not self.closed \
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
			self.symbol, self.price, 0
		).chain(self)

	def generate_order(self):
		return Order(self.symbol, self.price, self.amount_diff)

class PlacedPosition(Position):

	def __init__(self, symbol, price, amount, profit, time = None):
		super().__init__(symbol, price, amount)
		self.profit = profit
		self.time = time or datetime.now()

	def __eq__(self, other):
		return self.time == other.time if isinstance(other, PlacedPosition) \
			else super().__eq__(other)

class ReflectivePosition(Position):

	@staticmethod
	def add_order(position, order, key = None):
		pos_amount = position.amount if position else 0
		parts = {key: position.part(key) + order.amount} \
			if isinstance(position, ReflectivePosition) \
			else {None: pos_amount, key: order.amount} if key != None \
			else {None: pos_amount + order.amount}
		return ReflectivePosition(
			order.symbol, order.price, parts
		).chain(position)

	def __init__(self, symbol, price, parts):
		super().__init__(symbol, price, 0)
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