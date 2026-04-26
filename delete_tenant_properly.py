#!/usr/bin/env python3
"""
Tenant'ı ve ilişkili tüm verileri siler.
Foreign key constraint'leri dikkate alır.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL bulunamadı!")
    exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

from backend.schemas.tenant_model import TenantModel
from backend.schemas.session_model import SessionModel
from backend.schemas.message_model import MessageModel
from backend.schemas.log_model import LogModel

def delete_tenant(tenant_id):
    """Tenant'ı ve ilişkili tüm verileri siler"""
    print(f"\n{'='*70}")
    print(f"TENANT SİLME İŞLEMİ")
    print(f"{'='*70}")
    
    try:
        # Tenant'ı bul
        tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
        if not tenant:
            print(f"❌ Tenant ID {tenant_id} bulunamadı!")
            return
        
        print(f"\n📋 Silinecek Tenant:")
        print(f"   ID: {tenant.id}")
        print(f"   Name: {tenant.name}")
        print(f"   Plan: {tenant.plan}")
        print(f"   API Key: {tenant.api_key[:10]}...")
        
        # İlişkili session'ları bul
        sessions = db.query(SessionModel).filter(SessionModel.tenant_id == tenant_id).all()
        print(f"\n📊 İlişkili Veriler:")
        print(f"   Sessions: {len(sessions)}")
        
        total_messages = 0
        total_logs = 0
        
        for session in sessions:
            messages = db.query(MessageModel).filter(MessageModel.session_id == session.id).all()
            logs = db.query(LogModel).filter(LogModel.message_id.in_([m.id for m in messages])).all()
            total_messages += len(messages)
            total_logs += len(logs)
        
        print(f"   Messages: {total_messages}")
        print(f"   Logs: {total_logs}")
        
        # Onay iste
        print(f"\n{'='*70}")
        print(f"⚠️  UYARI: Tüm ilişkili veriler SİLİNECEK!")
        print(f"{'='*70}")
        
        response = input(f"\nTenant {tenant.name} (ID: {tenant_id}) silinsin mi? (evet/hayır): ").strip().lower()
        
        if response not in ['evet', 'yes', 'e', 'y']:
            print("\n❌ İşlem iptal edildi.")
            return
        
        # Sil
        print(f"\n🗑️  Siliniyor...")
        
        # Cascade delete otomatik çalışacak
        db.delete(tenant)
        db.commit()
        
        print(f"✅ Tenant başarıyla silindi!")
        print(f"   • {len(sessions)} session silindi")
        print(f"   • {total_messages} message silindi")
        print(f"   • {total_logs} log silindi")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Hata: {e}")
    finally:
        db.close()

def list_tenants():
    """Tüm tenant'ları listele"""
    print(f"\n{'='*70}")
    print(f"TÜM TENANT'LAR")
    print(f"{'='*70}\n")
    
    tenants = db.query(TenantModel).all()
    
    if not tenants:
        print("❌ Hiç tenant bulunamadı!")
        return
    
    for tenant in tenants:
        sessions = db.query(SessionModel).filter(SessionModel.tenant_id == tenant.id).count()
        print(f"ID: {tenant.id:3d} | Name: {tenant.name:20s} | Plan: {tenant.plan:10s} | Sessions: {sessions:3d}")
    
    db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Kullanım:")
        print("  python delete_tenant_properly.py list          # Tüm tenant'ları listele")
        print("  python delete_tenant_properly.py delete <id>   # Tenant'ı sil")
        print("\nÖrnek:")
        print("  python delete_tenant_properly.py list")
        print("  python delete_tenant_properly.py delete 44")
        exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        list_tenants()
    elif command == "delete":
        if len(sys.argv) < 3:
            print("❌ Tenant ID gerekli!")
            print("Kullanım: python delete_tenant_properly.py delete <id>")
            exit(1)
        
        try:
            tenant_id = int(sys.argv[2])
            delete_tenant(tenant_id)
        except ValueError:
            print(f"❌ Geçersiz Tenant ID: {sys.argv[2]}")
    else:
        print(f"❌ Bilinmeyen komut: {command}")
