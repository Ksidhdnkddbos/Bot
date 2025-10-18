from telethon import TelegramClient, events
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('DeleteBot')

# إعدادات البوت الجديدة
BOT_TOKEN = '7785659342:AAF8sOyTxCCTBkjBjV_El_-kj5kGyjtdns8'
API_ID = 21623560
API_HASH = '8c448c687d43262833a0ab100255fb43'
TARGET_CHANNEL_ID = -1003113363809  # ID قناتك

client = TelegramClient('delete_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@client.on(events.ChatAction(chats=TARGET_CHANNEL_ID))
async def handle_channel_events(event):
    """يراقب أحداث القناة ويحذف إشعارات تغيير الاسم"""
    try:
        # التحقق من أن الحدث هو تغيير اسم القناة
        if hasattr(event.action, 'title') and event.action.title:
            logger.info(f"🎯 إشعار تغيير اسم مكتشف: {event.action.title}")
            
            # انتظار 3 ثواني ثم الحذف
            await asyncio.sleep(3)
            
            if event.action_message:
                await event.action_message.delete()
                logger.info("🗑️ تم حذف إشعار تغيير الاسم بنجاح!")
            else:
                logger.warning("⚠️ لا توجد رسالة إجراء لحذفها")
                
    except Exception as e:
        logger.error(f"❌ خطأ في حذف الإشعار: {e}")

async def main():
    logger.info("🚀 بدأ تشغيل بوت حذف إشعارات تغيير الاسم...")
    
    # اختبار الاتصال
    me = await client.get_me()
    logger.info(f"🤖 البوت: @{me.username}")
    
    try:
        channel = await client.get_entity(TARGET_CHANNEL_ID)
        logger.info(f"📊 البوت يعمل على قناة: {channel.title}")
    except Exception as e:
        logger.error(f"❌ خطأ في الاتصال بالقناة: {e}")
        return
    
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
