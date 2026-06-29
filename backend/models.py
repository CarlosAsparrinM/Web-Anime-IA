from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class LocalizedString(BaseModel):
    es: str
    en: str

class ArticleModel(BaseModel):
    title: LocalizedString
    slug: str
    content: LocalizedString
    excerpt: LocalizedString
    category: str
    imageUrl: str
    imageAlt: str
    animeName: str
    tags: List[str]
    published: bool = True
    createdAt: datetime = None
    updatedAt: datetime = None
