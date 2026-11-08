"""KVKK-uyumlu kalıcı hafıza politikası.
Aşama 6 kuralı: sohbet mesajları ASLA otomatik kalıcı hafızaya yazılmaz.
Kalıcı kayıt için: açık kullanıcı eylemi + bu üç koşul."""

MEMORY_WRITE_RULES = {
    "auto_write_from_chat": False,         # her konuşmayı otomatik kaydetme
    "allowed_sources": ["explicit_save_button", "admin_document_upload"],
    "retention_days": 180,                 # sohbet mesajları için saklama süresi
    "analytics_logging": "metadata_only",  # soru metni değil, sadece sayı/kategori
}