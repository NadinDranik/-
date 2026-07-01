import re
import time
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.embeddings import cosine_similarity, embed_text
from app.models import Document, DocumentChunk, DocumentScope, KnowledgeItem, KnowledgeStatus

settings = get_settings()

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "17025": ["17025", "гост", "лаборатор", "испытательн", "аккредитац"],
    "неопределенность": ["неопределенност", "uncertainty", "u=", "расширенн"],
    "ВЛК": ["влк", "внутрилабораторн", "контрол"],
    "МСИ": ["мси", "межлабораторн", "сличен"],
    "ПК": ["подтвержден", "компетентност", "персонал"],
    "412-ФЗ": ["412", "фз", "аккредитац"],
    "корректирующие действия": ["корректирующ", "несоответств", "ка"],
}


@dataclass
class SearchHit:
    item: KnowledgeItem
    score: float
    match_type: str


class KnowledgeEngine:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def normalize_text(self, text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^\w\s\-.,;:()«»\"'№/]", "", text, flags=re.UNICODE)
        return text

    def detect_topic(self, query: str) -> str | None:
        normalized = self.normalize_text(query)
        best_topic = None
        best_score = 0
        for topic, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in normalized)
            if score > best_score:
                best_score = score
                best_topic = topic
        return best_topic

    async def get_embedding(self, text: str) -> list[float]:
        return embed_text(text)

    async def semantic_search(
        self,
        query_embedding: list[float],
        limit: int = 10,
        owner_id: UUID | None = None,
    ) -> list[SearchHit]:
        result = await self.db.execute(
            select(KnowledgeItem).where(
                KnowledgeItem.status == KnowledgeStatus.ACTIVE,
                KnowledgeItem.embedding.isnot(None),
            )
        )
        items = result.scalars().all()
        scored = [
            SearchHit(item=item, score=cosine_similarity(query_embedding, item.embedding or []), match_type="semantic")
            for item in items
            if item.embedding
        ]
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:limit]

    async def keyword_search(self, query: str, limit: int = 10) -> list[SearchHit]:
        words = [w for w in self.normalize_text(query).split() if len(w) > 2]
        if not words:
            return []

        conditions = []
        for word in words[:10]:
            pattern = f"%{word}%"
            conditions.append(KnowledgeItem.content.ilike(pattern))
            conditions.append(KnowledgeItem.title.ilike(pattern))

        stmt = (
            select(KnowledgeItem)
            .where(KnowledgeItem.status == KnowledgeStatus.ACTIVE)
            .where(or_(*conditions))
            .limit(limit * 3)
        )
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        hits = []
        for item in items:
            kw_text = " ".join(item.keywords or [])
            text_blob = f"{item.title} {item.content} {kw_text}".lower()
            score = min(0.9, 0.5 + 0.05 * sum(1 for w in words if w in text_blob))
            hits.append(SearchHit(item=item, score=score, match_type="keyword"))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:limit]

    async def search_by_normative(self, query: str, limit: int = 5) -> list[SearchHit]:
        doc_patterns = re.findall(r"(?:гост|приказ|фз|см)\s*[\w\-./]+", query.lower())
        if not doc_patterns:
            return []

        conditions = [KnowledgeItem.normative_document.ilike(f"%{p}%") for p in doc_patterns]
        clause_match = re.search(r"п\.?\s*(\d+(?:\.\d+)*)", query.lower())
        if clause_match:
            conditions.append(KnowledgeItem.document_clause.ilike(f"%{clause_match.group(1)}%"))

        stmt = (
            select(KnowledgeItem)
            .where(KnowledgeItem.status == KnowledgeStatus.ACTIVE)
            .where(or_(*conditions))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return [SearchHit(item=item, score=0.95, match_type="normative") for item in result.scalars().all()]

    async def search_document_chunks(
        self,
        query_embedding: list[float],
        owner_id: UUID | None = None,
        limit: int = 8,
    ) -> list[DocumentChunk]:
        scope_filter = Document.scope == DocumentScope.GLOBAL
        if owner_id:
            scope_filter = or_(scope_filter, Document.owner_id == owner_id)

        result = await self.db.execute(
            select(DocumentChunk)
            .join(Document)
            .where(DocumentChunk.embedding.isnot(None))
            .where(scope_filter)
        )
        chunks = result.scalars().all()
        scored = [(c, cosine_similarity(query_embedding, c.embedding or [])) for c in chunks if c.embedding]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored[:limit]]

    def merge_hybrid_results(self, *result_sets: list[SearchHit]) -> list[SearchHit]:
        merged: dict[UUID, SearchHit] = {}
        for hits in result_sets:
            for hit in hits:
                existing = merged.get(hit.item.id)
                if existing:
                    combined = (
                        existing.score * settings.hybrid_search_semantic_weight
                        + hit.score * settings.hybrid_search_keyword_weight
                    )
                    merged[hit.item.id] = SearchHit(
                        item=hit.item,
                        score=max(existing.score, combined),
                        match_type=f"{existing.match_type}+{hit.match_type}",
                    )
                else:
                    merged[hit.item.id] = hit
        return sorted(merged.values(), key=lambda h: h.score, reverse=True)

    async def hybrid_search(
        self,
        query: str,
        owner_id: UUID | None = None,
        limit: int = 10,
    ) -> list[SearchHit]:
        normalized = self.normalize_text(query)
        embedding = await self.get_embedding(normalized)

        semantic = await self.semantic_search(embedding, limit=limit, owner_id=owner_id)
        keyword = await self.keyword_search(query, limit=limit)
        normative = await self.search_by_normative(query, limit=limit)

        merged = self.merge_hybrid_results(semantic, keyword, normative)
        return merged[:limit]

    async def find_best_answer(self, query: str, owner_id: UUID | None = None) -> SearchHit | None:
        hits = await self.hybrid_search(query, owner_id=owner_id, limit=5)
        if not hits:
            return None
        best = hits[0]
        if best.score >= settings.knowledge_relevance_threshold:
            best.item.usage_count += 1
            await self.db.flush()
            return best
        return None

    async def create_from_qa(
        self,
        question: str,
        answer: str,
        category: str | None,
        keywords: list[str],
        author_id: UUID | None,
        source: str,
        used_documents: list | None = None,
    ) -> KnowledgeItem:
        from app.models import KnowledgeCategory

        cat = KnowledgeCategory.FAQ
        if category:
            for c in KnowledgeCategory:
                if c.value == category:
                    cat = c
                    break

        embedding = await self.get_embedding(f"{question}\n{answer}")
        item = KnowledgeItem(
            title=question[:500],
            category=cat,
            content=answer,
            keywords=keywords,
            embedding=embedding,
            author_id=author_id,
            source=source,
            related_documents=used_documents or [],
            question_type="auto_generated",
        )
        self.db.add(item)
        await self.db.flush()
        return item
