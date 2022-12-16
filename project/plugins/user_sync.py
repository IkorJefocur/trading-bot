from ..base import Plugin
from ..models.trader import User

class UserSync(Plugin):

	def __init__(self, bybit_service):
		super().__init__(bybit_service)
		self.user = User(0)

	def start_lifecycle(self):
		super().start_lifecycle()
		self.service.run_task_sync(self.init())
		self.service.send_task(self.watch())

	async def init(self):
		self.user.deposit = self.service.usdt_perpetual.get_wallet_balance(
			coin = 'USDT'
		)['result']['USDT']['wallet_balance']

	async def watch(self):
		self.service.usdt_perpetual_ws.wallet_stream(self.update_deposit)

	def update_deposit(self, data):
		self.user.deposit = data['data'][0]['wallet_balance']

class CopytradingUserSync(UserSync):

	async def init(self):
		self.user.deposit = float(self.service.http.get(
			'/contract/v3/private/copytrading/wallet/balance',
			coin = 'USDT'
		)['result']['walletBalance'])

	async def watch(self):
		ws = self.service.ws_private
		ws.subscribe('copyTradeWallet', self.update_deposit)

	def update_deposit(self, data):
		self.user.deposit = data['data']['walletBalance']