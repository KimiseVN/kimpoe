import discord
import pandas as pd
import os
import asyncio  # Import asyncio để dùng sleep
from discord.ext import commands

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

# Lưu lịch sử tin nhắn để xóa sau 30 phút
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

        # Tô màu đỏ cho tên skill bằng Markdown `[diff]`
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

@bot.command(name="update_excel")
async def update_excel(ctx):
    """Cập nhật danh sách từ file Excel"""
    global data
    try:
        data = load_data()
        await ctx.send(f"🔄 Danh sách Skill đã được cập nhật từ file Excel! 📜 Tổng số Skill: {len(data)}")
    except Exception as e:
        await ctx.send(f"❌ Lỗi khi cập nhật từ Excel: {str(e)}")

@bot.command(name="listskills")
async def list_skills(ctx):
    """Liệt kê tất cả Passive Skills có trong danh sách"""
    if data.empty:
        await ctx.send("⚠️ Không có Skill nào trong danh sách. Hãy kiểm tra file Excel và cập nhật lại bằng `!update_excel`.")
        return

    skills_list = data["Name"].tolist()
    chunk_size = 50  # Mỗi tin nhắn chứa tối đa 50 skill (để tránh vượt 4000 ký tự)
    
    await ctx.send("📜 **Danh sách Skill:**")
    
    for i in range(0, len(skills_list), chunk_size):
        chunk = "\n".join(skills_list[i:i + chunk_size])
        await ctx.send(f"```{chunk}```")

# Chạy bot với Token của bạn
TOKEN = "MTMzNzE5OTg4MTg1MjU1NTQ1OA.G99XF7.QFZE223BJru5j-5cB3pkzzax_DLFyFfE0QKCCE"
bot.run(TOKEN)
