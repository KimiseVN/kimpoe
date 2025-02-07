import os
import discord
import pandas as pd
import asyncio
from discord.ext import commands

# Lấy Token từ biến môi trường
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# ID của kênh được phép bot hoạt động (Thay bằng ID kênh thực tế của bạn)
ALLOWED_CHANNEL_ID = 1337203470167576607  # Thay bằng ID kênh Discord của bạn

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

# Thiết lập intents cho bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.typing = False
intents.presences = False

# Khởi tạo bot với prefix "!"
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot đã kết nối với Discord! Logged in as {bot.user}')
    print(f'🔹 Tổng số Skill hiện tại: {len(data)}')

@bot.event
async def on_guild_channel_update(before, after):
    """Khi mở kênh có bot, gửi thông báo hướng dẫn"""
    if after.id == ALLOWED_CHANNEL_ID:
        await after.send("📌 **Đây là kênh để Check Passive Skill**\n"
                         "💡 Copy Paste hoặc nhập chính xác tên Skill Point để kiểm tra.")

@bot.event
async def on_message(message):
    """Chỉ xử lý tin nhắn trong kênh được phép"""
    if message.author == bot.user:
        return
    if message.channel.id != ALLOWED_CHANNEL_ID:
        return  # Bỏ qua tin nhắn nếu không phải kênh cho phép

    skill_name = message.content.strip()
    skill_info = data[data["Name"].str.lower() == skill_name.lower()]

    if not skill_info.empty:
        skill_type = skill_info.iloc[0]["Type"]
        skill_effect = skill_info.iloc[0]["Effect"]
        response = f'**{skill_name}** ({skill_type})\n{skill_effect}'
        await message.channel.send(response)
    else:
        await message.channel.send("❌ Không tìm thấy Skill! Kiểm tra lại xem đã nhập đúng chưa.")

    await bot.process_commands(message)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx):
    """Xóa toàn bộ tin nhắn trong kênh Chatbot"""
    if ctx.channel.id == ALLOWED_CHANNEL_ID:
        await ctx.channel.purge()
        await ctx.send("🧹 **Đã xóa toàn bộ tin nhắn trong kênh này!**", delete_after=5)
    else:
        await ctx.send("❌ Lệnh này chỉ có thể sử dụng trong kênh được chỉ định.")

bot.run(TOKEN)
