from math import floor, copysign
from .position import Position

class CoinConstraint:

	def __init__(self, min_amount, max_amount, amount_step = None):
		self.min = min_amount
		self.max = max_amount
		self.step = amount_step

	def fit(self, value, increment = 0):
		return self.round(self.restrict(value) + increment)

	def round(self, value):
		return self.float_fix(
			floor(value / self.step) * self.step if self.step else value
		)

	def restrict(self, value):
		return min(max(abs(value), self.min), self.max) * copysign(1, value)

	def float_fix(self, value):
		return round(value, 10)

class Coin:

	def __init__(
		self, symbol,
		constraint = CoinConstraint(0, float('inf'))
	):
		self.symbol = symbol
		self.constraint = constraint

class Market:

	def __init__(self):
		self.coins = {}

	def coin(self, symbol):
		return self.coins.get(symbol.value)

	def add_coin(self, coin):
		self.coins[coin.symbol.value] = coin

	def adjust_position(self, full):
		coin = self.coin(full.symbol)
		if not coin:
			return

		amount = coin.constraint.round(full.amount)
		filled = amount - full.amount_diff
		head = None

		while abs(filled) < abs(amount):
			filled = coin.constraint.fit(amount - filled, filled)
			head = Position(
				full.symbol, full.price, filled
			).chain(head)
			yield head