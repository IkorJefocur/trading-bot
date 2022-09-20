class Order:

	def __init__(self, side, coin, time, close, low, high, tf):
		self.buy = side if type(side) == bool else side == 'buy'
		self.coin = coin
		self.time = time
		self.close = close
		self.low = low
		self.high = high
		self.tf = tf