
import http.client
import json
import re
import gzip
import os
import tempfile
import time
from deepseekpowsolver import DeepSeekPowSolver
import telebot
from telebot import types
import threading

# توكن البوت
BOT_TOKEN = input("token bot :")
bot = telebot.TeleBot(BOT_TOKEN)

# توكن DeepSeek
DEEPSEEK_TOKEN = input('token deep seek')

# تخزين مؤقت للملفات المستلمة
user_files = {}
user_states = {}
processing_messages = {}

def safe_get_current_token():
    """
    دالة آمنة للحصول على التوكن
    """
    try:
        return DEEPSEEK_TOKEN
    except:
        return DEEPSEEK_TOKEN

def _make_session():
    """
    إنشاء محادثة جديدة والحصول على ID جديد
    """
    try:
        conn = http.client.HTTPSConnection("chat.deepseek.com")
        
        current_token = safe_get_current_token()
        
        headers = {
            'User-Agent': "DeepSeek/1.4.2 Android/34",
            'Accept': "application/json",
            'Accept-Encoding': "gzip",
            'x-client-platform': "android",
            'x-client-version': "1.4.2",
            'x-client-locale': "ar",
            'x-rangers-id': "7094179430502815498",
            'authorization': f"Bearer {current_token}",
            'accept-charset': "UTF-8",
            'content-type': "application/json",
            'content-length': "0"
        }
        
        conn.request("POST", "/api/v0/chat_session/create", headers=headers)
        res = conn.getresponse()
        data = res.read()
        
        if res.getheader('Content-Encoding') == 'gzip':
            data = gzip.decompress(data)
        
        json_data = json.loads(data.decode('utf-8'))
        
        if json_data.get("code") == 0:
            new_id = json_data["data"]["biz_data"]["id"]
            print(f"✅ تم إنشاء محادثة جديدة: {new_id}")
            return new_id
        else:
            print(f"❌ فشل في إنشاء المحادثة: {json_data}")
            return None
            
    except Exception as e:
        print(f"❌ خطأ في إنشاء المحادثة: {e}")
        return None
    finally:
        try:
            conn.close()
        except:
            pass

def extract_response_advanced(response_data):
    """
    استخراج الرد بناءً على طريقة السورس المفتوح
    """
    try:
        if not response_data:
            return ""
            
        lines = response_data.strip().split('\n')
        complete_content = []
        thinking_content = []
        in_thinking = False
        
        for line in lines:
            if not line or not line.strip():
                continue
                
            line = line.strip()
            if not line.startswith('data: '):
                continue
                
            try:
                # إزالة "data: " وتحليل JSON
                json_str = line[6:]
                if json_str == '[DONE]':
                    break
                    
                data = json.loads(json_str)
                
                # محاكاة معالجة choices[0].delta مثل السورس
                if 'choices' in data and len(data['choices']) > 0:
                    choice = data['choices'][0]
                    if 'delta' in choice:
                        delta = choice['delta']
                        
                        # معالجة المحتوى العادي
                        if 'content' in delta and delta['content']:
                            complete_content.append(delta['content'])
                        
                        # معالجة التفكير (مشابه للسورس)
                        if 'type' in delta:
                            if delta['type'] == 'thinking':
                                if not in_thinking:
                                    in_thinking = True
                                    thinking_content.append("[思考开始]")
                            elif in_thinking:
                                in_thinking = False
                                thinking_content.append("[思考结束]")
                
                # النسخ الاحتياطي للنظام القديم (v)
                elif 'v' in data and isinstance(data['v'], str):
                    text = data['v']
                    if text and text not in ['FINISHED', 'WIP', '']:
                        complete_content.append(text)
                        
            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"خطأ في معالجة السطر: {e}")
                continue
        
        # دمج المحتوى
        final_content = ''.join(complete_content)
        
        # إضافة محتوى التفكير إذا كان موجوداً
        if thinking_content:
            thinking_text = ''.join(thinking_content)
            final_content = f"{thinking_text}\n{final_content}"
        
        return final_content
    except Exception as e:
        print(f"❌ خطأ في extract_response_advanced: {e}")
        return ""

