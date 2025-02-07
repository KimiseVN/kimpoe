import os
import discord
import pandas as pd
import asyncio
from discord.ext import commands

# Lấy Token từ biến môi trường
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# ID của kênh cho phép bot hoạt động (Thay bằng ID kênh Discord thực tế)
ALLOWED_CHANNEL_ID = 1337203470167576607  # Thay bằng ID kênh của bạn

# Dictionary lưu ID tin nhắn thông báo để xóa khi rời kênh
welcome_messages = {}

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
intents.members = True  # Bật để theo dõi thành viên vào/ra kênh
intents.typing = False
intents.presences = False

# Khởi tạo bot với prefix "!"
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot đã kết nối với Discord! Logged in as {bot.user}')
    print(f'🔹 Tổng số Skill hiện tại: {len(data)}')

@bot.event
async def on_voice_state_update(member, before, after):
    """Kiểm tra khi người dùng vào/rời kênh"""
    channel = bot.get_channel(ALLOWED_CHANNEL_ID)

    if after.channel and after.channel.id == ALLOWED_CHANNEL_ID:
        # Khi người dùng vào kênh, bot gửi thông báo
        if member.id not in welcome_messages:
            total_skills = len(data)
            welcome_message = await channel.send(
                f"📢 **Chào {member.name}!**\n"
                f"📌 Có tổng cộng **{total_skills} Skill** trong dữ liệu.\n"
                "✏️ Gửi tên Skill muốn kiểm tra!"
            )
            welcome_messages[member.id] = welcome_message.id  # Lưu ID tin nhắn để xóa sau

    elif before.channel and before.channel.id == ALLOWED_CHANNEL_ID:
        # Khi người dùng rời kênh, bot xóa thông báo
        if member.id in welcome_messages:
            try:
                msg = await channel.fetch_message(welcome_messages[member.id])
                await msg.delete()
            except discord.NotFound:
                pass  # Tin nhắn có thể đã bị xóa trước đó
            del welcome_messages[member.id]  # Xóa khỏi danh sách theo dõi

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
            confirm_msg = await ctx.send(f"🧹 **Đã xóa {len(deleted)} tin nhắn trong kênh này!**")
            await asyncio.sleep(5)
            await confirm_msg.delete()
        except discord.Forbidden:
            await ctx.send("❌ **Bot không có quyền xóa tin nhắn!** Hãy kiểm tra quyền 'Manage Messages'.")
        except discord.HTTPException:
            await ctx.send("❌ **Lỗi khi xóa tin nhắn!** Hãy thử lại sau.")
    else:
        await ctx.send("❌ **Lệnh này chỉ có thể sử dụng trong kênh được chỉ định.**")

bot.run(TOKEN)
