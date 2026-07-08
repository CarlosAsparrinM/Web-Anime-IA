from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class CommentModel(BaseModel):
    text: str
    date: datetime

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
    comments: List[CommentModel] = []
    createdAt: datetime = None
    updatedAt: datetime = None
