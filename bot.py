from telethon import TelegramClient
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('DeleteBot')

BOT_TOKEN = '7785659342:AAF8sOyTxCCTBkjBjV_El_-kj5kGyjtdns8'
API_ID = 21623560
API_HASH = '8c448c687d43262833a0ab100255fb43'
TARGET_CHANNEL_ID = -1003113363809

async def simple_delete_bot():
    client = TelegramClient('simple_bot', API_ID, API_HASH)
    await client.start(bot_token=BOT_TOKEN)
    
    logger.info("🚀 بوت الحذف البسيط يعمل...")
    
    last_message_id = 0
    
    while True:
        try:
            # الحصول على آخر رسالة
            async for message in client.iter_messages(TARGET_CHANNEL_ID, limit=1):
                current_message_id = message.id
                
                # إذا كانت رسالة جديدة
                if current_message_id > last_message_id:
                    last_message_id = current_message_id
                    
                    # التحقق إذا كانت إشعار تغيير اسم
                    if message.action and hasattr(message.action, 'title'):
                        logger.info(f"🎯 إشعار تغيير اسم: {message.action.title}")
                        
                        # حذف فوري
                        await message.delete()
                        logger.info("🗑️ تم حذف الإشعار!")
                    else:
                        logger.info("🔍 ليست رسالة تغيير اسم.")

                break
            
            await asyncio.sleep(3)  # فحص كل 3 ثواني
            
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            await asyncio.sleep(10)

if __name__ == '__main__':
    asyncio.run(simple_delete_bot())
