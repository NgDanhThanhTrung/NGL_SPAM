import threading
import requests
import time
import os
from flask import Flask, request, jsonify
from telegram import Bot
from telegram.ext import Application, CommandHandler, ContextTypes

app = Flask(__name__)

# ================= CẤU HÌNH =================
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN_HERE" 
API_KEY = "ngdanhthanhtrung"
# ID của bạn để nhận thông báo hoàn thành
YOUR_CHAT_ID = "YOUR_PERSONAL_CHAT_ID" 
# ============================================

# Khởi tạo bot để gửi thông báo chủ động
bot_notifier = Bot(token=TELEGRAM_TOKEN)

def send_ngl_request(username, message):
    url = "https://ngl.link/api/submit"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }
    data = {
        "username": username,
        "question": message,
        "deviceId": "0000-0000-0000-0000"
    }
    try:
        res = requests.post(url, data=data, headers=headers, timeout=5)
        return res.status_code
    except:
        return 500

def task_background_spam(username, message, count):
    """Tiến trình chạy ngầm gửi tin nhắn và báo cáo qua Telegram"""
    success = 0
    for _ in range(count):
        if send_ngl_request(username, message) == 200:
            success += 1
        time.sleep(0.3) # Delay để không bị NGL block IP server
    
    # Gửi thông báo về Telegram khi xong
    msg = f"✅ **HOÀN THÀNH NHIỆM VỤ**\n\n👤 Mục tiêu: `{username}`\n🚀 Thành công: `{success}/{count}`\n💬 Nội dung: {message}"
    try:
        # Gửi request trực tiếp đến API Telegram để thông báo
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(api_url, json={"chat_id": YOUR_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"Lỗi gửi thông báo: {e}")

# --- CỔNG HTTP (Dành cho Render và Phím tắt) ---
@app.route('/')
def home():
    return "API NGL & Bot Telegram is Running!"

@app.route('/api/ngl/', methods=['GET'])
def api_handler():
    user = request.args.get('user')
    content = request.args.get('content')
    count = int(request.args.get('count', 1))
    key = request.args.get('key')

    if key != API_KEY:
        return jsonify({"status": "error", "message": "Sai Key"}), 403

    # Kích hoạt luồng ngầm ngay lập tức
    thread = threading.Thread(target=task_background_spam, args=(user, content, count))
    thread.start()

    return jsonify({
        "status": "processing",
        "message": f"Đã bắt đầu gửi {count} tin tới {user}. Kết quả sẽ báo qua Telegram."
    })

# --- CẤU HÌNH BOT TELEGRAM ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"ID của bạn: `{update.effective_chat.id}`\nHãy điền ID này vào code.")

async def ngl_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        input_str = " ".join(context.args)
        parts = [p.strip() for p in input_str.split("|")]
        user, content = parts[0], parts[1]
        count = int(parts[2]) if len(parts) > 2 else 1

        thread = threading.Thread(target=task_background_spam, args=(user, content, count))
        thread.start()

        await update.message.reply_text(f"🚀 Đang gửi {count} tin tới {user}...")
    except:
        await update.message.reply_text("Cú pháp: `/ngl user | nội dung | số lần`", parse_mode="Markdown")

def run_bot():
    """Hàm khởi chạy Bot"""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("ngl", ngl_command))
    application.run_polling(close_loop=False)

# --- CHẠY SERVER ---
if __name__ == "__main__":
    # Khởi chạy Bot Telegram trong luồng riêng
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Render yêu cầu dùng cổng PORT từ biến môi trường
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