def extract_response_simple(response_data):
    """
    طريقة مبسطة مشابهة للسورس باستخدام regex محسن
    """
    try:
        if not response_data:
            return ""
            
        # نمط محسن لاستخراج المحتوى من events
        patterns = [
            r'data:\s*{\s*"v"\s*:\s*"([^"]*)"\s*}',  # للنظام القديم
            r'data:\s*{\s*[^}]*"content"\s*:\s*"([^"]*)"[^}]*}',  # للنظام الجديد
            r'"content"\s*:\s*"([^"]*)"',  # نسخ احتياطي
        ]
        
        all_content = []
        
        for pattern in patterns:
            matches = re.findall(pattern, response_data)
            for match in matches:
                if match and match not in ['FINISHED', 'WIP', '']:
                    # تنظيف النص من الأحرف الخاصة
                    try:
                        cleaned = match.encode('utf-8').decode('unicode_escape')
                        all_content.append(cleaned)
                    except:
                        all_content.append(match)
        
        return ''.join(all_content)
    except Exception as e:
        print(f"❌ خطأ في extract_response_simple: {e}")
        return ""

def separate_code_from_explanation(response_text):
    """
    فصل الكود عن الشرح في الرد
    """
    try:
        if not response_text:
            return "", ""
            
        # أنماط للتعرف على الكود
        code_patterns = [
            r'```(?:python|py)?\s*\n(.*?)```',
            r'```(?:javascript|js)?\s*\n(.*?)```',
            r'```(?:html)?\s*\n(.*?)```',
            r'```(?:css)?\s*\n(.*?)```',
            r'```(?:php)?\s*\n(.*?)```',
            r'```(?:java)?\s*\n(.*?)```',
            r'```(?:cpp|c\+\+)?\s*\n(.*?)```',
            r'```(?:c)?\s*\n(.*?)```',
            r'```(?:c#|cs)?\s*\n(.*?)```',
            r'```(?:ruby|rb)?\s*\n(.*?)```',
            r'```(?:go)?\s*\n(.*?)```',
            r'```(?:rust|rs)?\s*\n(.*?)```',
            r'```(?:swift)?\s*\n(.*?)```',
            r'```(?:kotlin|kt)?\s*\n(.*?)```',
            r'```(?:bash|sh)?\s*\n(.*?)```',
            r'```(?:sql)?\s*\n(.*?)```',
            r'```(?:json)?\s*\n(.*?)```',
            r'```(?:xml)?\s*\n(.*?)```',
            r'```(?:yaml|yml)?\s*\n(.*?)```',
            r'```(?:markdown|md)?\s*\n(.*?)```',
            r'```\s*\n(.*?)```',  # النمط العام
        ]
        
        code_blocks = []
        detected_language = "txt"
        explanation = response_text
        
        for pattern in code_patterns:
            matches = re.findall(pattern, response_text, re.DOTALL)
            if matches:
                # تحديد اللغة من النمط
                if 'python' in pattern or 'py' in pattern:
                    detected_language = "python"
                elif 'javascript' in pattern or 'js' in pattern:
                    detected_language = "javascript"
                elif 'html' in pattern:
                    detected_language = "html"
                elif 'css' in pattern:
                    detected_language = "css"
                elif 'php' in pattern:
                    detected_language = "php"
                elif 'java' in pattern:
                    detected_language = "java"
                elif 'cpp' in pattern or 'c++' in pattern:
                    detected_language = "cpp"
                elif 'c#' in pattern or 'cs' in pattern:
                    detected_language = "cs"
                elif 'ruby' in pattern or 'rb' in pattern:
                    detected_language = "ruby"
                elif 'go' in pattern:
                    detected_language = "go"
                elif 'rust' in pattern or 'rs' in pattern:
                    detected_language = "rust"
                elif 'swift' in pattern:
                    detected_language = "swift"
                elif 'kotlin' in pattern or 'kt' in pattern:
                    detected_language = "kotlin"
                elif 'bash' in pattern or 'sh' in pattern:
                    detected_language = "bash"
                elif 'sql' in pattern:
                    detected_language = "sql"
                elif 'json' in pattern:
                    detected_language = "json"
                elif 'xml' in pattern:
                    detected_language = "xml"
                elif 'yaml' in pattern or 'yml' in pattern:
                    detected_language = "yaml"
                elif 'markdown' in pattern or 'md' in pattern:
                    detected_language = "markdown"
                
                code_blocks.extend(matches)
                
                # إزالة الكود من الشرح
                for match in matches:
                    code_block = re.escape(match)
                    explanation = re.sub(f'```.*?{code_block}.*?```', '', explanation, flags=re.DOTALL)
                    # إزالة الكود بدون علامات إذا بقي
                    explanation = explanation.replace(match, '')
                
                break  # نكتفي بأول نمط يطابق
        
        # إذا لم نجد كود في ```، نبحث عن كود بدون تنسيق
        if not code_blocks:
            # نمط للكود بدون علامات ```
            lines = response_text.split('\n')
            in_code_block = False
            current_code = []
            explanation_lines = []
            
            for line in lines:
                if any(keyword in line.lower() for keyword in ['import ', 'def ', 'class ', 'function ', 'var ', 'let ', 'const ', '<html', '<?php', 'public class', '#include', 'package ', 'using ']):
                    in_code_block = True
                
                if in_code_block:
                    current_code.append(line)
                else:
                    explanation_lines.append(line)
                    
                # محاولة اكتشاف نهاية الكود
                if in_code_block and len(line.strip()) == 0 and len(current_code) > 10:
                    break
            
            if current_code and len(current_code) > 3:
                code_blocks.append('\n'.join(current_code))
                explanation = '\n'.join(explanation_lines)
                # محاولة تخمين اللغة
                if any(word in response_text.lower() for word in ['python', 'import ', 'def ', 'print(']):
                    detected_language = "python"
                elif any(word in response_text.lower() for word in ['javascript', 'function ', 'const ', 'let ', 'var ', 'console.']):
                    detected_language = "javascript"
                elif any(word in response_text.lower() for word in ['html', '<html', '<div', '<body']):
                    detected_language = "html"
                elif any(word in response_text.lower() for word in ['css', '{', '}', 'font-size']):
                    detected_language = "css"
                elif any(word in response_text.lower() for word in ['php', '<?php', '$_']):
                    detected_language = "php"
    
        # تنظيف الشرح من الأسطر الفارغة الزائدة
        explanation = '\n'.join([line for line in explanation.split('\n') if line.strip()])
        
        # إذا لم نعثر على أي كود، نعيد النص كاملاً كشرح
        if not code_blocks:
            return "", response_text, "txt"
        
        # دمج جميع كتل الكود
        full_code = '\n\n'.join(code_blocks)
        
        return full_code, explanation, detected_language
    except Exception as e:
        print(f"❌ خطأ في separate_code_from_explanation: {e}")
        return "", response_text, "txt"

