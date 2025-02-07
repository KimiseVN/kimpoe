# Sử dụng base image có Python và Tesseract
FROM python:3.12

# Cập nhật hệ thống và cài đặt Tesseract OCR
RUN apt-get update && apt-get install -y tesseract-ocr libtesseract-dev

# Cài đặt thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn vào container
COPY . .

# Chạy bot
CMD ["python", "bot.py"]
