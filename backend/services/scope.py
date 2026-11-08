from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from backend.logger import logger

class Scope(str, Enum):
    IN_SCOPE = "in_scope"
    OUT_OF_SCOPE = "out_of_scope"
    BORDERLINE = "borderline"

# Açıkça kapsam dışı: mevzuat değil, genel sohbet / tıbbi tavsiye / hesaplama
_OUT_PATTERNS = [
    "seni kim yaptı", "hava durumu", "şarkı", "yemek tarifi",
    "şiir yaz", "kod yaz", "borsa", "maç",
]
# Sınırda: sağlık içerir ama mevzuat sorusu olmayabilir
_BORDERLINE_HINTS = ["olur mu", "yapmalı mıyım", "tavsiye", "teşhis",
                     "doz", "kaç gram", "reçete"]

@dataclass
class ScopeDecision:
    scope: Scope
    reason: str

def quick_classify(question: str) -> ScopeDecision:
    q = (question or "").strip().lower()
    if not q:
        return ScopeDecision(Scope.OUT_OF_SCOPE, "empty")
    if any(p in q for p in _OUT_PATTERNS):
        return ScopeDecision(Scope.OUT_OF_SCOPE, "pattern_hit")
    if any(h in q for h in _BORDERLINE_HINTS):
        return ScopeDecision(Scope.BORDERLINE, "borderline_hint")
    return ScopeDecision(Scope.IN_SCOPE, "no_signal")

def llm_classify(question: str) -> ScopeDecision:
    """Sınırda sorular için tek-token LLM onayı. Hata yaparsa IN_SCOPE döner
    (yanlış reddetmek, yanlış kabulden daha zararlı)."""
    from backend.llm_client import llm_client   # senin gerçek export'un: nesne, fonksiyon değil

    prompt = (
        "Aşağıdaki soru Türkiye sağlık mevzuatı (kanun, yönetmelik, tebliğ, "
        "uygulama rehberi) kapsamında mı? Sadece EVET ya da HAYIR yaz.\n\n"
        f"Soru: {question}\nCevap:"
    )
    try:
        out = llm_client.invoke(prompt).content.strip().upper()
        scope = Scope.IN_SCOPE if "EVET" in out else Scope.OUT_OF_SCOPE
        return ScopeDecision(scope, "llm_confirmed")
    except Exception as e:
        logger.warning(f"Scope LLM hatası, in_scope fallback: {e}")
        return ScopeDecision(Scope.IN_SCOPE, "llm_failed_fallback")

def classify_question(question: str) -> ScopeDecision:
    quick = quick_classify(question)
    if quick.scope is Scope.BORDERLINE:
        return llm_classify(question)
    return quick