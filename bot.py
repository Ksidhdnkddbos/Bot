from telethon import TelegramClient
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('UltimateDeleteBot')

async def ultimate_delete_bot():
    client = TelegramClient('ultimate', 21623560, '8c448c687d43262833a0ab100255fb43')
    await client.start(bot_token='7785659342:AAF8sOyTxCCTBkjBjV_El_-kj5kGyjtdns8')
    
    logger.info("🔥 البوت النهائي يعمل - جاهز لحذف الإشعارات!")
    
    while True:
        try:
            # الحصول على آخر رسالة فقط
            async for message in client.iter_messages(-1003113363809, limit=1):
                if message.action and hasattr(message.action, 'title'):
                    logger.info(f"🎯 حذف إشعار: {message.action.title}")
                    await message.delete()
                    logger.info("✅ تم الحذف!")
                break
                
            await asyncio.sleep(1)  # فحص كل ثانية
            
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            await asyncio.sleep(3)

asyncio.run(ultimate_delete_bot())
