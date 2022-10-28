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
			if Symbol.valid(symbol['name']):
				self.market.add_coin(Coin(
					Symbol(symbol['name']),
					CoinConstraint(
						symbol['lot_size_filter']['min_trading_qty'],
						symbol['lot_size_filter']['max_trading_qty'],
						symbol['lot_size_filter']['qty_step']
					)
				))

	async def watch(self):
		self.service.usdt_perpetual_ws.wallet_stream(self.update_deposit)

	def update_deposit(self, data):
		self.user.deposit = data['data'][0]['wallet_balance']

class BybitCopytradingWatch(BybitWatch):

	async def init(self):
		self.user.deposit = float(self.service.target.get(
			'/contract/v3/private/copytrading/wallet/balance',
			coin = 'USDT'
		)['result']['walletBalance'])

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

	async def watch(self):
		ws = self.service.ws_private
		ws.subscribe('copyTradeWallet', self.update_deposit)

	def update_deposit(self, data):
		self.user.depoit = data['data']['walletBalance']