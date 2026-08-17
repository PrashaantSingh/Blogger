from langgraph.graph import StateGraph,START,END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()
from pydantic import BaseModel,Field
from typing import Annotated,List,TypedDict
import operator
from langgraph.types import Send



class Section(BaseModel):
    id: int = Field(
        description="A unique identifier for the section."
    )
    title: str = Field(
        description="The title of an actual section that will appear in the final blog."
    )
    description: str = Field(
        description="A brief summary of the specific content that should be covered in this section."
    )

class OutlineSchema(BaseModel):
    outline:List[Section]
    blog_title:str=Field(description='a concise,crisp and catchy blog title in markdown formatting')

class SectionDraft(BaseModel):
    section_id:int
    title:str
    content:str

class BlogState(BaseModel):
    topic: str
    blog_title:str=''
    outline: List[Section] = []
    draft_sections: Annotated[List[SectionDraft], operator.add] = []
    final_blog: str = ""



model=ChatOpenAI(base_url="http://localhost:11434/v1",model='gemma')

graph=StateGraph(BlogState)

from datetime import datetime


def generate_outline(state: BlogState):
    llm = model.with_structured_output(OutlineSchema)
    prompt = f"""
You are an expert editor and essayist.
Create a structured 5–7 section outline and an engaging title for an in-depth, high-quality article on:
"{state.topic}"

EDITORIAL PRINCIPLES:
1. Tone Matching: Adapt your tone and terminology naturally to the subject matter (e.g., narrative and evocative for history/pop culture; rigorous and analytical for science/tech).
2. Logical Narrative Arc: Ensure each section flows naturally into the next to build a complete, cohesive story or guide.
3. Natural Headings: Use clear, engaging section titles. Avoid generic academic or tech jargon unless the topic explicitly calls for it.
4. Unique Integer IDs: Assign clean sequential integers starting at 1 (1, 2, 3, ...).

SECTION SPECIFICATIONS:
- id: Sequential number (1, 2, 3, ...)
- title: Natural, engaging section heading (e.g., "From Peter Parker to Spider-Man: The Radioactive Spider", NOT "System Architecture of Powers")
- description: Specific points, events, concepts, or context to cover in this section.
"""
    result = llm.invoke(prompt)
    return {
        'outline': result.outline,
        'blog_title': result.blog_title
    }

def fanout_writers(state: BlogState):
    # Formatted outline summary passed to every worker for cross-section awareness
    outline_summary = "\n".join(
        [f"{s.id}. {s.title}: {s.description}" for s in state.outline]
    )
    return [
        Send("writer", {
            "topic": state.topic,
            "section": sec,
            "full_outline": outline_summary
        })
        for sec in state.outline
    ]

def writer(state: dict):
    topic = state["topic"]
    section = state["section"]
    full_outline = state.get("full_outline", "")

    llm = model.with_structured_output(SectionDraft)

    prompt = f"""
You are a skilled writer contributing one chapter/section to a comprehensive, publication-ready piece.

ARTICLE OUTLINE FOR CONTEXT:
{full_outline}

YOUR SECTION:
- Topic: {topic}
- Section {section.id}: {section.title}
- Focus: {section.description}

WRITING GUIDELINES:
1. Tone & Style: Match the natural voice of the subject matter. Make it engaging, informative, and rich with concrete details, examples, and context.
2. Structure: Use standard Markdown formatting (paragraphs, occasional bullet points or bold highlights where they add clarity).
3. Seamless Flow: Focus entirely on this section's specific focus so it fits cleanly into the broader piece without repeating other sections.
4. Clean Content:
   - Do NOT include the section title as a header in your output (it is added automatically).
   - Do NOT include meta-commentary like "In this article", "As we saw earlier", or "In conclusion".
   - Avoid generic AI buzzwords (e.g., "delve into", "testament to", "tapestry of", "in today's world").
"""

    result = llm.invoke(prompt)

    return {
        "draft_sections": [
            SectionDraft(
                section_id=section.id,
                title=section.title,
                content=result.content.strip()
            )
        ]
    }

def merge_sections(state: BlogState):
    sections = sorted(
        state.draft_sections,
        key=lambda x: x.section_id
    )

    content = "\n\n".join(
        f"## {section.title}\n\n{section.content}"
        for section in sections
    )

    return {
        'blog_title':state.blog_title,
        "final_blog": content
    }


graph.add_node('generate_outline',generate_outline)
graph.add_node('writer',writer)
graph.add_node('merge_sections',merge_sections)

graph.add_conditional_edges('generate_outline',fanout_writers,['writer'])
graph.add_edge(START,'generate_outline')
graph.add_edge('writer','merge_sections')
graph.add_edge('merge_sections',END)

blog_writer=graph.compile()