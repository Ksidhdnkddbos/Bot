from telethon import TelegramClient
from telethon.tl.types import ChannelAdminLogEventActionChangeTitle
from telethon.tl.functions.channels import GetAdminLogRequest
from telethon.tl.types import InputChannel
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('AdminLogBot')

async def admin_log_bot():
    client = TelegramClient('admin_bot', 21623560, '8c448c687d43262833a0ab100255fb43')
    await client.start(bot_token='7785659342:AAF8sOyTxCCTBkjBjV_El_-kj5kGyjtdns8')
    
    logger.info("🚀 بوت سجل المشرفين يعمل...")
    
    channel = await client.get_entity(-1003113363809)
    input_channel = InputChannel(channel.id, channel.access_hash)
    
    last_event = 0
    
    while True:
        try:
            # جلب سجل المشرفين
            result = await client(GetAdminLogRequest(
                channel=input_channel,
                q='',
                max_id=0,
                min_id=last_event,
                limit=5
            ))
            
            for event in result.events:
                if event.id > last_event:
                    last_event = event.id
                    
                    # إذا كان تغيير اسم
                    if isinstance(event.action, ChannelAdminLogEventActionChangeTitle):
                        logger.info(f"🔄 تغيير اسم: {event.action.new_value}")
                        
                        # حذف آخر رسالة (الإشعار)
                        async for msg in client.iter_messages(channel, limit=1):
                            if msg.action:
                                await msg.delete()
                                logger.info("🗑️ تم حذف الإشعار!")
                            break
            
            await asyncio.sleep(3)
            
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            await asyncio.sleep(5)

asyncio.run(admin_log_bot())
