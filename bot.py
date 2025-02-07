import os
import discord
import pandas as pd
import pytesseract
from PIL import Image
import requests
from io import BytesIO
from googletrans import Translator
from discord.ext import commands

# Lấy Token từ biến môi trường
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# ID của kênh được phép bot hoạt động
ALLOWED_CHANNEL_ID = 1337203470167576607  # Thay bằng ID kênh của bạn

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

# Khởi tạo bộ dịch Google Translate
translator = Translator()

def translate_text(text):
    """Dịch văn bản từ tiếng Anh sang tiếng Việt"""
    translated_text = translator.translate(text, src="en", dest="vi").text
    return translated_text

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
async def on_message(message):
    """Chỉ xử lý tin nhắn trong kênh được phép"""
    if message.author == bot.user:
        return
    if message.channel.id != ALLOWED_CHANNEL_ID:
        return  # Bỏ qua tin nhắn nếu không phải kênh cho phép

    # Xử lý lệnh bot trước
    await bot.process_commands(message)

    # Nếu tin nhắn có ảnh, tiến hành trích xuất văn bản
    if message.attachments:
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ["png", "jpg", "jpeg"]):
                await process_image(message, attachment)

async def process_image(message, attachment):
    """Trích xuất văn bản từ ảnh và tìm kiếm Skill"""
    response = requests.get(attachment.url)
    img = Image.open(BytesIO(response.content))

    # Sử dụng Tesseract OCR để nhận diện văn bản
    extracted_text = pytesseract.image_to_string(img)

    # Lọc danh sách Skill từ văn bản OCR
    skill_names = []
    for line in extracted_text.split("\n"):
        line = line.strip()
        if line.lower().startswith("allocates "):
            skill_name = line.replace("Allocates ", "").strip()
            skill_names.append(skill_name)

    if not skill_names:
        await message.channel.send("❌ Không tìm thấy Skill nào trong ảnh!")
        return

    # Tạo phản hồi với thông tin Skill tìm được
    response_text = "**📜 Các Skill tìm thấy:**\n"
    for skill_name in skill_names:
        skill_info = data[data["Name"].str.strip().str.lower() == skill_name.lower()]
        if not skill_info.empty:
            skill_type = skill_info.iloc[0]["Type"]
            skill_effect = skill_info.iloc[0]["Effect"]
            skill_effect_vi = translate_text(skill_effect)

            response_text += (
                f'\n🔹 **{skill_name}** ({skill_type})\n'
                f'📜 **Effect (EN):** {skill_effect}\n'
                f'🇻🇳 **Effect (VI):** ||{skill_effect_vi}||\n'
            )
        else:
            response_text += f'\n❌ **{skill_name}** - Không có trong dữ liệu!\n'

    await message.channel.send(response_text)

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
