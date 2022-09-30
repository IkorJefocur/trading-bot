class Trader:

	def __init__(self, uid, performance = {}):
		self.id = uid
		self.performance = performance

class Order:

	def __init__(self, trader, open_point, close_point, side, coin, profit):
		self.trader = trader
		self.open = open_point
		self.close = close_point
		self.side = side if type(side) == bool else side == 'long'
		self.coin = coin
		self.profit = profit

class OrderPoint:

	def __init__(self, time, price, quanty):
		self.time = time
		self.price = price
		self.quanty = quanty

class Profit:

	def __init__(self, roe, pnl):
		self.roe = roe
		self.pnl = pnl