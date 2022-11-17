class TraderMeta:

	def __init__(self, uid, name = ''):
		self.id = uid
		self.nickname = name

	@property
	def binance_url(self):
		return 'https://www.binance.com/ru/futures-activity/leaderboard' \
			+ f'/user?encryptedUid={self.id}'