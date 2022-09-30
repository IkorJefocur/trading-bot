import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from telethon import events
from telethon.helpers import add_surrogate
from telethon.tl.types import MessageEntityTextUrl
from events import Events
from ..base import Plugin
from ..models.trader import Order, OrderPoint, Profit

class TradersWatch(Plugin):

	def __init__(self, telegram_service, traders):
		super().__init__(telegram_service)
		self.events = Events(('order_made'))
		self.traders = {trader.id: trader for trader in traders}

	def start_lifecycle(self):
		self.service.target.on(events.NewMessage)(self.handle_message)
		super().start_lifecycle()

	async def handle_message(self, event):
		pattern = re.compile(r"""
			.*?\s+(.+?)\s*\|.*?\n+
			.*?:\s*(\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}:\d{2})\n+
			.*?:\s*(\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}:\d{2})\n+
			\s*([a-z]+)\s*-\s*(short|long).*?\n+
			.*?:\s*(\d+\.?\d+)\n+
			.*?:\s*(\d+\.?\d+)\n+
			.*?:\s*(\d+\.?\d+)\n+
			.*?:\s*(\d+\.?\d+)\n+
			.*?:\s*(\d+\.?\d+)%\s*\|.*?:\s*(\d+\.?\d+)
		""", re.X | re.I)
		time_pattern = '%d-%m-%Y %H:%M:%S'

		text = add_surrogate(event.message.message)
		match = pattern.match(text)
		if not match:
			return

		trader_id = parse_qs(urlparse(
			next((entity.url for entity in event.message.entities if (
				isinstance(entity, MessageEntityTextUrl)
				and entity.offset == match.start(1)
				and entity.offset + entity.length == match.end(1)
			)), '')
		).query) \
			.get('encryptedUid', [None])[0]
		if trader_id not in self.traders:
			return

		open_time = datetime.strptime(match[2], time_pattern)
		close_time = datetime.strptime(match[3], time_pattern)
		coin = match[4]
		side = match[5].lower()
		open_price = float(match[6])
		close_price = float(match[7])
		open_quanty = float(match[8])
		close_quanty = float(match[9])
		roe = float(match[10]) / 100
		pnl = float(match[11])

		self.events.order_made(Order(
			self.traders[trader_id],
			OrderPoint(open_time, open_price, open_quanty),
			OrderPoint(close_time, close_price, close_quanty),
			side, coin, Profit(roe, pnl)
		))