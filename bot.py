from telethon import TelegramClient
from telethon.tl.functions.messages import DeleteHistory
from telethon.tl.types import PeerChannel

# إعداد المتغيرات
BOT_TOKEN = '7785659342:AAF8sOyTxCCTBkjBjV_El_-kj5kGyjtdns8'
API_ID = 21623560
API_HASH = '8c448c687d43262833a0ab100255fb43'
TARGET_CHANNEL_ID = -1003113363809

# إنشاء عميل تليجرام
client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

async def delete_notifications():
    # حذف الإشعارات من القناة
    await client(DeleteHistory(peer=PeerChannel(TARGET_CHANNEL_ID), max_id=0, just_clear=True))

# تشغيل العميل
with client:
    client.loop.run_until_complete(delete_notifications())
