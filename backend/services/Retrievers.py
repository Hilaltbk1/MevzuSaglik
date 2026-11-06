from __future__ import annotations
from backend.services.topic_router import classify_topics, should_apply_topic_filter
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny
from collections import defaultdict
from backend.services.chunking11 import assemble_parent, source_label
from backend.services.text_utils import tokenize
import threading
from typing import List, Any, Dict, Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.retrievers import BM25Retriever
from langchain_core.prompts import PromptTemplate
from backend.config.configuration import Settings
from backend.prompt.My_Prompt import create_prompt
from backend.logger import logger

load_dotenv()
settings = Settings()

# Thread-safe lazy loading
_chain_instance: Optional[Any] = None
_chain_lock = threading.Lock()


def retrieval_chain():
    """
    Thread-safe lazy loading ile RAG chain'i oluşturur.
    """
    global _chain_instance

    if _chain_instance is not None:
        return _chain_instance

    with _chain_lock:
        if _chain_instance is not None:
            return _chain_instance

        logger.info("🚀 RAG zinciri başlatılıyor (thread-safe)...")
        _chain_instance = _create_chain_instance()
        return _chain_instance


def invalidate_chain():
    """Yeni doküman yüklendiğinde veya silindiğinde RAG zincirini sıfırlar."""
    global _chain_instance
    with _chain_lock:
        _chain_instance = None
    logger.info("🔄 RAG zinciri sıfırlandı (bir sonraki sorguda güncel verilerle yüklenecek).")


