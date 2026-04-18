# استفاده از نسخه سبک و رسمی پایتون
FROM python:3.11-slim

# تنظیم پوشه کاری داخل کانتینر
WORKDIR /app

# نصب پکیج‌های پایه سیستم‌عامل برای کامپایل درایورهای دیتابیس
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# کپی کردن فایل نیازمندی‌ها و نصب آن‌ها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی کردن تمام کدهای پروژه به داخل کانتینر
COPY . .

# باز کردن پورت 8000 برای FastAPI
EXPOSE 8000

# دستور روشن کردن سرور
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]