import asyncio
import os
from telegram.ext import ApplicationBuilder
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("TOKEN_TELEGRAM_BOT")
API_TOKEN_NOTEX = os.getenv("TOKEN_TELEGRAM_BOT_NOTEX")
ENVIRONMENT = os.getenv("ENVIRONMENT", "PRODUCT")

CHAT_IDS = {
    "server": "-1002404389414",
    "subscriptions": "-1002440579880",
    "daily_report": "-1002206711544",
    "errors": "-1002299462127",
    "shorts_video": "-1002484962091"
}

async def send_health_status(status, group='subscriptions'):
    if ENVIRONMENT.lower() == "dev":
        return
        
    chat_id = CHAT_IDS.get(group, CHAT_IDS['subscriptions'])
    
    token = API_TOKEN
    
    if group == 'server':
        emoji = "📥"
    elif group == 'subscriptions':
        emoji = "🎉"
        token = API_TOKEN_NOTEX
    elif group == 'daily_report':
        emoji = "📊"
        token = API_TOKEN_NOTEX
    elif group == 'shorts_video':
        emoji = "🎥"
        token = API_TOKEN_NOTEX
    else:
        emoji = "🚨"
    message = f"{emoji} {ENVIRONMENT}:\n{status}"
    
    async with ApplicationBuilder().token(token).build() as application:
        await application.bot.send_message(chat_id=chat_id, text=message)

# async def main():
#     await send_health_status(status="test bot", group="shorts_video")

# if __name__ == "__main__":
#     asyncio.run(main())