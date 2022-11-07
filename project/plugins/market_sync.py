from ..base import Plugin
from ..models.position import Symbol
from ..models.market import CoinConstraint, Coin

class MarketSync(Plugin):

	def __init__(self, bybit_service, market):
		super().__init__(bybit_service)
		self.market = market

	def start_lifecycle(self):
		super().start_lifecycle()
		self.service.run_task_sync(self.init())

	async def init(self):
		for symbol in self.service.usdt_perpetual.query_symbol()['result']:
			if Symbol.valid(symbol['name']):
				self.market.add_coin(Coin(
					Symbol(symbol['name']),
					CoinConstraint(
						symbol['lot_size_filter']['min_trading_qty'],
						symbol['lot_size_filter']['max_trading_qty'],
						symbol['lot_size_filter']['qty_step']
					)
				))

class CopytradingMarketSync(MarketSync):

	async def init(self):
		for symbol in self.service.target.get(
			'/contract/v3/public/copytrading/symbol/list'
		)['result']['list']:
			if Symbol.valid(symbol['symbol']):
				self.market.add_coin(Coin(
					Symbol(symbol['symbol']),
					CoinConstraint(
						float(symbol['lotSizeFilter']['minOrderQty']),
						float(symbol['lotSizeFilter']['maxOrderQty']),
						float(symbol['lotSizeFilter']['qtyStep'])
					)
				))