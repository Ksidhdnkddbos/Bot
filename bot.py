from telethon import TelegramClient, events
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('DeleteBot')

BOT_TOKEN = '7785659342:AAF8sOyTxCCTBkjBjV_El_-kj5kGyjtdns8'
API_ID = 21623560
API_HASH = '8c448c687d43262833a0ab100255fb43'
TARGET_CHANNEL_ID = -1003113363809 # ID قناتك

client = TelegramClient('delete_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@client.on(events.NewMessage(chats=TARGET_CHANNEL_ID))
async def delete_notification(event):
    try:
        message = event.message
        
        # Debug: طباعة كل الرسائل
        logger.info(f"📨 رسالة جديدة - ID: {message.id} - النص: {message.text}")
        
        # التحقق من إشعار التغيير
        if message.action:
            logger.info(f"🔍 إجراء مكتشف: {message.action}")
            
            if hasattr(message.action, 'title'):
                logger.info(f"🎯 إشعار تغيير اسم: {message.action.title}")
                
                # حذف الإشعار بعد 2 ثانية
                await asyncio.sleep(2)
                await message.delete()
                logger.info("🗑️ تم حذف إشعار التغيير بنجاح!")
                return
        
        # إذا كانت رسالة عادية
        logger.info(f"💬 رسالة عادية: {message.text}")
            
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")

# أمر اختبار
@client.on(events.NewMessage(pattern='/test'))
async def test_command(event):
    await event.reply("✅ البوت يعمل وجاهز لحذف الإشعارات!")
    logger.info("✅ تم استلام أمر الاختبار")

async def main():
    logger.info("🚀 بدأ تشغيل بوت حذف الإشعارات...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
