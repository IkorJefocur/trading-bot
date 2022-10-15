from math import copysign
from .position import Symbol, Position, TradingAccount

class SymbolConstraint:

	def __init__(self, min_amount, max_amount, amount_step = None):
		self.min = min_amount
		self.max = max_amount
		self.step = amount_step

	def fit(self, value):
		return self.round(self.restrict(value))

	def round(self, value):
		return self.float_fix(
			round(value / self.step) * self.step if self.step else value
		)

	def restrict(self, value):
		return min(max(abs(value), self.min), self.max) * copysign(1, value)

	def float_fix(self, value):
		return round(value, 10)

class ReflectivePosition(Position):

	def __init__(
		self, symbol, price, parts, profit,
		constraint = None, time = None
	):
		super().__init__(symbol, price, 0, profit, time)
		self.parts = parts
		self.constraint = constraint or SymbolConstraint(0, float('inf'))

	@property
	def amount(self):
		prev = self.prev.amount if self.prev else 0
		return self.constraint.round(prev + self.amount_diff)
	@amount.setter
	def amount(self, value): pass

	@Position.amount_diff.getter
	def amount_diff(self):
		prev = self.prev.amount if self.prev else 0
		current = sum(self.parts_chain.values())
		return self.constraint.fit(current - prev)

	@property
	def parts_chain(self):
		prev = self.prev.parts_chain \
			if isinstance(self.prev, ReflectivePosition) else {}
		return {**prev, **self.parts}

class User(TradingAccount):

	def __init__(self, deposit):
		super().__init__(deposit)
		self.constraints = {}

	def set_constraint(self, symbol, constraint):
		if isinstance(symbol, Symbol):
			symbol = symbol.value
		self.constraints[symbol] = constraint

	def copy_position(self, base, trader):
		amount = base.amount \
			* (self.deposit / trader.deposit if trader.deposit > 0 else 0)

		return ReflectivePosition(
			base.symbol, base.price, {trader: amount}, base.profit,
			self.constraints.get(base.symbol.value)
		)