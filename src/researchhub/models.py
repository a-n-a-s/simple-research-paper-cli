from pydantic import BaseModel
import uuid
class Paper(BaseModel):
    paper_id : int = uuid.uuid4()
    title : str
    authors : list[str]
    abstract : str | None = None
    doi : str | None = None
    publication_year : int
    source : str | None = None
    paper_url:str | None = None
