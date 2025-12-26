import telebot
from telebot import types
import random
import json
import os
import unicodedata
import re
from datetime import datetime

# ===== CONFIG =====
BOT_TOKEN = "token"  # Thay bằng token thật từ BotFather
DATA_FILE = "user_data.json"

bot = telebot.TeleBot(BOT_TOKEN)

# ===== UTIL =====
def remove_accents(text):
    """Loại bỏ dấu tiếng Việt"""
    nfd = unicodedata.normalize('NFD', text)
    return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')

def generate_username(full_name):
    """Tạo username từ họ tên"""
    username = remove_accents(full_name.lower())
    username = username.replace(" ", "")
    random_num = random.randint(10, 99)
    username = f"{username}{random_num}"
    return username

def generate_password(full_name):
    """Tạo mật khẩu từ họ tên + ký tự đặc biệt"""
    base = remove_accents(full_name.lower())
    base = base.replace(" ", "")
    special_chars = "!@#$%^&*"
    password = base + ''.join(random.choices(special_chars, k=random.randint(2, 3)))
    password += str(random.randint(100, 999))
    return password

def generate_random_birthday():
    """Tạo ngày sinh ngẫu nhiên từ 1970-2005"""
    year = random.randint(1970, 2005)
    month = random.randint(1, 12)
    
    if month in [1, 3, 5, 7, 8, 10, 12]:
        max_day = 31
    elif month in [4, 6, 9, 11]:
        max_day = 30
    else:
        if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            max_day = 29
        else:
            max_day = 28
    
    day = random.randint(1, max_day)
    return f"{day:02d}/{month:02d}/{year}"

def parse_input(text):
    """Phân tích input thành họ tên, số điện thoại, số tài khoản"""
    tokens = text.split()
    numbers = []
    words = []
    
    for token in tokens:
        clean_token = re.sub(r'[^\w\sÀ-ỹ]', '', token)
        
        if clean_token.isdigit():
            numbers.append(clean_token)
        elif clean_token:
            words.append(clean_token)
    
    full_name = ' '.join(words)
    phone = None
    account_number = None
    
    for num in numbers:
        if len(num) >= 9 and len(num) <= 11 and not phone:
            phone = num
        elif not account_number:
            account_number = num
    
    if len(numbers) == 1:
        phone = numbers[0]
        account_number = None
    elif len(numbers) >= 2:
        if not phone or not account_number:
            sorted_numbers = sorted(numbers, key=len)
            if len(sorted_numbers) >= 2:
                phone = sorted_numbers[0] if len(sorted_numbers[0]) <= 11 else sorted_numbers[1]
                account_number = sorted_numbers[-1]
            else:
                phone = sorted_numbers[0]
    
    return full_name, phone, account_number

def save_data(user_data):
    """Lưu dữ liệu vào file JSON"""
    existing_data = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except:
                existing_data = []
    
    existing_data.append(user_data)
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)

# ===== HANDLERS =====
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_create = types.KeyboardButton("🎲 Tạo tài khoản mới")
    btn_view = types.KeyboardButton("📋 Xem danh sách")
    markup.add(btn_create, btn_view)
    
    bot.send_message(
        message.chat.id,
        "👋 Chào mừng đến với Bot tạo tài khoản!\n\n"
        "📌 Cách nhập: Gõ tất cả thông tin vào 1 dòng\n"
        "📌 Ví dụ: Nguyễn Văn A 0123456789 1234567890\n"
        "📌 Hoặc: 0123456789 Nguyễn Văn A 1234567890\n\n"
        "⚡ Bot sẽ tự động nhận diện họ tên và số!\n\n"
        "Chọn chức năng bạn muốn sử dụng:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == "🎲 Tạo tài khoản mới")
def create_account(message):
    bot.send_message(
        message.chat.id,
        "📝 Nhập thông tin (gõ tự do, bot sẽ tự phân tích):\n\n"
        "Ví dụ:\n"
        "• Nguyễn Văn A 0123456789 1234567890\n"
        "• Trần Thị B 0987654321 9876543210\n"
        "• 0912345678 Lê Văn C 1122334455\n\n"
        "💡 Thứ tự không quan trọng, bot sẽ tự nhận diện!"
    )

@bot.message_handler(func=lambda message: message.text not in ["📋 Xem danh sách", "🎲 Tạo tài khoản mới"] and not message.text.startswith('/'))
def process_input(message):
    chat_id = message.chat.id
    input_text = message.text.strip()
    
    try:
        # Phân tích input
        full_name, phone, account_number = parse_input(input_text)
        
        # Kiểm tra thông tin
        if not full_name:
            bot.send_message(
                chat_id,
                "❌ Không tìm thấy họ tên! Vui lòng nhập lại."
            )
            return
        
        if not phone:
            phone = "Chưa có"
        
        if not account_number:
            account_number = "Chưa có"
        
        # Tạo username và password
        username = generate_username(full_name)
        password = generate_password(full_name)
        birthday = generate_random_birthday()
        
        # Lưu thông tin
        user_data = {
            'username': username,
            'password': password,
            'phone': phone,
            'account_number': account_number,
            'full_name': full_name,
            'birthday': birthday,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        save_data(user_data)
        
        # Xuất kết quả
        output_line = f"{username}|{password}|{phone}|{account_number}|{full_name}|{birthday}"
        
        output = (
            f"✅ TẠO TÀI KHOẢN THÀNH CÔNG!\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"`{output_line}`\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"📋 Chi tiết:\n"
            f"🔑 Tài khoản: `{username}`\n"
            f"🔐 Mật khẩu: `{password}`\n"
            f"📞 Số điện thoại: {phone}\n"
            f"🏦 Số TK: {account_number}\n"
            f"👤 Họ và tên: {full_name}\n"
            f"🎂 Ngày sinh: {birthday}\n\n"
            f"💡 _Nhấn vào các đoạn có dấu ` để sao chép_"
        )
        
        bot.send_message(chat_id, output, parse_mode='Markdown')
        
    except Exception as e:
        bot.send_message(
            chat_id,
            f"❌ Có lỗi xảy ra: {str(e)}\n\n"
            "Vui lòng nhập lại thông tin!"
        )

@bot.message_handler(func=lambda message: message.text == "📋 Xem danh sách")
def view_list(message):
    if not os.path.exists(DATA_FILE):
        bot.send_message(message.chat.id, "📭 Chưa có dữ liệu nào được lưu.")
        return
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except:
            bot.send_message(message.chat.id, "📭 Chưa có dữ liệu nào được lưu.")
            return
    
    if not data:
        bot.send_message(message.chat.id, "📭 Chưa có dữ liệu nào được lưu.")
        return
    
    # Hiển thị 10 tài khoản gần nhất
    recent_data = data[-10:] if len(data) > 10 else data
    
    response = "📋 DANH SÁCH TÀI KHOẢN GẦN NHẤT:\n\n"
    for i, item in enumerate(recent_data, 1):
        line = f"{item['username']}|{item['password']}|{item['phone']}|{item['account_number']}|{item['full_name']}|{item['birthday']}"
        response += f"━━━ #{i} ━━━\n`{line}`\n\n"
    
    response += f"\n💡 _Tổng cộng: {len(data)} tài khoản_"
    
    bot.send_message(message.chat.id, response, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.send_message(
        message.chat.id,
        "❓ Vui lòng chọn chức năng từ menu bên dưới."
    )

# ===== RUN =====
if __name__ == "__main__":
    print("Bot đang chạy...")
    bot.polling(none_stop=True)
    
