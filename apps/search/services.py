"""Retrieval over frame descriptions.

PostgreSQL: full-text search (english config: stemming) with ts_rank, normalised to 0-1 as rank/(rank+1).
This is KEYWORD retrieval, not semantic search: "walked in" will not match "entered" unless a stem or word overlaps.
SQLite (tests/dev only): fraction of query terms found as substrings. Same ordering contract, weaker matching.
"""
import re
from functools import reduce
from operator import or_
from django.conf import settings
from django.db import connection
from django.db.models import F, Q
from apps.processing.models import FrameDescription

STOPWORDS = set("""a an the and or of to in on at by for with from into onto is are was were be been it its this that these those
show me find when did does do moment moments time times someone somebody anyone anybody person people there where while who whom
can you please get give look looking see saw seen happen happened happens happening video footage""".split())

def normalise_query(query):
    seen, terms = set(), []
    for t in re.findall(r"[a-z0-9]+", query.lower()):
        if len(t) > 1 and t not in STOPWORDS and t not in seen:
            seen.add(t); terms.append(t)
    return terms

def _stem(t):
    for suf in ("ing", "ed", "es", "s"):
        if t.endswith(suf) and len(t) - len(suf) >= 3:
            return t[: -len(suf)]
    return t

def search_frames(query, video_id=None, limit=None):
    limit = limit or settings.SEARCH_MAX_RESULTS
    terms = normalise_query(query)
    if not terms:
        raise ValueError("Query has no searchable words. Describe a person, object or action.")
    qs = FrameDescription.objects.select_related("frame__video")
    if video_id:
        qs = qs.filter(frame__video_id=video_id)
    if connection.vendor == "postgresql":
        from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
        sq = reduce(or_, [SearchQuery(t, config="english") for t in terms])
        qs = (qs.annotate(vec=SearchVector("search_text", config="english")).filter(vec=sq)
                .annotate(score=SearchRank(F("vec"), sq, normalization=32)).order_by("-score", "frame__timestamp_seconds")[:limit])
        rows = [(d, float(d.score)) for d in qs]
    else:
        stems = [_stem(t) for t in terms]
        cands = qs.filter(reduce(or_, [Q(search_text__icontains=s) for s in stems]))
        scored = []
        for d in cands:
            low = d.search_text.lower()
            scored.append((d, sum(s in low for s in stems) / len(stems)))
        scored.sort(key=lambda x: (-x[1], x[0].frame.timestamp_seconds))
        rows = scored[:limit]
    return [{"video_id": d.frame.video_id, "video_title": d.frame.video.title, "timestamp_seconds": d.frame.timestamp_seconds,
             "description": d.description, "relevance_score": round(score, 4)} for d, score in rows]
