from telethon import TelegramClient, events
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('DeleteBot')

BOT_TOKEN = '7785659342:AAF8sOyTxCCTBkjBjV_El_-kj5kGyjtdns8'
API_ID = 21623560
API_HASH = '8c448c687d43262833a0ab100255fb43'
TARGET_CHANNEL_ID = -1003113363809

client = TelegramClient('delete_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@client.on(events.ChatAction(chats=TARGET_CHANNEL_ID))
async def handle_channel_events(event):
    """يراقب أحداث القناة ويحذف إشعارات تغيير الاسم"""
    try:
        logger.info(f"🔔 حدث في القناة: {event}")
        
        # التحقق من أن الحدث هو تغيير اسم القناة
        if hasattr(event, 'action') and hasattr(event.action, 'title'):
            logger.info(f"🎯 إشعار تغيير اسم: {event.action.title}")
            
            # البحث عن رسالة الإشعار في القناة
            await asyncio.sleep(3)
            
            async for message in client.iter_messages(TARGET_CHANNEL_ID, limit=10):
                if (message.action and 
                    hasattr(message.action, 'title') and 
                    message.action.title == event.action.title):
                    
                    await message.delete()
                    logger.info("🗑️ تم حذف إشعار تغيير الاسم بنجاح!")
                    return
            
            logger.warning("⚠️ لم يتم العثور على رسالة الإشعار")
                
    except Exception as e:
        logger.error(f"❌ خطأ في حذف الإشعار: {e}")

@client.on(events.NewMessage(chats=TARGET_CHANNEL_ID))
async def handle_all_messages(event):
    """يراقب جميع الرسائل للتصحيح"""
    try:
        message = event.message
        if message.action:
            logger.info(f"📋 رسالة إجراء: {message.action}")
            
            if hasattr(message.action, 'title'):
                logger.info(f"🎯 إشعار تغيير اسم (من NewMessage): {message.action.title}")
                
                # حذف فوري لإشعار تغيير الاسم
                await asyncio.sleep(2)
                await message.delete()
                logger.info("🗑️ تم الحذف من NewMessage!")
                
    except Exception as e:
        logger.error(f"❌ خطأ في NewMessage: {e}")

async def main():
    logger.info("🚀 بدأ تشغيل بوت حذف إشعارات تغيير الاسم...")
    
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
