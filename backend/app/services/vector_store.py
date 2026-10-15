from pathlib import Path

from langchain_chroma import Chroma
from app.services.embedding_service import embeddings

persist_directory = Path(__file__).resolve().parents[2] / "chroma_db"

vector_store = Chroma(
    collection_name="blog_documents",
    embedding_function=embeddings,
    persist_directory=str(persist_directory),
)
