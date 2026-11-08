"""Konfigurasi development lokal. Password tidak dicetak dan tidak disimpan di repo."""
import base64
import getpass
import hashlib
import json
from pathlib import Path
import secrets
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'IF133.Tugas1.Api.csproj'


def password_hash(password):
    iterations = 210000
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations, dklen=32)
    return f'{iterations}.{base64.b64encode(salt).decode()}.{base64.b64encode(digest).decode()}'


def read_password(label):
    while True:
        first = getpass.getpass(f'Password {label} (12–1024 unit UTF-16): ')
        second = getpass.getpass('Ulangi password: ')
        if 12 <= len(first.encode('utf-16-le')) // 2 <= 1024 and first.strip() and first == second:
            return first
        print('Password harus 12–1024 unit UTF-16, tidak hanya whitespace, dan konfirmasi harus sama.')


def main():
    print('Konfigurasi disimpan di .NET User Secrets di luar repository, khusus Development.')
    print('JWT key baru akan dibuat. Token lama tidak berlaku setelah aplikasi direstart.')
    connection = getpass.getpass('Connection string MySQL (kosong = pertahankan User Secret yang sudah ada): ').strip()
    admin = read_password('admin')
    reader = read_password('reader')
    values = {
        'Jwt:Key': secrets.token_urlsafe(48),
        'Jwt:Issuer': 'IF133.Tugas1.Api',
        'Jwt:Audience': 'IF133.Tugas1.Client',
        'Jwt:ExpiresMinutes': '30',
        'Auth:Users:0:Username': 'admin',
        'Auth:Users:0:Role': 'Admin',
        'Auth:Users:0:PasswordHash': password_hash(admin),
        'Auth:Users:1:Username': 'reader',
        'Auth:Users:1:Role': 'Reader',
        'Auth:Users:1:PasswordHash': password_hash(reader),
    }
    if connection:
        values['ConnectionStrings:DefaultConnection'] = connection
    result = subprocess.run(['dotnet', 'user-secrets', 'set', '--project', str(PROJECT)], input=json.dumps(values), text=True, capture_output=True)
    if result.returncode:
        raise SystemExit('Gagal menyimpan User Secrets. Pastikan .NET SDK terpasang dan UserSecretsId ada pada csproj.')
    print('Konfigurasi berhasil disimpan. Akun: admin (Admin), reader (Reader).')
    print('Jalankan: dotnet run --launch-profile https')
    print('Jangan bagikan file secrets.json atau menaruh password pada collection yang dikumpulkan.')


if __name__ == '__main__':
    main()
