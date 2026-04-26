#!/usr/bin/env python3
"""
Veritabanını tamamen sıfırlar.
Tüm tabloları siler ve yeniden oluşturur.
⚠️ UYARI: TÜM VERİLER SİLİNECEK!
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL bulunamadı!")
    exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

print("=" * 70)
print("⚠️  VERİTABANI SIFIRLAMA")
print("=" * 70)
print("\n❌ UYARI: TÜM VERİLER SİLİNECEK!")
print("   • Tüm user'lar silinecek")
print("   • Tüm tenant'lar silinecek")
print("   • Tüm session'lar silinecek")
print("   • Tüm mesajlar silinecek")
print("   • ID'ler 1'den başlayacak")

response = input("\nDevam etmek istiyor musunuz? (evet/hayır): ").strip().lower()

if response not in ['evet', 'yes', 'e', 'y']:
    print("\n❌ İşlem iptal edildi.")
    exit(0)

print("\n🗑️  Siliniyor...")

try:
    # Tüm tabloları sil (cascade delete otomatik çalışacak)
    db.execute(text("TRUNCATE TABLE log CASCADE"))
    db.execute(text("TRUNCATE TABLE message CASCADE"))
    db.execute(text("TRUNCATE TABLE session CASCADE"))
    db.execute(text("TRUNCATE TABLE users CASCADE"))
    db.execute(text("TRUNCATE TABLE tenant CASCADE"))
    
    # Sequence'leri sıfırla
    db.execute(text("ALTER SEQUENCE users_id_seq RESTART WITH 1"))
    db.execute(text("ALTER SEQUENCE tenant_id_seq RESTART WITH 1"))
    db.execute(text("ALTER SEQUENCE session_id_seq RESTART WITH 1"))
    db.execute(text("ALTER SEQUENCE message_id_seq RESTART WITH 1"))
    db.execute(text("ALTER SEQUENCE log_id_seq RESTART WITH 1"))
    
    db.commit()
    
    print("✅ Veritabanı başarıyla sıfırlandı!")
    print("\n📊 Yeni durum:")
    print("   • User ID'ler: 1'den başlayacak")
    print("   • Tenant ID'ler: 1'den başlayacak")
    print("   • Session ID'ler: 1'den başlayacak")
    print("   • Message ID'ler: 1'den başlayacak")
    print("   • Log ID'ler: 1'den başlayacak")
    
except Exception as e:
    db.rollback()
    print(f"❌ Hata: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