def get_file_extension(language):
    """
    الحصول على امتداد الملف المناسب للغة
    """
    extensions = {
        "python": "py",
        "javascript": "js",
        "html": "html",
        "css": "css",
        "php": "php",
        "java": "java",
        "cpp": "cpp",
        "c": "c",
        "cs": "cs",
        "ruby": "rb",
        "go": "go",
        "rust": "rs",
        "swift": "swift",
        "kotlin": "kt",
        "bash": "sh",
        "sql": "sql",
        "json": "json",
        "xml": "xml",
        "yaml": "yml",
        "markdown": "md",
        "txt": "txt"
    }
    return extensions.get(language, "txt")

def safe_read_file_content(file_path):
    """
    قراءة آمنة لمحتوى الملف مع معالجة جميع الأخطاء
    """
    try:
        if not file_path:
            return "❌ مسار الملف غير صالح"
        
        if not os.path.exists(file_path):
            return "❌ الملف غير موجود"
        
        # تحديد نوع الملف من الامتداد
        ext = os.path.splitext(file_path)[1].lower()
        
        supported_extensions = ['.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.md', '.php', '.java', '.cpp', '.c', '.rb', '.go', '.rs', '.swift', '.kt', '.sh', '.sql', '.yml', '.yaml']
        
        if ext in supported_extensions:
            # ملفات نصية
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return content
        else:
            # لملفات أخرى، نحاول قراءتها كنص
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                return content
            except:
                return "⚠️ لا يمكن قراءة محتوى الملف (قد يكون ثنائي أو مشفر)"
                
    except Exception as e:
        return f"❌ خطأ في قراءة الملف: {e}"

