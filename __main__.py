from os import environ
from dotenv import load_dotenv
from project import run, Server, Bot

load_dotenv()

run(
	Server(allowed_ips = ['127.0.0.1']),
	Bot(token = environ['TELEGRAM_TOKEN'], chats = [environ['TELEGRAM_CHAT']])
)