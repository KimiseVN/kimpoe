import os
import discord
import pandas as pd
import asyncio
from discord.ext import commands

# Lấy Token từ biến môi trường
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# ID của kênh được phép bot hoạt động (Thay bằng ID kênh của bạn)
ALLOWED_CHANNEL_ID = 1337203470167576607  # Thay bằng ID kênh thực tế của bạn

# Tên file dữ liệu Excel
EXCEL_FILE = "passive_skills.xlsx"

# Kiểm tra và tạo file Excel nếu chưa tồn tại
if not os.path.exists(EXCEL_FILE):
    df = pd.DataFrame(columns=["Name", "Type", "Effect"])
    df.to_excel(EXCEL_FILE, index=False)
    print("✅ Đã tạo file passive_skills.xlsx")

def load_data():
    """Load dữ liệu từ file Excel"""
    return pd.read_excel(EXCEL_FILE)

data = load_data()

# Lưu lịch sử tin nhắn để xóa sau 24 giờ
history_messages = []

# Thiết lập intents cho bot
intents = discord.Intents.default()
intents.message_content = True  # Cho phép bot đọc nội dung tin nhắn

# Khởi tạo bot với prefix "!"
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot đã kết nối với Discord! Logged in as {bot.user}')
    print(f'🔹 Tổng số Skill hiện tại: {len(data)}')

@bot.event
async def on_message(message):
    """Lắng nghe tất cả tin nhắn trong server và tự động tìm skill nếu có trong danh sách."""
    if message.author == bot.user:  # Bỏ qua tin nhắn của bot để tránh loop vô hạn
        return

    skill_name = message.content.strip()  # Lấy nội dung tin nhắn của người dùng
    skill_info = data[data["Name"].str.lower() == skill_name.lower()]

    if not skill_info.empty:
        skill_type = skill_info.iloc[0]["Type"]
        skill_effect = skill_info.iloc[0]["Effect"]

        # Chỉ in đậm tên skill
        response = f'**{skill_name}** ({skill_type})\n{skill_effect}'
        msg = await message.channel.send(response)

        # Lưu tin nhắn để xóa sau 24 giờ
        history_messages.append(msg)

        # Tự động xóa sau 24 giờ
        await asyncio.sleep(86400)
        await msg.delete()
        history_messages.remove(msg)
    else:
        msg = await message.channel.send("❌ Không tìm thấy! Kiểm tra lại tên Skill xem đã chính xác chưa?")
        
        # Lưu tin nhắn để xóa sau 24 giờ
        history_messages.append(msg)

        # Tự động xóa sau 24 giờ
        await asyncio.sleep(86400)
        await msg.delete()
        history_messages.remove(msg)

    await bot.process_commands(message)  # Đảm bảo các lệnh khác vẫn hoạt động

bot.run(TOKEN)
