class Order:

	def __init__(self, side, coin, time, close, low, high, tf):
		self.buy = side if type(side) == bool else side == 'buy'
		self.coin = coin
		self.time = time
		self.close = close
		self.low = low
		self.high = high
		self.tf = tf

	@property
	def pivot(self):
		return self.low if self.buy else self.high

	@property
	def candle_shadow(self):
		return abs(self.close - self.pivot)