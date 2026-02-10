import threading
import requests
import time
import os
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

app = Flask(__name__)

# --- CẤU HÌNH ---
# Thay Token bạn lấy từ @BotFather vào đây
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE" 
# Key bảo mật cho API của bạn (tự đặt tùy ý)
API_KEY = "shopaccvanquoc"

def send_ngl(username, message):
    url = f"https://ngl.link/api/submit"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }
    data = {
        "username": username,
        "question": message,
        "deviceId": "00000000-0000-0000-0000-000000000000"
    }
    try:
        res = requests.post(url, data=data, headers=headers, timeout=10)
        return res.status_code
    except:
        return 500

# --- PHẦN 1: API CHO PHÍM TẮT (FLASK) ---
@app.route('/')
def home():
    return "Server is running!"

@app.route('/api/ngl/', methods=['GET'])
def api_handler():
    user = request.args.get('user')
    content = request.args.get('content')
    count = int(request.args.get('count', 1))
    key = request.args.get('key')

    if key != API_KEY:
        return jsonify({"error": "Wrong API Key"}), 403

    success = 0
    for _ in range(count):
        if send_ngl(user, content) == 200:
            success += 1
        time.sleep(0.3) # Delay nhẹ để tránh bị block

    return jsonify({"status": "success", "sent": success, "target": user})

# --- PHẦN 2: TELEGRAM BOT ---
async def ngl_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Cú pháp: /ngl username | content | count
        input_str = " ".join(context.args)
        parts = [p.strip() for p in input_str.split("|")]
        
        user = parts[0]
        content = parts[1]
        count = int(parts[2]) if len(parts) > 2 else 1

        await update.message.reply_text(f"🚀 Đang gửi {count} tin tới {user}...")
        
        success = 0
        for _ in range(count):
            if send_ngl(user, content) == 200:
                success += 1
            time.sleep(0.2)

        await update.message.reply_text(f"✅ Xong! Thành công {success}/{count}.")
    except:
        await update.message.reply_text("❌ Lỗi! Cú pháp đúng: /ngl username | nội dung | số lần")

def run_telegram_bot():
    # Tạo bot và thêm lệnh /ngl
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("ngl", ngl_command))
    application.run_polling(close_loop=False)

# --- CHẠY CẢ HAI ---
if __name__ == "__main__":
    # Chạy Telegram Bot ở luồng phụ (Thread)
    t = threading.Thread(target=run_telegram_bot)
    t.start()
    
    # Chạy Flask API ở luồng chính
    # Render sẽ dùng cổng mặc định qua biến môi trường PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
