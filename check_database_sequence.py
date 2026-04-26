#!/usr/bin/env python3
"""
Veritabanı sequence'lerini kontrol eder.
User ve Tenant ID'lerinin neden 1'den başlamadığını gösterir.
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
print("VERİTABANI SEQUENCE KONTROLÜ")
print("=" * 70)

try:
    # Users tablosu
    print("\n📋 USERS TABLOSU:")
    users_result = db.execute(text("SELECT COUNT(*) as count, MAX(id) as max_id FROM users")).fetchone()
    print(f"   Toplam user: {users_result[0]}")
    print(f"   Max ID: {users_result[1]}")
    
    # Tenant tablosu
    print("\n📋 TENANT TABLOSU:")
    tenant_result = db.execute(text("SELECT COUNT(*) as count, MAX(id) as max_id FROM tenant")).fetchone()
    print(f"   Toplam tenant: {tenant_result[0]}")
    print(f"   Max ID: {tenant_result[1]}")
    
    # Session tablosu
    print("\n📋 SESSION TABLOSU:")
    session_result = db.execute(text("SELECT COUNT(*) as count, MAX(id) as max_id FROM session")).fetchone()
    print(f"   Toplam session: {session_result[0]}")
    print(f"   Max ID: {session_result[1]}")
    
    # Sequence'leri kontrol et (PostgreSQL için - düzeltilmiş)
    print("\n📊 SEQUENCE'LER (PostgreSQL):")
    try:
        sequences = db.execute(text("""
            SELECT sequence_name, last_value 
            FROM information_schema.sequences 
            WHERE sequence_schema = 'public'
            ORDER BY sequence_name
        """)).fetchall()
        
        if sequences:
            for seq_name, last_val in sequences:
                print(f"   {seq_name}: {last_val}")
        else:
            print("   ⚠️  Sequence bulunamadı")
    except Exception as e:
        print(f"   ⚠️  Sequence bilgisi alınamadı (normal olabilir): {type(e).__name__}")
    
    # İlk 5 user'ı göster
    print("\n📋 İLK 5 USER:")
    try:
        users = db.execute(text("SELECT id, username, email, created_at FROM users ORDER BY id LIMIT 5")).fetchall()
        for user in users:
            print(f"   ID: {user[0]:3d} | Username: {user[1]:20s} | Email: {user[2]}")
    except Exception as e:
        print(f"   ❌ Hata: {e}")
    
    # İlk 5 tenant'ı göster
    print("\n📋 İLK 5 TENANT:")
    try:
        tenants = db.execute(text("SELECT id, name, plan FROM tenant ORDER BY id LIMIT 5")).fetchall()
        for tenant in tenants:
            print(f"   ID: {tenant[0]:3d} | Name: {tenant[1]:20s} | Plan: {tenant[2]}")
    except Exception as e:
        print(f"   ❌ Hata: {e}")
    
    print("\n" + "=" * 70)
    print("ÖZET:")
    print("=" * 70)
    
    if users_result[1] and users_result[1] > users_result[0]:
        print(f"⚠️  User ID'ler 1'den başlamıyor!")
        print(f"   Toplam: {users_result[0]}, Max ID: {users_result[1]}")
        print(f"   Çözüm: Eski kayıtlar silinmiş, sequence reset edilmemiş")
        print(f"\n   SQL Editor'de çalıştırın:")
        print(f"   SELECT setval('users_id_seq', {users_result[1]});")
    
    if tenant_result[1] and tenant_result[1] > tenant_result[0]:
        print(f"⚠️  Tenant ID'ler 1'den başlamıyor!")
        print(f"   Toplam: {tenant_result[0]}, Max ID: {tenant_result[1]}")
        print(f"   Çözüm: Eski kayıtlar silinmiş, sequence reset edilmemiş")
        print(f"\n   SQL Editor'de çalıştırın:")
        print(f"   SELECT setval('tenant_id_seq', {tenant_result[1]});")
    
except Exception as e:
    print(f"❌ Hata: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
