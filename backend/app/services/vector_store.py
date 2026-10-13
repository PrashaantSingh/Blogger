from langchain_chroma import Chroma
from app.services.embedding_service import embeddings

vector_store = Chroma(
    collection_name="blog_documents",
    embedding_function=embeddings,
    persist_directory="./chroma_db",
)