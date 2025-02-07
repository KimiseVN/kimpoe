import os
import discord
import pandas as pd
import asyncio
from discord.ext import commands

# Lấy Token từ biến môi trường
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# ID của kênh Discord mà bot được phép hoạt động
ALLOWED_CHANNEL_ID = 1337203470167576607  # Cập nhật ID mới

# Tên file dữ liệu Excel
EXCEL_FILE = "passive_skills.xlsx"

# Kiểm tra và tạo file Excel nếu chưa tồn tại
if not os.path.exists(EXCEL_FILE):
    df = pd.DataFrame(columns=["Name", "Type", "Effect"])
    df.to_excel(EXCEL_FILE, index=False)
    print("✅ Đã tạo file passive_skills.xlsx")

def load_data():
    """Load dữ liệu từ file Excel"""
    return pd.read_excel(EXCEL_FILE).fillna("")  # Xử lý giá trị NaN nếu có

data = load_data()

# Thiết lập intents cho bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.presences = True
intents.members = True  # Cần bật "Server Members Intent"

# Khởi tạo bot với prefix "!"
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    """Bot đã khởi động thành công"""
    print(f'✅ Bot đã kết nối với Discord! Logged in as {bot.user}')
    print(f'🔹 Tổng số Skill hiện tại: {len(data)}')

@bot.event
async def on_member_update(before, after):
    """Gửi tin nhắn chào mừng khi thành viên vào kênh"""
    guild = after.guild
    member = after

    # Lấy kênh văn bản Discord
    channel = guild.get_channel(ALLOWED_CHANNEL_ID)

    # Kiểm tra nếu người dùng đang xem kênh
    if after.activity and hasattr(after.activity, "name"):
        if after.activity.name == "Reading Messages" and channel:
            skill_count = len(data)
            welcome_message = await channel.send(
                f"👋 **Chào {member.mention}!**\n📌 Hiện tại có **{skill_count}** Skill Not.\n✍️ Gửi tên Skill để kiểm tra ngay!"
            )
            await asyncio.sleep(30)  # Xóa tin nhắn sau 30 giây
            await welcome_message.delete()

@bot.event
async def on_message(message):
    """Chỉ xử lý tin nhắn trong kênh được phép"""
    if message.author == bot.user:
        return
    if message.channel.id != ALLOWED_CHANNEL_ID:
        return  # Bỏ qua tin nhắn nếu không phải kênh cho phép

    # Xử lý lệnh bot trước (fix lỗi !clear)
    await bot.process_commands(message)

    # Chuẩn hóa tên Skill để tìm kiếm chính xác
    skill_name = message.content.strip().lower()
    skill_info = data[data["Name"].str.strip().str.lower() == skill_name]

    if not skill_info.empty:
        skill_type = skill_info.iloc[0]["Type"]
        skill_effect = skill_info.iloc[0]["Effect"]
        response = f'**{skill_name.capitalize()}** ({skill_type})\n{skill_effect}'
        await message.channel.send(response)
    else:
        if not message.content.startswith("!"):  # Tránh báo lỗi khi gõ lệnh
            await message.channel.send("❌ Không tìm thấy Skill! Kiểm tra lại xem đã nhập đúng chưa.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 100):
    """Xóa toàn bộ tin nhắn trong kênh Chatbot"""
    if ctx.channel.id == ALLOWED_CHANNEL_ID:
        try:
            deleted = await ctx.channel.purge(limit=amount)
            await ctx.send(f"🧹 **Đã xóa {len(deleted)} tin nhắn trong kênh này!**", delete_after=5)
        except discord.Forbidden:
            await ctx.send("❌ Bot không có quyền xóa tin nhắn! Hãy kiểm tra quyền 'Manage Messages'.")
        except discord.HTTPException:
            await ctx.send("❌ Lỗi khi xóa tin nhắn! Hãy thử lại sau.")
    else:
        await ctx.send("❌ Lệnh này chỉ có thể sử dụng trong kênh được chỉ định.")

bot.run(TOKEN)
