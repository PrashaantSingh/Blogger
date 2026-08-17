
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
import json
from app.graph.workflow import blog_writer
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def run_graph(topic: str):
    final_blog_content = None
    blog_title = None
    
    task_sections = {}

    async for chunk in blog_writer.astream(
        {"topic": topic},
        stream_mode="tasks"
    ):
        name = chunk.get("name")
        result = chunk.get("result")
        task_id = chunk.get("id")
        
        task_input = chunk.get("input", {})
        if hasattr(task_input, "model_dump"):
            task_input_dict = task_input.model_dump()
        elif hasattr(task_input, "dict"):
            task_input_dict = task_input.dict()
        elif isinstance(task_input, dict):
            task_input_dict = task_input
        else:
            task_input_dict = {}


        section_data = task_input_dict.get("section")
        section_title = None
        if isinstance(section_data, dict):
            section_title = section_data.get("title")
        elif hasattr(section_data, "title"):
            section_title = section_data.title

        if not section_title and isinstance(result, dict) and "section" in result:
            res_sec = result.get("section")
            section_title = res_sec.get("title") if isinstance(res_sec, dict) else getattr(res_sec, "title", None)


        if section_title and task_id:
            task_sections[task_id] = section_title
        elif task_id in task_sections:
            section_title = task_sections[task_id]

        if name == "merge_sections" and result:
            final_blog_content = result.get("final_blog")
            blog_title = result.get("blog_title")

        is_completed = bool(name and result)

        event_data = {
            'id': task_id,
            'name': name,
            'completed': is_completed,
            'section': section_title
        }
        
        yield json.dumps(event_data) + "\n"

    if final_blog_content:
        final_data = {
            'finished': True, 
            'blog': final_blog_content,
            'blog_title': blog_title
        }
        yield json.dumps(final_data) + "\n"

@app.get('/generate')
async def generate_blog(topic: str = Query(..., description="The blog topic to generate")):
    return StreamingResponse(run_graph(topic), media_type="application/x-ndjson")