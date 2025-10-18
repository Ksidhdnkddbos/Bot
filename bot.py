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
        logger.info(f"🔔 حدث تغيير اسم مكتشف!")
        
        # التحقق من أن الحدث هو تغيير اسم القناة
        if hasattr(event, 'action') and hasattr(event.action, 'title'):
            logger.info(f"🎯 العنوان الجديد: {event.action.title}")
            
            # الحذف المباشر لرسالة الحدث
            if hasattr(event, 'action_message') and event.action_message:
                await asyncio.sleep(2)
                await event.action_message.delete()
                logger.info("🗑️ تم حذف إشعار تغيير الاسم بنجاح!")
            else:
                logger.warning("⚠️ لا توجد رسالة إجراء مباشرة، جرب البحث...")
                
                # البحث عن الرسالة في القناة
                await asyncio.sleep(3)
                async for message in client.iter_messages(TARGET_CHANNEL_ID, limit=5):
                    if (message and 
                        hasattr(message, 'action') and 
                        message.action and 
                        hasattr(message.action, 'title')):
                        
                        await message.delete()
                        logger.info("🗑️ تم حذف الإشعار بالبحث!")
                        break
                
    except Exception as e:
        logger.error(f"❌ خطأ في حذف الإشعار: {e}")

async def main():
    logger.info("🚀 بدأ تشغيل بوت حذف إشعارات تغيير الاسم...")
    
    me = await client.get_me()
    logger.info(f"🤖 البوت: @{me.username}")
    
    try:
        channel = await client.get_entity(TARGET_CHANNEL_ID)
        logger.info(f"📊 البوت يعمل على قناة: {channel.title}")
        
        # اختبار الصلاحيات
        me_entity = await client.get_entity(me.id)
        permissions = await client.get_permissions(TARGET_CHANNEL_ID, me_entity)
        logger.info(f"🔐 صلاحية الحذف: {permissions.delete_messages}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في الاتصال: {e}")
        return
    
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
