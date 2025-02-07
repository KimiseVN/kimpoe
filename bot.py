import os
import discord
import pandas as pd
import asyncio
from discord.ext import commands
from googletrans import Translator

# Lấy Token từ biến môi trường
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# ID của kênh Discord mà bot được phép hoạt động
ALLOWED_CHANNEL_ID = 1337203470167576607

# Tên file dữ liệu Excel
EXCEL_FILE = "passive_skills.xlsx"

# Danh sách từ khóa cần giữ nguyên khi dịch
EXCLUDED_WORDS = [
    "Critical Strike", "Spell Damage", "Fire Resistance", "Cold Resistance", "Life Leech",
    "Strength", "Dexterity", "Intelligence", "Energy Shield", "Spirit", "Armour", "Evasion",
    "Accuracy", "Physical Damage", "Critical Damage Bonus", "Critical Chance", "Life", "Mana",
    "Attributes", "Lightning Damage", "Cold Damage", "Fire Damage"
]

# Khởi tạo bộ dịch
translator = Translator()

# Load dữ liệu từ file Excel
def load_data():
    return pd.read_excel(EXCEL_FILE).fillna("")

data = load_data()

# Đếm tổng số lượng Skill
def get_total_skill_count():
    return len(data)

# **Sửa lại hàm dịch để tránh lỗi placeholder hiển thị**
def translate_with_exclusions(text, excluded_words):
    """Dịch văn bản sang tiếng Việt nhưng giữ nguyên một số thuật ngữ"""
    replacement_map = {}

    # Thay thế các từ khóa cần giữ nguyên bằng placeholder đặc biệt
    for word in excluded_words:
        placeholder = f"#EXCLUDE#{word}#EXCLUDE#"
        replacement_map[placeholder] = word
        text = text.replace(word, placeholder)

    # Gửi văn bản qua Google Translate
    translated_text = translator.translate(text, src="en", dest="vi").text

    # Thay thế lại các thuật ngữ về trạng thái ban đầu
    for placeholder, word in replacement_map.items():
        translated_text = translated_text.replace(placeholder, word)

    return translated_text

# Thiết lập intents cho bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.presences = False
intents.members = False

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot đã kết nối với Discord! Logged in as {bot.user}')
    print(f'🔹 Tổng số Skill hiện tại: {get_total_skill_count()}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.channel.id != ALLOWED_CHANNEL_ID:
        return  

    await bot.process_commands(message)

    # Chuẩn hóa tên Skill để tìm kiếm chính xác
    skill_query = message.content.strip().lower()
    skill_results = data[data["Name"].str.strip().str.lower() == skill_query]

    if not skill_results.empty:
        row = skill_results.iloc[0]
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
        if not message.content.startswith("!"):
            await message.channel.send("❌ Không tìm thấy Skill! Kiểm tra lại xem đã nhập đúng chưa.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 100):
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
