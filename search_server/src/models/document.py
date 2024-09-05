from typing import List, Optional

from pydantic import BaseModel


class DocumentMeta(BaseModel):
    identifier: str
    datestamp: str
    title: str
    abstract: str
    authors: str
    categories: str
    comments: Optional[str]
    license: Optional[str]
    submitter: str


class DocumentResponse(BaseModel):
    content: str
    meta: DocumentMeta
