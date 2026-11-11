from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from backend.logger import logger

class Scope(str, Enum):
    IN_SCOPE = "in_scope"
    OUT_OF_SCOPE = "out_of_scope"
    BORDERLINE = "borderline"

_OUT_PATTERNS = [
    "seni kim yaptı", "hava durumu", "şarkı", "yemek tarifi",
    "şiir yaz", "kod yaz", "borsa", "maç", "tatil", "film", "dizi",
]
_BORDERLINE_HINTS = ["olur mu", "yapmalı mıyım", "tavsiye", "teşhis",
                     "doz", "kaç gram", "reçete"]
_MEVZUAT_SIGNALS = [
    "yönetmelik", "yonetmelik", "kanun", "kanunu", "tebliğ", "teblig",
    "madde", "md.", "rehber", "protokol", "talimat", "sirküler", "sirkuler",
    "mevzuat", "yasa", "yasal", "yönerge", "yonerge",
    "sağlık bakanlığı", "saglik bakanligi", "sağlık bakanliğinin",
    "sayılı", "sayili", "tarihli", "uygulama usul", "hasta hakları",
    "hasta haklari", "hasta güvenliği", "hasta guvenligi", "kvkk",
]

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
    if any(s in q for s in _MEVZUAT_SIGNALS):
        return ScopeDecision(Scope.IN_SCOPE, "mevzuat_signal")
    if any(h in q for h in _BORDERLINE_HINTS):
        return ScopeDecision(Scope.BORDERLINE, "borderline_hint")
    return ScopeDecision(Scope.BORDERLINE, "no_mevzuat_signal")

def llm_classify(question: str) -> ScopeDecision:
    from backend.llm_client import llm_client
    prompt = (
        "Asagidaki soru Turkiye saglik mevzuati (kanun, yonetmelik, teblig, "
        "uygulama rehberi) kapsaminda mi? Sadece EVET ya da HAYIR yaz.\n\n"
        f"Soru: {question}\nCevap:"
    )
    try:
        out = llm_client.invoke(prompt).content.strip().upper()
        scope = Scope.IN_SCOPE if "EVET" in out else Scope.OUT_OF_SCOPE
        return ScopeDecision(scope, "llm_confirmed")
    except Exception as e:
        logger.warning(f"Scope LLM hatasi, in_scope fallback: {e}")
        return ScopeDecision(Scope.IN_SCOPE, "llm_failed_fallback")

def classify_question(question: str) -> ScopeDecision:
    quick = quick_classify(question)
    if quick.scope is Scope.BORDERLINE:
        return llm_classify(question)
    return quick
