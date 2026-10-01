# Gunakan image Python versi ringan
FROM python:3.10-slim

# Set folder kerja di dalam sistem Deplexo
WORKDIR /app

# Salin file requirements terlebih dahulu untuk mengoptimalkan proses build
COPY requirements.txt .

# Install semua dependensi (termasuk Flask, Gunicorn, dan curl_cffi)
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh file bot dan app ke dalam folder kerja
COPY . .

# Jalankan aplikasi menggunakan Gunicorn yang terikat ke PORT milik Deplexo
CMD sh -c "gunicorn app:app --bind 0.0.0.0:${PORT:-8000} --workers 1 --threads 2"
