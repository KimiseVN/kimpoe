import os
import discord
import pandas as pd
import asyncio
from discord.ext import commands
from googletrans import Translator  # Dùng googletrans để dịch

# Lấy Token từ biến môi trường
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# ID của kênh Discord mà bot được phép hoạt động
ALLOWED_CHANNEL_ID = 1337203470167576607  # Cập nhật ID kênh Discord

# Tên file dữ liệu Excel
EXCEL_FILE = "passive_skills.xlsx"

# Danh sách từ khóa cần giữ nguyên khi dịch
EXCLUDED_WORDS = [
    "Critical Strike", "Spell Damage", "Fire Resistance", "Cold Resistance", "Life Leech",
    "Strength", "Dexterity", "Intelligence", "Energy Shield", "Spirit", "Armour", "Evasion",
    "Accuracy", "Physical Damage", "Critical Damage Bonus", "Critical Chance", "Life", "Mana",
    "Attributes", "Lightning Damage", "Cold Damage", "Fire Damage"
]

# ID của tin nhắn ghim (sẽ cập nhật sau lần chạy đầu)
PINNED_MESSAGE_ID = None  

# Khởi tạo bộ dịch
translator = Translator()

# Kiểm tra và tạo file Excel nếu chưa tồn tại
if not os.path.exists(EXCEL_FILE):
    df = pd.DataFrame(columns=["Name", "Type", "Effect"])
    df.to_excel(EXCEL_FILE, index=False)
    print("✅ Đã tạo file passive_skills.xlsx")

def load_data():
    """Load dữ liệu từ file Excel"""
    return pd.read_excel(EXCEL_FILE).fillna("")  # Xử lý giá trị NaN nếu có

data = load_data()

# Đếm tổng số lượng Skill
def get_total_skill_count():
    return len(data)

# Hàm dịch Google Translate nhưng giữ nguyên một số từ
def translate_with_exclusions(text, excluded_words):
    """Dịch văn bản sang tiếng Việt nhưng giữ nguyên một số từ"""
    replacement_map = {}

    # Thay thế các từ cần giữ nguyên bằng mã đặc biệt
    for i, word in enumerate(excluded_words):
        placeholder = f"{{EXCLUDE_{i}}}"
        replacement_map[placeholder] = word
        text = text.replace(word, placeholder)

    # Dịch văn bản
    translated_text = translator.translate(text, src="en", dest="vi").text

    # Thay thế lại các từ đã giữ nguyên
    for placeholder, word in replacement_map.items():
        translated_text = translated_text.replace(placeholder, word)

    return translated_text

# Thiết lập intents cho bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.presences = False
intents.members = False

# Khởi tạo bot với prefix "!"
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    """Bot đã khởi động thành công"""
    print(f'✅ Bot đã kết nối với Discord! Logged in as {bot.user}')
    print(f'🔹 Tổng số Skill hiện tại: {get_total_skill_count()}')
    
    # Đảm bảo tin nhắn ghim được cập nhật đúng
    channel = bot.get_channel(ALLOWED_CHANNEL_ID)
    if channel:
        await update_pinned_message(channel)

async def update_pinned_message(channel):
    """Cập nhật tin nhắn ghim với tổng số Skill"""
    global PINNED_MESSAGE_ID

    skill_count = get_total_skill_count()
    message_content = f"📌 **Có tổng cộng {skill_count} Skill**\n📝 Hãy nhập chính xác tên Skill để kiểm tra!"

    async for message in channel.history(limit=50):
        if message.pinned:
            await message.edit(content=message_content)
            PINNED_MESSAGE_ID = message.id
            return
    
    # Nếu không có tin nhắn ghim, tạo mới và ghim lại
    new_message = await channel.send(message_content)
    await new_message.pin()
    PINNED_MESSAGE_ID = new_message.id

@bot.event
async def on_message(message):
    """Chỉ xử lý tin nhắn trong kênh được phép"""
    if message.author == bot.user:
        return
    if message.channel.id != ALLOWED_CHANNEL_ID:
        return  # Bỏ qua tin nhắn nếu không phải kênh cho phép

    # Xử lý lệnh bot trước
    await bot.process_commands(message)

    # Chuẩn hóa tên Skill để tìm kiếm chính xác
    skill_query = message.content.strip().lower()
    skill_results = data[data["Name"].str.strip().str.lower() == skill_query]  # Chỉ tìm tên Skill chính xác

    if not skill_results.empty:
        row = skill_results.iloc[0]  # Lấy đúng 1 kết quả khớp
        skill_name = row["Name"]
        skill_type = row["Type"]
        skill_effect = row["Effect"]

        # Dịch phần Effect sang Tiếng Việt nhưng giữ nguyên thuật ngữ
        translated_effect = translate_with_exclusions(skill_effect, EXCLUDED_WORDS)

        response = (
            f'**{skill_name}** ({skill_type})\n'
            f'📜 **Effect (EN):** {skill_effect}\n'
            f'🇻🇳 **Effect (VI):** {translated_effect}'
        )
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
            await update_pinned_message(ctx.channel)  # Cập nhật tin nhắn ghim sau khi xóa
        except discord.Forbidden:
            await ctx.send("❌ Bot không có quyền xóa tin nhắn! Hãy kiểm tra quyền 'Manage Messages'.")
        except discord.HTTPException:
            await ctx.send("❌ Lỗi khi xóa tin nhắn! Hãy thử lại sau.")
    else:
        await ctx.send("❌ Lệnh này chỉ có thể sử dụng trong kênh được chỉ định.")

bot.run(TOKEN)
