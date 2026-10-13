"""Command-line entry point for the Blogger generation workflow.

The implementation lives under ``backend.app.graph`` so the API and CLI use the
same router, research, planning, worker, and reducer pipeline.
"""

import argparse
import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.graph.workflow import blog_writer


def run(topic: str) -> str:
    result = blog_writer.invoke(
        {
            "topic": topic,
            "plan": None,
            "mode": "closed_book",
            "needs_research": False,
            "queries": [],
            "evidence": [],
            "sections": [],
        }
    )
    return result["final"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a technical blog post")
    parser.add_argument("topic", help="Topic to write about")
    args = parser.parse_args()
    print(run(args.topic))
