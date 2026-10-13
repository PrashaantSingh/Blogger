import json
import time
from uuid import uuid4
from collections.abc import AsyncIterator

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.graph.workflow import approved_writer, planning_writer
from app.services.rag_service import (
    ingest_documents,
    retrieve_context,
)

router = APIRouter()
pending_plans: dict[str, dict] = {}


def _event(**payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False) + "\n"


from fastapi import UploadFile, HTTPException
from io import BytesIO



async def extract_documents(files: list[UploadFile] | None) -> str:
   
    if not files:
        return ""

    extracted_text = []
    max_file_size = 10 * 1024 * 1024
    max_total_chars = 200_000

    for file in files:
        content = await file.read()
        filename = (file.filename or "").lower()

        if len(content) > max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"{filename} exceeds the 10 MB limit."
            )

        try:
            if filename.endswith((".txt", ".md", ".csv")):
                text = content.decode("utf-8")

            elif filename.endswith(".pdf"):
                from pypdf import PdfReader

                reader = PdfReader(BytesIO(content))
                text = "\n".join(
                    page.extract_text() or ""
                    for page in reader.pages
                )

            elif filename.endswith(".docx"):
                from docx import Document

                doc = Document(BytesIO(content))
                text = "\n".join(
                    paragraph.text
                    for paragraph in doc.paragraphs
                )

            else:
                raise HTTPException(
                    status_code=415,
                    detail=f"Unsupported file format: {filename}"
                )

            extracted_text.append(
                f"\n--- Document: {filename} ---\n{text}"
            )

        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Could not read {filename}: {exc}"
            ) from exc
        finally:
            await file.close()

    combined_text = "\n".join(extracted_text)
    return combined_text[:max_total_chars]




async def run_graph(approved_state: dict) -> AsyncIterator[str]:
    started_at = time.perf_counter()
    plan = approved_state.get("plan")
    tasks = plan.tasks if hasattr(plan, "tasks") else (plan or {}).get("tasks", [])
    plan_titles = {
        (task.id if hasattr(task, "id") else task["id"]): (
            task.title if hasattr(task, "title") else task["title"]
        )
        for task in tasks
    }
    total_sections = len(plan_titles)
    completed_sections = 0

    def emit(
        name: str,
        message: str,
        *,
        section: str | None = None,
        progress: int = 0,
        event_id: str | None = None,
    ) -> str:
        return _event(
            id=event_id or name,
            name=name,
            message=message,
            section=section,
            completed=True,
            progress=progress,
            elapsed_ms=round((time.perf_counter() - started_at) * 1000),
        )

    yield emit("start", "Preparing the generation workflow", progress=0)
    try:
        async for update in approved_writer.astream(
            approved_state,
            stream_mode="updates",
        ):
            for name, result in update.items():
                if not isinstance(result, dict):
                    continue
                if name == "reducer":
                    yield _event(
                        finished=True,
                        blog=result.get("final", ""),
                        blog_title=(result.get("final", "").split("\n", 1)[0].removeprefix("# ").strip()),
                        elapsed_ms=round((time.perf_counter() - started_at) * 1000),
                    )
                    continue
                if name == "worker":
                    sections = result.get("sections", [])
                    section_id = sections[0][0] if sections else 0
                    completed_sections += 1
                    section_title = plan_titles.get(section_id, f"Section {section_id}")
                    progress = 35 + round((completed_sections / max(total_sections, 1)) * 50)
                    yield emit(
                        name,
                        f"Finished section {completed_sections} of {total_sections}",
                        section=section_title,
                        progress=progress,
                        event_id=f"section-{section_id}",
                    )
                else:
                    yield emit(name, f"Completed {name.replace('_', ' ')}")
    except Exception as exc:
        yield _event(
            error="Blog generation failed",
            detail=str(exc),
            elapsed_ms=round((time.perf_counter() - started_at) * 1000),
        )



@router.post("/plan")
async def create_plan(
    topic: str = Form(..., min_length=3, max_length=500),
    supporting_documents: list[UploadFile] | None = File(default=None),
):
    topic = topic.strip()
    batch_id = uuid4().hex

    supporting_context = ""

    if supporting_documents:
        extracted_text = await extract_documents(supporting_documents)

        if extracted_text.strip():
            ingest_documents(extracted_text, batch_id)

            supporting_context = retrieve_context(
                topic=topic,
                batch_id=batch_id,
            )
    print('<<-context->>')
    print(supporting_context)

    state = await planning_writer.ainvoke({
        "topic": topic,
        "supporting_context": supporting_context,
        "plan": None,
        "mode": "closed_book",
        "needs_research": False,
        "queries": [],
        "evidence": [],
        "sections": [],
    })

    plan = state.get("plan")

    if plan is None:
        raise ValueError("The planner did not return an outline")

    approval_id = uuid4().hex
    state["document_batch_id"] = batch_id
    pending_plans[approval_id] = state

    return {
        "approval_id": approval_id,
        "topic": topic,
        "mode": state.get("mode", "closed_book"),
        "needs_research": state.get("needs_research", False),
        "source_count": len(state.get("evidence", [])),
        "document_names": [
            file.filename for file in supporting_documents or []
        ],
        "blog_title": plan.blog_title,
        "sections": [task.model_dump() for task in plan.tasks],
    }


@router.get("/generate")
async def generate_blog(approval_id: str = Query(..., min_length=8)):
    approved_state = pending_plans.pop(approval_id, None)
    if approved_state is None:
        return StreamingResponse(
            iter([_event(error="This approval has expired or was already used.")]),
            media_type="application/x-ndjson",
            status_code=410,
        )
    return StreamingResponse(
        run_graph(approved_state),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
