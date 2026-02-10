import threading
import requests
import time
import os
import asyncio
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

app = Flask(__name__)

# ================= CẤU HÌNH =================
# 1. Dán Token thật lấy từ @BotFather vào đây (Ví dụ: "7823456:AAFdgdg...")
TELEGRAM_TOKEN = "TOKEN" 

# 2. Thông tin bảo mật và định danh (Đã cập nhật Key mới của bạn)
API_KEY = "bomaylanhavua"
YOUR_CHAT_ID = "7346983056" 
# ============================================

def send_ngl_request(username, message):
    url = "https://ngl.link/api/submit"
    headers = {"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"}
    data = {"username": username, "question": message, "deviceId": "0000-0000"}
    try:
        res = requests.post(url, data=data, headers=headers, timeout=5)
        return res.status_code
    except: return 500

def task_background_spam(username, message, count):
    """Gửi spam ngầm và báo cáo về Telegram khi hoàn tất"""
    success = 0
    for _ in range(count):
        if send_ngl_request(username, message) == 200: success += 1
        time.sleep(0.3)
    
    # Gửi báo cáo kết quả trực tiếp tới ID 7346983056
    msg = f"✅ **GỬI SPAM HOÀN TẤT**\n\n👤 Target: `{username}`\n🚀 Thành công: `{success}/{count}`\n💬 Nội dung: {message}"
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={"chat_id": YOUR_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

@app.route('/')
def home(): return "Server NGL is Running!"

@app.route('/api/ngl/', methods=['GET'])
def api_handler():
    user, content, key = request.args.get('user'), request.args.get('content'), request.args.get('key')
    count_raw = request.args.get('count', 1)
    
    try:
        count = int(count_raw)
    except:
        count = 1
    
    if key != API_KEY: return jsonify({"status": "error", "msg": "Sai Key"}), 403
    
    # Kích hoạt luồng gửi ngầm
    threading.Thread(target=task_background_spam, args=(user, content, count)).start()
    return jsonify({"status": "processing", "info": f"Đang gửi {count} tin tới {user}"})

# --- LOGIC BOT TELEGRAM ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Chào Trung! Hệ thống đã sẵn sàng.\nID của bạn: `{update.effective_chat.id}`")

async def ngl_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Cú pháp: /ngl user | content | count
        parts = [p.strip() for p in " ".join(context.args).split("|")]
        user, content, count = parts[0], parts[1], int(parts[2])
        
        threading.Thread(target=task_background_spam, args=(user, content, count)).start()
        await update.message.reply_text(f"🚀 Đang gửi {count} tin nhắn tới {user}...")
    except:
        await update.message.reply_text("❌ Sai cú pháp!\nHãy nhập: `/ngl username | nội dung | số lần`", parse_mode="Markdown")

def run_bot():
    # Khởi tạo loop asyncio riêng cho bot để tránh lỗi signal trên Render
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("ngl", ngl_command))
    
    # stop_signals=False là bắt buộc để chạy được trên Web Service Render
    application.run_polling(stop_signals=False)

if __name__ == "__main__":
    # Chạy Bot trong luồng daemon để không chặn Flask
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Chạy Flask Server (Render sẽ cấp cổng PORT)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
