from math import copysign
from .position import Position

class SymbolConstraint:

	def __init__(self, min_amount, max_amount, amount_step = None):
		self.min = min_amount
		self.max = max_amount
		self.step = amount_step

	def fit(self, value, increment = 0):
		return self.round(self.restrict(value) + increment)

	def round(self, value):
		return self.float_fix(
			round(value / self.step) * self.step if self.step else value
		)

	def restrict(self, value):
		return min(max(abs(value), self.min), self.max) * copysign(1, value)

	def float_fix(self, value):
		return round(value, 10)

class Market:

	def __init__(self):
		self.constraints = {}

	def constraint(self, symbol):
		return self.constraints.get(symbol.value) \
			or SymbolConstraint(0, float('inf'))

	def set_constraint(self, symbol, constraint):
		self.constraints[symbol.value] = constraint

	def adjust_position(self, full):
		constraint = self.constraint(full.symbol)
		amount = constraint.round(full.amount)
		filled = amount - full.amount_diff
		head = None

		while abs(filled) < abs(amount):
			filled = constraint.fit(amount - filled, filled)
			head = Position(
				full.symbol, full.price, filled, full.profit
			).chain(head)
			yield head