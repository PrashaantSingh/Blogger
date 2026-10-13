from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.services.vector_store import vector_store


def ingest_documents(text: str, batch_id: str):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )

    chunks = splitter.create_documents(
        [text],
        metadatas=[{"batch_id": batch_id}],
    )

    if chunks:
        vector_store.add_documents(chunks)

    return len(chunks)


def retrieve_context(topic: str, batch_id: str) -> str:
    results = vector_store.similarity_search(
        query=topic,
        k=5,
        filter={"batch_id": batch_id},
    )

    return "\n\n".join(doc.page_content for doc in results)