"""
SpiderLang fmt — source dialects & build-file emitters.

- st_dialect: the second language (.st) with its OWN vocabulary and tokens,
  distinct from the traditional .mk encoding — never just an extension swap.
"""
from .st_dialect import (
    ST_KEYWORDS, ST_BLOCKS, st_keywords, st_render, is_st_dialect,
    classify, mk_leaks, is_st_keyword,
)

__all__ = ["ST_KEYWORDS", "ST_BLOCKS", "st_keywords", "st_render",
           "is_st_dialect", "classify", "mk_leaks", "is_st_keyword"]
