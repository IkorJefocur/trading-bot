from ..base import Plugin
from ..models.position import Symbol
from ..models.market import CoinConstraint, Coin

class BybitWatch(Plugin):

	def __init__(self, bybit_service, market, user):
		super().__init__(bybit_service)
		self.market = market
		self.user = user

	def start_lifecycle(self):
		super().start_lifecycle()
		self.service.run_task_sync(self.init())
		self.service.send_task(self.watch())

	async def init(self):
		self.user.deposit = self.service.usdt_perpetual.get_wallet_balance(
			coin = 'USDT'
		)['result']['USDT']['wallet_balance']

		for symbol in self.service.usdt_perpetual.query_symbol()['result']:
			constraint = symbol['lot_size_filter']
			if Symbol.valid(symbol['name']):
				self.market.add_coin(Coin(
					Symbol(symbol['name']),
					CoinConstraint(
						constraint['min_trading_qty'],
						constraint['max_trading_qty'],
						constraint['qty_step']
					)
				))

	async def watch(self):
		self.service.usdt_perpetual_ws.wallet_stream(self.update_deposit)

	def update_deposit(self, data):
		self.user.deposit = data['data'][0]['wallet_balance']