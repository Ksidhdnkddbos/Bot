import asyncio
import pytz
from datetime import datetime
from telegram import Bot
from telegram.error import BadRequest, TimedOut
import logging

# الإعدادات الأساسية
TOKEN = "7145022358:AAH8Mo5WzM3HTCibUqZ-E2RYcLPXmf6b8BY"
CHANNEL_ID = -1002551837124
BAGHDAD_TZ = pytz.timezone('Asia/Baghdad')

# زخرفة الأرقام - الإصلاح هنا
normzltext = "1234567890"
namerzfont = "𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿𝟶"

# إعداد التسجيل المخفف
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    datefmt='%H:%M:%S'
)

# تعطيل السجلات غير الضرورية
logging.getLogger("httpx").setLevel(logging.WARNING)

class ChannelUpdater:
    """فئة لإدارة تحديث القناة بكفاءة"""
    
    def __init__(self):
        self.bot = Bot(token=TOKEN)
        self.last_minute = None
        self.consecutive_errors = 0
        
    def _decorate_time(self, time_str: str) -> str:
        """تطبيق الزخرفة على الوقت بكفاءة - الإصلاح هنا"""
        # استخدام str.maketrans بشكل صحيح
        translator = str.maketrans(normzltext, namerzfont)
        return time_str.translate(translator)
    
    async def _safe_delete_notification(self):
        """حذف الإشعار بأمان مع تقليل استهلاك الموارد"""
        try:
            updates = await self.bot.get_updates(
                offset=-1,
                timeout=0.3,
                limit=1
            )
            
            for update in updates:
                if (update.channel_post and 
                    update.channel_post.chat.id == CHANNEL_ID and
                    hasattr(update.channel_post, 'new_chat_title')):
                    
                    await self.bot.delete_message(
                        CHANNEL_ID,
                        update.channel_post.message_id
                    )
                    return True
                    
        except (TimedOut, BadRequest):
            pass
        except Exception:
            self.consecutive_errors += 1
            
        return False
    
    async def update_channel_name(self):
        """تحديث اسم القناة مرة واحدة"""
        try:
            now = datetime.now(BAGHDAD_TZ)
            current_minute = now.minute
            
            # التحقق من عدم تكرار التحديث لنفس الدقيقة
            if current_minute == self.last_minute:
                return False
            
            # تحويل الوقت إلى نظام 12 ساعة
            hour = now.hour
            hour_12 = hour % 12
            if hour_12 == 0:
                hour_12 = 12
            
            # تحديد الفترة (صباحاً/مساءً)
            period = "صَ" if hour < 12 else "مَ"
            
            # تنسيق وزخرفة الوقت
            time_str = f"{hour_12:02d}:{now.minute:02d}"
            decorated_time = self._decorate_time(time_str)
            
            # تحديث اسم القناة
            new_name = f"𓏺 {decorated_time} . {period}"
            await self.bot.set_chat_title(CHANNEL_ID, new_name)
            
     #       logging.info(f"✅ {now.strftime('%H:%M:%S')} - {new_name}")
            
            # تحديث آخر دقيقة
            self.last_minute = current_minute
            self.consecutive_errors = 0
            
            # محاولة حذف الإشعار بعد فترة قصيرة
            await asyncio.sleep(2.4)
            await self._safe_delete_notification()
            
            return True
            
        except Exception as e:
            self.consecutive_errors += 1
            if self.consecutive_errors > 5:
                logging.error(f"❌ أخطاء متتالية: {e}")
            return False
    
    async def run(self):
        """تشغيل البوت بشكل دائم"""
        logging.info("🚀 بدأ تشغيل البوت (النسخة المحسنة والمُصلَحة)")
        
        try:
            while True:
                now = datetime.now(BAGHDAD_TZ)
                
                # تحديث فقط عند تغيير الدقيقة
                if now.minute != self.last_minute:
                    await self.update_channel_name()
                
                # انتظار أطول بين الفحوصات لتقليل الحمل
                await asyncio.sleep(15)
                
        except KeyboardInterrupt:
            logging.info("⏹️ إيقاف البوت...")
        finally:
            await self.bot.close()

async def main():
    """الدالة الرئيسية"""
    updater = ChannelUpdater()
    await updater.run()

if __name__ == "__main__":
    import sys
    if not sys.flags.debug:
        logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    asyncio.run(main())
