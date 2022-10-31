from math import floor, copysign
from .position import Order

class CoinConstraint:

	def __init__(self, min_amount, max_amount, amount_step = None):
		self.min = min_amount
		self.max = max_amount
		self.step = amount_step

	def fit(self, value, increment = 0):
		return self.round(self.restrict(value) + increment)

	def round(self, value):
		return self.float_fix(
			floor(self.float_fix(abs(value) / self.step)) \
				* copysign(1, value) * self.step
		) if self.step else self.float_fix(value)

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
		left = coin.constraint.round(full.amount_diff)

		while left > 0 if full.long == full.increased else left < 0:
			amount = coin.constraint.fit(left)
			yield Order(full.symbol, full.price, amount)
			left -= amount