def send_message_to_deepseek(prompt, file_content=None):
    """
    إرسال رسالة إلى DeepSeek مع محتوى الملف
    """
    try:
        # إنشاء محادثة جديدة
        chat_session_id = _make_session()
        if not chat_session_id:
            return None

        # دمج المحتوى مع محتوى الملف
        full_prompt = prompt
        if file_content and file_content.startswith("❌") == False and file_content.startswith("⚠️") == False:
            full_prompt = f"{prompt}\n\nمحتوى الملف:\n```\n{file_content}\n```"

        solver = DeepSeekPowSolver(token=DEEPSEEK_TOKEN)
        pow_result = solver.FiF()

        if not pow_result:
            print("❌ فشل في حل التحدي")
            return None

        payload = json.dumps({
            "chat_session_id": chat_session_id,
            "parent_message_id": None,
            "prompt": full_prompt,
            "ref_file_ids": [],
            "thinking_enabled": True,
            "search_enabled": False
        })

        headers = {
            'User-Agent': "DeepSeek/1.4.2 Android/34",
            'Accept': "application/json",
            'Content-Type': "application/json",
            'x-ds-pow-response': pow_result,
            'x-client-platform': "android", 
            'x-client-version': "1.4.2",
            'x-client-locale': "ar",
            'x-rangers-id': "7094179430502815498",
            'authorization': DEEPSEEK_TOKEN,
            'accept-charset': "UTF-8"
        }

        conn = http.client.HTTPSConnection("chat.deepseek.com")
        conn.request("POST", "/api/v0/chat/completion", payload, headers)

        response = conn.getresponse()
        response_data = response.read().decode("utf-8")

        if response.status == 200:
            # تجربة الطريقة المتقدمة أولاً
            complete_message = extract_response_advanced(response_data)
            
            # إذا لم تنجح، استخدم الطريقة البسيطة
            if not complete_message:
                complete_message = extract_response_simple(response_data)
            
            return complete_message
        else:
            print(f"❌ فشل الطلب برمز الحالة: {response.status}")
            return None
            
    except Exception as e:
        print(f"❌ حدث خطأ في send_message_to_deepseek: {e}")
        return None
    finally:
        try:
            conn.close()
        except:
            pass

def safe_save_code_to_file(code_content, language, user_id):
    """
    حفظ آمن للكود في ملف بالامتداد المناسب
    """
    try:
        if not code_content:
            return None
            
        extension = get_file_extension(language)
        timestamp = int(time.time())
        filename = f"code_{user_id}_{timestamp}.{extension}"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(code_content)
        return filename
    except Exception as e:
        print(f"❌ خطأ في حفظ الملف: {e}")
        return None

def safe_save_explanation_to_file(explanation, user_id):
    """
    حفظ آمن للشرح في ملف نصي
    """
    try:
        if not explanation:
            return None
            
        timestamp = int(time.time())
        filename = f"explanation_{user_id}_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(explanation)
        return filename
    except Exception as e:
        print(f"❌ خطأ في حفظ ملف الشرح: {e}")
        return None

def safe_delete_file(file_path):
    """
    حذف آمن للملف
    """
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        print(f"❌ خطأ في حذف الملف {file_path}: {e}")
    return False

def safe_edit_message(chat_id, message_id, text, parse_mode=None):
    """
    تعديل آمن للرسالة مع معالجة الأخطاء
    """
    try:
        if message_id:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                parse_mode=parse_mode
            )
            return True
    except Exception as e:
        print(f"❌ خطأ في تعديل الرسالة {message_id}: {e}")
    return False

def safe_delete_message(chat_id, message_id):
    """
    حذف آمن للرسالة مع معالجة الأخطاء
    """
    try:
        if message_id:
            bot.delete_message(chat_id, message_id)
            return True
    except Exception as e:
        print(f"❌ خطأ في حذف الرسالة {message_id}: {e}")
    return False

