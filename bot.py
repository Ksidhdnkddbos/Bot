from telethon import TelegramClient, events
import asyncio
import logging

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('DeleteBot')

# إعدادات البوت
BOT_TOKEN = '7785659342:AAF8sOyTxCCTBkjBjV_El_-kj5kGyjtdns8'
API_ID = 21623560  # أو استخدم Config.APP_ID
API_HASH = '8c448c687d43262833a0ab100255fb43'  # أو استخدم Config.API_HASH

# قناة الهدف (ضع ID القناة هنا)
TARGET_CHANNEL_ID = -1001234567890  # غير هذا إلى ID قناتك

client = TelegramClient('delete_bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@client.on(events.NewMessage(chats=TARGET_CHANNEL_ID))
async def delete_notification(event):
    """يحذف إشعارات تغيير اسم القناة تلقائياً"""
    try:
        message = event.message
        
        # التحقق إذا كانت الرسالة إشعار تغيير اسم
        if (message.action and 
            hasattr(message.action, 'title') and 
            message.action.title):
            
            # انتظار قليل ثم الحذف
            await asyncio.sleep(3)
            await message.delete()
            logger.info(f"🗑️ تم حذف إشعار تغيير الاسم: {message.action.title}")
            
    except Exception as e:
        logger.error(f"❌ خطأ في حذف الإشعار: {e}")

async def main():
    """الدالة الرئيسية"""
    logger.info("🚀 بدأ تشغيل بوت حذف الإشعارات...")
    logger.info(f"📊 البوت يعمل على القناة: {TARGET_CHANNEL_ID}")
    
    # الحصول على معلومات البوت
    me = await client.get_me()
    logger.info(f"🤖 البوت: @{me.username} ({me.id})")
    
    # تشغيل البوت
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