def _create_chain_instance():
    from backend.services.Vector_store import initialize_vector_store

    logger.info("🚀 RAG zinciri başlatılıyor...")

    llm = ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL_NAME or "gemini-1.5-flash",
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0,
    )

    logger.info("📦 Vector store yükleniyor...")
    v_db, split_text = initialize_vector_store(rebuild_db=False)
    if v_db is None:
        raise ValueError("Hata: Vektör veritabanı başlatılamadı! Qdrant bağlantısını kontrol et.")

    if split_text is None or len(split_text) == 0:
        logger.warning("⚠️ Chunks bulunamadı, BM25 devre dışı kalacak")
        split_text = []

    logger.info(f"✅ {len(split_text)} chunk yüklendi")

    def get_bm25_retriever(split_text):
        if not split_text or len(split_text) == 0:
            logger.warning("⚠️ BM25 için chunks yok, sadece vector search kullanılacak")
            return None

        # pkl kullanmadan her zaman bellekte oluştur (yeni belgeler eklendikçe güncel kalsın)
        public_chunks = [
            d for d in split_text
            if d.metadata.get("access_scope", "public") == "public"
        ]
        bm25 = BM25Retriever.from_documents(
            public_chunks if public_chunks else split_text,
            preprocess_func=tokenize
        )

        return bm25

    # Retriever'ları oluştur
    vector_retriever = v_db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.VECTOR_FETCH_K},
    )
    bm25_retriever = get_bm25_retriever(split_text)
    parent_index = defaultdict(list)
    for d in split_text:
        pid = d.metadata.get("parent_id")
        if pid:
            parent_index[pid].append({
                "child_index": d.metadata.get("child_index", 0),
                "text": d.metadata.get("body", d.page_content),
            })

    if bm25_retriever:
        bm25_retriever.k = settings.BM25_FETCH_K
        logger.info(
            f"✅ Hybrid hazır | mode={settings.RETRIEVAL_MODE} "
            f"v_k={settings.VECTOR_FETCH_K} bm25_k={settings.BM25_FETCH_K} "
            f"rrf_k={settings.RRF_K}"
        )
    else:
        logger.warning("⚠️ Sadece Vector Search kullanılacak (BM25 yok)")

    from langchain_core.retrievers import BaseRetriever
    from langchain_core.documents import Document

    def _owner_matches(meta_owner, user_id) -> bool:
        """Qdrant/BM25 owner_id string|int tutarsızlığını normalize et."""
        if user_id is None or meta_owner is None:
            return False
        return str(meta_owner) == str(user_id)

    def doc_key(doc) -> str:
        md = getattr(doc, "metadata", None) or {}
        return (
            md.get("chunk_id")
            or md.get("id")
            or f"{md.get('parent_id', '')}:{md.get('child_index', '')}:{doc.page_content[:120]}"
        )

    def reciprocal_rank_fusion(ranked_lists, *, key_fn, rrf_k=60, weights=None, top_n=20):
        if weights is None:
            weights = [1.0] * len(ranked_lists)
        scores = {}
        doc_map = {}
        for list_i, docs in enumerate(ranked_lists):
            w = weights[list_i]
            for rank, doc in enumerate(docs):
                kid = key_fn(doc)
                if not kid:
                    continue
                doc_map[kid] = doc
                scores[kid] = scores.get(kid, 0.0) + w * (1.0 / (rrf_k + rank + 1))
        ordered = sorted(scores, key=scores.get, reverse=True)
        return [doc_map[k] for k in ordered[:top_n]]

    class HybridRetriever(BaseRetriever):
        v_store: Any
        b_retriever: Any = None

        def retrieve(
            self,
            query: str,
            *,
            user_id: Optional[int] = None,
            route_topics: Optional[List[str]] = None,
            apply_topic_filter: bool = False,
        ) -> List[Document]:
            use_topic = bool(apply_topic_filter and route_topics)
            route_topics_list = list(route_topics or [])

            # --- 1) PRIVACY FILTER (her zaman) ---
            if user_id is not None:
                privacy_filter = Filter(
                    should=[
                        FieldCondition(
                            key="metadata.access_scope",
                            match=MatchValue(value="public"),
                        ),
                        FieldCondition(
                            key="metadata.owner_id",
                            match=MatchValue(value=str(user_id)),
                        ),
                    ]
                )
            else:
                privacy_filter = Filter(
                    must=[
                        FieldCondition(
                            key="metadata.access_scope",
                            match=MatchValue(value="public"),
                        ),
                    ]
                )

            # --- 2) TOPIC FILTER (soft) — primary VEYA topics listesi (BM25 ile aynı kural) ---
            # Not: Qdrant'ta must varken should zorunlu filtre DEĞİLDİR → nested Filter.
            qdrant_filter = privacy_filter
            if use_topic:
                topic_or = Filter(
                    should=[
                        FieldCondition(
                            key="metadata.primary_topic",
                            match=MatchAny(any=route_topics_list),
                        ),
                        FieldCondition(
                            key="metadata.topics",
                            match=MatchAny(any=route_topics_list),
                        ),
                    ]
                )
                if user_id is not None:
                    qdrant_filter = Filter(
                        must=[
                            topic_or,
                            Filter(
                                should=[
                                    FieldCondition(
                                        key="metadata.access_scope",
                                        match=MatchValue(value="public"),
                                    ),
                                    FieldCondition(
                                        key="metadata.owner_id",
                                        match=MatchValue(value=str(user_id)),
                                    ),
                                ]
                            ),
                        ]
                    )
                else:
                    musts = list(privacy_filter.must or [])
                    musts.append(topic_or)
                    qdrant_filter = Filter(must=musts)

            mode = settings.RETRIEVAL_MODE  # vector | bm25 | hybrid

            # --- 3) Vector arama (Doğrudan VectorStore'dan filtre ile çağrılır) ---
            v_docs: List[Document] = []
            if mode in ("vector", "hybrid"):
                try:
                    v_docs = self.v_store.similarity_search(
                        query,
                        k=settings.VECTOR_FETCH_K,
                        filter=qdrant_filter,
                    )
                except Exception as e:
                    logger.warning(f"Vector search hatası (filtreli): {e}")
                    v_docs = []

                if use_topic and len(v_docs) < 3:
                    logger.info("⚠️ Topic filter az sonuç verdi → privacy-only fallback")
                    try:
                        v_docs = self.v_store.similarity_search(
                            query,
                            k=settings.VECTOR_FETCH_K,
                            filter=privacy_filter,
                        )
                    except Exception as e:
                        logger.warning(f"Vector search hatası (fallback): {e}")
                    use_topic = False

            # --- 4) BM25 ---
            b_docs: List[Document] = []
            if mode in ("bm25", "hybrid") and self.b_retriever is not None:
                b_docs_all = self.b_retriever.invoke(query)
                b_docs = [
                    d for d in b_docs_all
                    if (
                        d.metadata.get("access_scope", "public") == "public"
                        or _owner_matches(d.metadata.get("owner_id"), user_id)
                    )
                    and (
                        not use_topic
                        or d.metadata.get("primary_topic") in route_topics_list
                        or any(t in (d.metadata.get("topics") or []) for t in route_topics_list)
                    )
                ]

            # --- 5) Mode / RRF ---
            if mode == "vector" or not self.b_retriever:
                return v_docs[: settings.HYBRID_TOP_N]
            if mode == "bm25":
                return b_docs[: settings.HYBRID_TOP_N]

            if not b_docs:
                return v_docs[: settings.HYBRID_TOP_N]
            if not v_docs:
                return b_docs[: settings.HYBRID_TOP_N]

            fused = reciprocal_rank_fusion(
                [v_docs, b_docs],
                key_fn=doc_key,
                rrf_k=settings.RRF_K,
                weights=[settings.VECTOR_WEIGHT, settings.BM25_WEIGHT],
                top_n=settings.HYBRID_TOP_N,
            )
            logger.info(
                f"🔀 hybrid: v={len(v_docs)} bm25={len(b_docs)} "
                f"fused={len(fused)} rrf_k={settings.RRF_K}"
            )
            return fused

        def _get_relevant_documents(
            self, query: str, *, run_manager=None
        ) -> List[Document]:
            return self.retrieve(query)

    hybrid_retriever = HybridRetriever(v_store=v_db, b_retriever=bm25_retriever)

    rerank_model = None
    if settings.ENABLE_RERANK:
        print("✨ Re-Ranker modeli yükleniyor (ilk seferde biraz sürebilir)...")
        try:
            from sentence_transformers.cross_encoder import CrossEncoder
            rerank_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        except Exception as e:
            print(f"⚠️ Re-Ranker modeli yüklenemedi, sadece Hybrid Search kullanılacak: {e}")
            rerank_model = None
    else:
        print("ℹ️ ENABLE_RERANK=false → hybrid ölçümü için reranker kapalı")

    qa_pr, c_pr = create_prompt()

    document_prompt = PromptTemplate(
        input_variables=["page_content", "source_label"],
        template="[Kaynak: {source_label}]\nİÇERİK: {page_content}",
    )

    class FullChain:
        def __init__(self, llm_client, retriever, reranker, qa_prompt, ctx_prompt, doc_prompt, parent_index):
            self.llm          = llm_client
            self.parent_index = parent_index
            self.retriever    = retriever
            self.reranker     = reranker
            self.qa_prompt    = qa_prompt
            self.ctx_prompt   = ctx_prompt
            self.doc_prompt   = doc_prompt

        def _expand_to_parents(self, docs, cap=4000, max_parents=4):
            from langchain_core.documents import Document as LCDoc
            out, seen = [], set()
            for d in docs:
                pid = d.metadata.get("parent_id")
                if not pid:
                    out.append(d)
                elif pid not in seen:
                    seen.add(pid)
                    kids = self.parent_index.get(pid)
                    if kids:
                        matched = {
                            x.metadata.get("child_index")
                            for x in docs
                            if x.metadata.get("parent_id") == pid
                        }
                        out.append(LCDoc(
                            page_content=assemble_parent(kids, matched, cap),
                            metadata=dict(d.metadata),
                        ))
                    else:
                        out.append(d)
                if len(out) >= max_parents:
                    break
            return out

        def _build_search_query(self, question: str, chat_history: List[Any]) -> str:
            if not chat_history:
                return question
            try:
                history_text = "\n".join([getattr(m, "content", str(m)) for m in chat_history])
                prompt = self.ctx_prompt.format(input=question, chat_history=history_text)
                resp   = self.llm.invoke(prompt)
                return getattr(resp, "content", str(resp))
            except Exception:
                return question

        def _generate_queries(self, question: str, chat_history: List[Any], n: int = 2) -> List[str]:
            """Ana sorgu + n alternatif sorgu üretir. Toplam n+1 sorgu döner."""
            history_text = "\n".join([getattr(m, "content", str(m)) for m in chat_history])
            prompt = (
                f"Aşağıdaki soruyu mevzuat veritabanında aramak için {n} farklı biçimde yeniden ifade et.\n"
                f"Her versiyon farklı kelime seçimi veya farklı açı kullanmalı.\n"
                f"KESİNLİKLE olmayan madde numarası, kanun adı veya tarih UYDURMA.\n"
                f"Yalnızca {n} satır yaz, her satıra bir sorgu. Başka açıklama ekleme.\n\n"
                f"Sohbet geçmişi: {history_text}\n"
                f"Soru: {question}"
            )
            try:
                resp = self.llm.invoke(prompt)
                raw = getattr(resp, "content", str(resp)).strip()
                alternatives = [
                    q.strip("0123456789.-) ").strip()
                    for q in raw.split("\n") if q.strip()
                ][:n]
            except Exception:
                alternatives = []
            # Orijinal soruyu başa koy, tekrarları kaldır
            seen, unique = set(), []
            for q in [question] + alternatives:
                if q and q not in seen:
                    seen.add(q)
                    unique.append(q)
            return unique

        def _needs_decomposition(self, question: str) -> bool:
            """Sorunun birden fazla bağımsız alt soruya ihtiyacı var mı?"""
            q = question.lower()
            signals = [
                (" ve " in q and "?" in q),      # "... ve ...?" şeklinde
                ("hem " in q and " hem " in q),   # "hem X hem Y"
                ("ayrıca" in q),                  # "ayrıca şunu da"
                (q.count("?") > 1),               # birden fazla soru işareti
                (" ile birlikte " in q),           # "X ile birlikte Y"
            ]
            return sum(signals) >= 2  # 2+ sinyal varsa karmaşık say

        def _decompose_question(self, question: str) -> List[str]:
            """Karmaşık soruyu bağımsız alt sorulara böler."""
            prompt = (
                f"Aşağıdaki soruyu birbirinden bağımsız 2-3 alt soruya böl.\n"
                f"Her alt soru tek başına mevzuatta aranabilir olmalı.\n"
                f"KESİNLİKLE olmayan madde numarası veya kanun adı UYDURMA.\n"
                f"Yalnızca alt soruları yaz, her satıra bir tane. Açıklama ekleme.\n\n"
                f"Soru: {question}"
            )
            try:
                resp = self.llm.invoke(prompt)
                raw  = getattr(resp, "content", str(resp)).strip()
                subs = [
                    q.strip("0123456789.-) ").strip()
                    for q in raw.split("\n") if q.strip()
                ][:3]
                return subs if subs else [question]
            except Exception:
                return [question]

        def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
            question: str = inputs.get("input", "")
            chat_history: List[Any] = inputs.get("chat_history", [])
            current_user_id: int | None = inputs.get("current_user_id", None)

            search_query = self._build_search_query(question, chat_history)

            # Topic routing
            route = classify_topics(search_query)
            use_topic = should_apply_topic_filter(route, min_confidence=0.70)
            logger.info(
                f"🧭 route={route.topics} conf={route.confidence:.2f} "
                f"apply={use_topic} ({route.reason})"
            )

            # ── Query Decomposition / Multi-Query ────────────────────────
            if self._needs_decomposition(question):
                sub_questions = self._decompose_question(question)
                logger.info(f"🔀 Decomposition: {len(sub_questions)} alt soru → {sub_questions}")
                queries = list(dict.fromkeys([search_query] + sub_questions))
            else:
                queries = self._generate_queries(search_query, [], n=2)
            logger.info(f"🔍 {len(queries)} sorgu: {queries}")

            k_rrf = 60
            all_scores: Dict[str, float] = {}
            all_docs_map: Dict[str, Any] = {}

            def _key(doc):
                md = doc.metadata or {}
                return (
                    md.get("chunk_id")
                    or f"{md.get('parent_id', '')}:{md.get('child_index', '')}:{doc.page_content[:120]}"
                )

            for q in queries:
                q_docs = self.retriever.retrieve(
                    q,
                    user_id=current_user_id,
                    route_topics=route.topics,
                    apply_topic_filter=use_topic,
                )
                for rank, doc in enumerate(q_docs):
                    key = _key(doc)
                    all_scores[key] = all_scores.get(key, 0) + 1 / (k_rrf + rank + 1)
                    all_docs_map[key] = doc

            sorted_keys = sorted(all_scores, key=lambda x: all_scores[x], reverse=True)
            docs = [all_docs_map[k] for k in sorted_keys[:15]]
            logger.info(f"🔀 multi-query RRF: {len(all_docs_map)} aday → top {len(docs)}")

            # Manuel Re-Ranking
            corrective_trigger = False
            if self.reranker and docs:
                try:
                    pairs         = [[question, d.page_content] for d in docs]
                    rerank_scores = self.reranker.predict(pairs)
                    scored_docs   = sorted(zip(rerank_scores, docs), key=lambda x: x[0], reverse=True)
                    best_score    = scored_docs[0][0] if scored_docs else -99

                    logger.info(f"📊 Rerank en iyi skor: {best_score:.2f}")

                    if best_score < -4.0:
                        # En iyi belge bile çok alakasız → corrective tetikle
                        logger.warning(f"⚠️ Corrective RAG: en iyi skor {best_score:.2f} < -4.0 → alakasız belgeler")
                        corrective_trigger = True
                        docs = []
                    else:
                        docs = [d for score, d in scored_docs[:6] if score > -3.0]
                        if not docs:
                            logger.warning("⚠️ Re-Ranker yeterli güven puanı bulamadı, dökümanlar elendi.")
                            corrective_trigger = True
                except Exception as e:
                    logger.warning(f"⚠️ Re-ranking hatası, orijinal sıralama kullanılacak: {e}")
                    docs = docs[:6]
            else:
                docs = docs[:6]
            docs = self._expand_to_parents(docs)

            # ── Corrective RAG + Abstention ───────────────────────────────
            if not docs or corrective_trigger:
                reason = "alakasız belgeler" if corrective_trigger else "boş sonuç"
                logger.warning(f"⚠️ Corrective RAG tetiklendi ({reason}), fallback aramaya geçiliyor")
                fallback_docs = self.retriever.retrieve(
                    question,
                    user_id=current_user_id,
                    route_topics=None,
                    apply_topic_filter=False,
                )
                if fallback_docs:
                    docs = fallback_docs[:6]
                    docs = self._expand_to_parents(docs)
                    logger.info(f"✅ Fallback arama {len(docs)} belge buldu")
                else:
                    logger.warning("⚠️ Fallback da sonuç vermedi → abstention")
                    return {
                        "answer": (
                            "Bu soruyu yanıtlamak için sistemimizde yeterli mevzuat kaydı bulunamadı.\n\n"
                            "Lütfen şunlardan birini deneyin:\n"
                            "• Sorunuzu farklı kelimelerle ifade edin\n"
                            "• İlgili mevzuatın adını veya madde numarasını belirtin\n"
                            "• Konuyu daha genel bir ifadeyle sorun"
                        ),
                        "context": [],
                    }

            formatted_docs = []
            for d in docs:
                s_label = d.metadata.get("source_label") or source_label(d.metadata) or d.metadata.get("Mevzuat_Adi", "Bilinmeyen")
                text = self.doc_prompt.format(
                    page_content=d.page_content,
                    source_label=s_label,
                )
                formatted_docs.append(text)

            context_text     = "\n\n".join(formatted_docs)
            qa_prompt_filled = self.qa_prompt.format(input=question, context=context_text)
            answer_msg       = self.llm.invoke(qa_prompt_filled)
            answer_text      = getattr(answer_msg, "content", str(answer_msg))

            return {"answer": answer_text, "context": docs}

    class ChainContainer:
        def __init__(self, fc):
            self.full_chain = fc

    full_chain = FullChain(
        llm_client=llm,
        retriever=hybrid_retriever,
        reranker=rerank_model,
        qa_prompt=qa_pr,
        ctx_prompt=c_pr,
        doc_prompt=document_prompt,
        parent_index=parent_index,
    )

    _chain_instance = ChainContainer(full_chain)
    return _chain_instance