def split_long_message(message, max_length=4000):
    """
    تقسيم الرسالة الطويلة إلى أجزاء
    """
    try:
        if not message:
            return []
            
        if len(message) <= max_length:
            return [message]
        
        parts = []
        while len(message) > max_length:
            # البحث عن آخر مسافة ضمن الحد الأقصى
            split_index = message.rfind('\n', 0, max_length)
            if split_index == -1:
                split_index = message.rfind(' ', 0, max_length)
            if split_index == -1:
                split_index = max_length
            
            parts.append(message[:split_index])
            message = message[split_index:].lstrip()
        
        if message:
            parts.append(message)
        
        return parts
    except Exception as e:
        print(f"❌ خطأ في split_long_message: {e}")
        return [message[:max_length]] if message else [""]

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """
    معالج أمر البداية
    """
    try:
        welcome_text = """
🚀 **مرحباً بك في بوت DeepSeek AI المتطور!**

📖 **كيفية الاستخدام:**
1. أرسل لي الملف الذي تريد تحليله (نصي، كود، إلخ)
2. ثم أرسل سؤالك أو طلبك المتعلق بالملف
3. سأقوم بتحليل المحتوى والإجابة على سؤالك

⚡ **الميزات الجديدة:**
• استخراج الكود فقط وحفظه بامتداد مناسب
• فصل الشرح عن الكود وإرسالهما منفصلين
• دعم جميع لغات البرمجة
• إرسال الملفات تلقائياً
• معالجة الردود الطويلة

📝 **الملفات المدعومة:**
- ملفات نصية (.txt)
- كود برمجي (.py, .js, .html, .php, .java, إلخ)
- ملفات Markdown (.md)
- JSON, XML, YAML
- وغيرها من الملفات النصية

💡 **أمثلة على الطلبات:**
• "رتب هذا الكود وأعطني السكربت فقط"
• "استخرج الكود وأعطني الملف بصيغة py"
• "حلل الملف وأصلح الأخطاء"

استخدم /code لتفعيل وضع استخراج الكود فقط
استخدم /full للحصول على الرد الكامل
استخدم /auto للوضع التلقائي
        """
        bot.reply_to(message, welcome_text, parse_mode='Markdown')
        
        # تعيين الحالة الافتراضية للمستخدم
        user_id = message.from_user.id
        user_states[user_id] = {'mode': 'auto'}  # auto, code_only, full
        
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {str(e)}")

@bot.message_handler(commands=['code'])
def set_code_mode(message):
    """
    تفعيل وضع استخراج الكود فقط
    """
    try:
        user_id = message.from_user.id
        user_states[user_id] = {'mode': 'code_only'}
        bot.reply_to(message, "🔧 **تم تفعيل وضع استخراج الكود فقط**\n\nالآن سأستخرج الكود فقط وأحفظه في ملف بالامتداد المناسب، وسأرسل الشرح منفصلاً.", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {str(e)}")

@bot.message_handler(commands=['full'])
def set_full_mode(message):
    """
    تفعيل وضع الرد الكامل
    """
    try:
        user_id = message.from_user.id
        user_states[user_id] = {'mode': 'full'}
        bot.reply_to(message, "📄 **تم تفعيل وضع الرد الكامل**\n\nالآن سأرسل الرد الكامل مع الشرح.", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {str(e)}")

@bot.message_handler(commands=['auto'])
def set_auto_mode(message):
    """
    تفعيل الوضع التلقائي
    """
    try:
        user_id = message.from_user.id
        user_states[user_id] = {'mode': 'auto'}
        bot.reply_to(message, "🤖 **تم تفعيل الوضع التلقائي**\n\nسأقرر تلقائياً ما إذا كان يجب استخراج الكود فقط أو إرسال الرد الكامل.", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {str(e)}")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    """
    معالج استقبال الملفات
    """
    try:
        user_id = message.from_user.id
        
        # التأكد من وجود حالة للمستخدم
        if user_id not in user_states:
            user_states[user_id] = {'mode': 'auto'}
        
        # تنظيف أي ملف قديم للمستخدم
        if user_id in user_files:
            old_file_info = user_files[user_id]
            safe_delete_file(old_file_info.get('file_path'))
            del user_files[user_id]
        
        # الحصول على معلومات الملف
        file_info = bot.get_file(message.document.file_id)
        if not file_info or not file_info.file_path:
            bot.reply_to(message, "❌ لم أستطع الحصول على معلومات الملف")
            return
            
        downloaded_file = bot.download_file(file_info.file_path)
        if not downloaded_file:
            bot.reply_to(message, "❌ فشل في تحميل الملف")
            return
        
        # حفظ الملف مؤقتاً
        file_extension = os.path.splitext(message.document.file_name)[1] if message.document.file_name else '.txt'
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
        temp_file.write(downloaded_file)
        temp_file.close()
        
        # تخزين معلومات الملف للمستخدم
        user_files[user_id] = {
            'file_path': temp_file.name,
            'file_name': message.document.file_name or 'unknown_file'
        }
        
        # قراءة محتوى الملف لعرض عينة
        file_content = safe_read_file_content(temp_file.name)
        preview = file_content[:500] + "..." if len(file_content) > 500 else file_content
        
        # الحصول على وضع المستخدم
        mode = user_states[user_id]['mode']
        mode_text = {
            'auto': 'تلقائي',
            'code_only': 'كود فقط',
            'full': 'رد كامل'
        }.get(mode, 'تلقائي')
        
        response_text = f"""
📁 **تم استلام الملف بنجاح!**

📄 **اسم الملف:** `{user_files[user_id]['file_name']}`
📊 **حجم الملف:** {len(downloaded_file)} بايت
🔧 **الوضع الحالي:** {mode_text}

📖 **عينة من المحتوى:**
```

{preview}

```

✍️ **الآن أرسل سؤالك أو طلبك المتعلق بهذا الملف**

💡 **الأوامر المتاحة:**
/code - استخراج الكود فقط
/full - الرد الكامل مع الشرح  
/auto - الوضع التلقائي
        """
        
        bot.reply_to(message, response_text, parse_mode='Markdown')
        
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ في معالجة الملف: {str(e)}")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    """
    معالج استقبال النصوص (الأسئلة) - الإصدار المحسن مع فصل الكود عن الشرح
    """
    user_id = message.from_user.id
    processing_msg_id = None
    
    try:
        # التأكد من وجود حالة للمستخدم
        if user_id not in user_states:
            user_states[user_id] = {'mode': 'auto'}
        
        # التحقق من وجود ملف للمستخدم
        if user_id not in user_files:
            bot.reply_to(message, """
❌ **لم يتم استلام ملف بعد!**

📁 يرجى إرسال الملف أولاً، ثم أرسل سؤالك.
استخدم /help لمشاهدة التعليمات.
            """)
            return
        
        file_info = user_files[user_id]
        user_question = message.text
        user_mode = user_states[user_id]['mode']
        
        # إرسال رسالة معالجة جديدة
        processing_msg = bot.send_message(message.chat.id, "🔄 جاري معالجة طلبك...")
        processing_msg_id = processing_msg.message_id
        
        # قراءة محتوى الملف
        file_content = safe_read_file_content(file_info['file_path'])
        
        # إرسال الطلب إلى DeepSeek
        response = send_message_to_deepseek(user_question, file_content)
        
        if response:
            should_send_full_response = True
            
            if user_mode == 'code_only' or (user_mode == 'auto' and any(keyword in user_question.lower() for keyword in ['كود', 'سكربت', 'برمجة', 'code', 'script', 'program', 'script'])):
                # فصل الكود عن الشرح
                code_content, explanation, language = separate_code_from_explanation(response)
                
                has_code = code_content and code_content.strip() and len(code_content.strip()) > 50
                has_explanation = explanation and explanation.strip() and len(explanation.strip()) > 10
                
                if has_code:
                    # حفظ الكود في ملف
                    code_file = safe_save_code_to_file(code_content, language, user_id)
                    
                    if code_file:
                        # تحديث رسالة المعالجة
                        safe_edit_message(message.chat.id, processing_msg_id, "✅ **تم استخراج الكود بنجاح!**\n\nجاري إرسال الملفات...")
                        
                        # إرسال ملف الكود
                        try:
                            with open(code_file, 'rb') as f:
                                bot.send_document(
                                    message.chat.id, 
                                    f, 
                                    caption=f"📁 **الكود المستخرج**\n\n🔧 **اللغة:** {language}\n📊 **حجم الكود:** {len(code_content)} حرف"
                                )
                            
                            # تنظيف ملف الكود
                            safe_delete_file(code_file)
                            
                        except Exception as e:
                            safe_edit_message(message.chat.id, processing_msg_id, f"❌ **خطأ في إرسال ملف الكود:** {str(e)}")
                    
                    
                    if has_explanation:
                        if len(explanation) <= 3500:
                            bot.send_message(
                                message.chat.id,
                                f"📝 **الشرح:**\n\n{explanation}",
                                parse_mode='Markdown'
                            )
                        else:
                            
                            explanation_file = safe_save_explanation_to_file(explanation, user_id)
                            if explanation_file:
                                with open(explanation_file, 'rb') as f:
                                    bot.send_document(
                                        message.chat.id,
                                        f,
                                        caption="📝 **الشرح الكامل**"
                                    )
                                safe_delete_file(explanation_file)
                            else:
                                
                                parts = split_long_message(explanation)
                                for i, part in enumerate(parts):
                                    if i == 0:
                                        bot.send_message(
                                            message.chat.id,
                                            f"📝 **الشرح** (الجزء {i+1} من {len(parts)}):\n\n{part}"
                                        )
                                    else:
                                        bot.send_message(
                                            message.chat.id,
                                            f"📝 **الشرح** (الجزء {i+1} من {len(parts)}):\n\n{part}"
                                        )
                    
                    
                    safe_delete_message(message.chat.id, processing_msg_id)
                    should_send_full_response = False
                    
                else:
                    safe_edit_message(
                        message.chat.id, 
                        processing_msg_id, 
                        "❌ **لم يتم العثور على كود في الرد**\n\nجاري إرسال الرد الكامل..."
                    )
                    
                    user_mode = 'full'
            
            
            if should_send_full_response:
                if len(response) <= 3500:
                    safe_edit_message(
                        message.chat.id, 
                        processing_msg_id, 
                        f"✅ **تمت المعالجة بنجاح!**\n\n{response}", 
                        parse_mode='Markdown'
                    )
                else:
                    safe_edit_message(
                        message.chat.id, 
                        processing_msg_id, 
                        "✅ **تمت المعالجة بنجاح!**\n\nالرد طويل جداً، جاري إرساله كملف..."
                    )
                    
                    
                    response_file = safe_save_explanation_to_file(response, user_id)
                    
                    if response_file:
                        try:
                            with open(response_file, 'rb') as f:
                                bot.send_document(
                                    message.chat.id, 
                                    f, 
                                    caption="📄 **الرد الكامل من DeepSeek AI**"
                                )
                            safe_delete_file(response_file)
                        except Exception as e:
                            
                            parts = split_long_message(response)
                            for i, part in enumerate(parts):
                                if i == 0:
                                    safe_edit_message(
                                        message.chat.id, 
                                        processing_msg_id, 
                                        f"✅ **تمت المعالجة بنجاح!** (الجزء {i+1} من {len(parts)})\n\n{part}"
                                    )
                                else:
                                    bot.send_message(
                                        message.chat.id,
                                        f"📄 **استكمال الرد** (الجزء {i+1} من {len(parts)})\n\n{part}"
                                    )
                    else:
                        safe_edit_message(
                            message.chat.id, 
                            processing_msg_id, 
                            "❌ **فشل في حفظ الرد في ملف**\n\nجاري إرسال الرد مقسماً..."
                        )
                        
                        parts = split_long_message(response)
                        for i, part in enumerate(parts):
                            if i == 0:
                                safe_edit_message(
                                    message.chat.id, 
                                    processing_msg_id, 
                                    f"✅ **تمت المعالجة بنجاح!** (الجزء {i+1} من {len(parts)})\n\n{part}"
                                )
                            else:
                                bot.send_message(
                                    message.chat.id,
                                    f"📄 **استكمال الرد** (الجزء {i+1} من {len(parts)})\n\n{part}"
                                )
                        
        else:
            safe_edit_message(
                message.chat.id, 
                processing_msg_id, 
                "❌ **فشل في الحصول على رد من DeepSeek**\n\nيرجى المحاولة مرة أخرى لاحقاً."
            )
        
    except Exception as e:
        error_msg = f"❌ حدث خطأ: {str(e)}"
        try:
            if processing_msg_id:
                safe_edit_message(message.chat.id, processing_msg_id, error_msg)
            else:
                bot.reply_to(message, error_msg)
        except:
            bot.reply_to(message, error_msg)
    
    finally:
        
        if user_id in user_files:
            file_info = user_files[user_id]
            safe_delete_file(file_info.get('file_path'))
            del user_files[user_id]

@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    """
    معالج للرسائل الأخرى
    """
    bot.reply_to(message, """
❓ **تعليمات غير واضحة**

📁 يرجى إرسال الملف أولاً، ثم أرسل سؤالك.
استخدم /help لمشاهدة التعليمات الكاملة.
    """)

# تشغيل البوت مع معالجة الأخطاء
def run_bot():
    print("🚀 بدء تشغيل بوت DeepSeek AI...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت: {e}")
        
        time.sleep(5)
        run_bot()

if __name__ == "__main__":
    run_bot()
