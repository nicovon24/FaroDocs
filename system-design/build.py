"""Build the proposed FaroDocs system-design HTML sources and SVG exports.

The diagrams are original, data-driven figures. The installed diagram-design
exporter turns each HTML source into a standalone SVG without web fonts.
"""

from __future__ import annotations

import argparse
import html
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
COLORS = {
    "paper": "#F7F3EA",
    "surface": "#FFFEFB",
    "ink": "#17263D",
    "muted": "#526176",
    "rule": "#C9D0D5",
    "accent": "#A84128",
    "accent_wash": "#F3DFD6",
    "data_wash": "#E9EFF1",
}


@dataclass(frozen=True)
class Node:
    key: str
    x: int
    y: int
    title: str
    detail: str
    kind: str = "normal"
    width: int = 200
    height: int = 96


@dataclass(frozen=True)
class Edge:
    points: tuple[tuple[int, int], ...]
    dashed: bool = False
    accent: bool = False


@dataclass(frozen=True)
class Figure:
    slug: str
    eyebrow: str
    title: str
    subtitle: str
    description: str
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]
    footer: str


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def draw_node(node: Node) -> str:
    if node.kind == "focus":
        fill, stroke = COLORS["accent_wash"], COLORS["accent"]
    elif node.kind == "data":
        fill, stroke = COLORS["data_wash"], COLORS["rule"]
    else:
        fill, stroke = COLORS["surface"], COLORS["rule"]
    x, y, w, h = node.x, node.y, node.width, node.height
    tag = "DATA" if node.kind == "data" else "PROCESS" if node.kind == "focus" else "STEP"
    return (
        f'<g data-node="{esc(node.key)}">'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
        f'<text x="{x + 18}" y="{y + 24}" fill="{COLORS["muted"]}" '
        f'font-family="ui-monospace, Consolas, monospace" font-size="10" '
        f'letter-spacing="1.5">{tag}</text>'
        f'<text x="{x + 18}" y="{y + 53}" fill="{COLORS["ink"]}" '
        f'font-family="system-ui, sans-serif" font-size="18" font-weight="650">{esc(node.title)}</text>'
        f'<text x="{x + 18}" y="{y + 75}" fill="{COLORS["muted"]}" '
        f'font-family="system-ui, sans-serif" font-size="12">{esc(node.detail)}</text>'
        '</g>'
    )


def draw_edge(edge: Edge) -> str:
    if len(edge.points) < 2:
        raise ValueError("An edge needs at least two points")
    for first, second in zip(edge.points, edge.points[1:]):
        if first[0] != second[0] and first[1] != second[1]:
            raise ValueError(f"Non-orthogonal edge: {edge.points}")
    path = "M " + " L ".join(f"{x} {y}" for x, y in edge.points)
    stroke = COLORS["accent"] if edge.accent else COLORS["muted"]
    dash = ' stroke-dasharray="6 5"' if edge.dashed else ""
    marker = "arrow-accent" if edge.accent else "arrow"
    return (
        f'<path d="{path}" fill="none" stroke="{stroke}" stroke-width="2"'
        f'{dash} marker-end="url(#{marker})"/>'
    )


def svg(figure: Figure) -> str:
    c = COLORS
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" '
        f'width="1280" height="720" role="img" '
        f'aria-labelledby="{figure.slug}-title {figure.slug}-desc">',
        f'<title id="{figure.slug}-title">{esc(figure.title)}</title>',
        f'<desc id="{figure.slug}-desc">{esc(figure.description)}</desc>',
        '<defs>',
        f'<marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">'
        f'<path d="M 0 0 L 10 4 L 0 8" fill="none" stroke="{c["muted"]}" stroke-width="1.4"/></marker>',
        f'<marker id="arrow-accent" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">'
        f'<path d="M 0 0 L 10 4 L 0 8" fill="none" stroke="{c["accent"]}" stroke-width="1.4"/></marker>',
        '</defs>',
        f'<rect x="0" y="0" width="1280" height="720" fill="{c["paper"]}"/>',
        f'<text x="64" y="51" fill="{c["accent"]}" font-family="ui-monospace, Consolas, monospace" '
        f'font-size="12" letter-spacing="2">FARODOCS / {esc(figure.eyebrow)}</text>',
        f'<text x="64" y="97" fill="{c["ink"]}" font-family="Georgia, serif" '
        f'font-size="38">{esc(figure.title)}</text>',
        f'<text x="64" y="128" fill="{c["muted"]}" font-family="system-ui, sans-serif" '
        f'font-size="15">{esc(figure.subtitle)}</text>',
        f'<line x1="64" y1="151" x2="1216" y2="151" stroke="{c["rule"]}"/>',
    ]
    parts.extend(draw_edge(edge) for edge in figure.edges)
    parts.extend(draw_node(node) for node in figure.nodes)
    parts.extend([
        f'<line x1="64" y1="618" x2="1216" y2="618" stroke="{c["rule"]}"/>',
        f'<text x="64" y="651" fill="{c["muted"]}" font-family="system-ui, sans-serif" '
        f'font-size="14">{esc(figure.footer)}</text>',
        f'<text x="1216" y="651" text-anchor="end" fill="{c["accent"]}" '
        f'font-family="ui-monospace, Consolas, monospace" font-size="11" '
        f'letter-spacing="1.2">PROPOSED SYSTEM</text>',
        '</svg>',
    ])
    return "\n".join(parts)


FIGURES = (
    Figure(
        slug="topology",
        eyebrow="01 / TOPOLOGY",
        title="One product, clear runtime owners",
        subtitle="Next.js serves the experience; FastAPI owns document decisions; Python jobs process files.",
        description="Proposed topology: Next.js communicates with FastAPI. FastAPI stores metadata in PostgreSQL, queues work through a broker, and the worker writes private files and derived passages. A model adapter is optional.",
        nodes=(
            Node("web", 64, 218, "Next.js", "UI + short actions", "focus", 210),
            Node("api", 374, 218, "FastAPI", "auth + domain API", "normal", 210),
            Node("worker", 684, 218, "Python worker", "extract + embed", "normal", 210),
            Node("model", 994, 218, "Model adapter", "embed + answer", "normal", 210),
            Node("database", 374, 430, "PostgreSQL", "metadata + pgvector", "data", 210),
            Node("broker", 684, 430, "Job broker", "durable tasks", "data", 210),
            Node("files", 994, 430, "Private files", "originals + previews", "data", 210),
        ),
        edges=(
            Edge(((274, 266), (374, 266)), accent=True),
            Edge(((479, 314), (479, 430))),
            Edge(((584, 266), (634, 266), (634, 478), (684, 478))),
            Edge(((789, 430), (789, 314)), dashed=True),
            Edge(((894, 266), (994, 266)), dashed=True),
            Edge(((894, 286), (944, 286), (944, 478), (994, 478))),
            Edge(((894, 314), (920, 314), (920, 560), (479, 560), (479, 526)), dashed=True),
            Edge(((479, 218), (479, 184), (1099, 184), (1099, 218)), dashed=True),
        ),
        footer="Server Actions handle brief UI changes; FastAPI enforces permissions and owns persistent state.",
    ),
    Figure(
        slug="ingestion",
        eyebrow="02 / INGESTION",
        title="A file becomes located evidence",
        subtitle="Versioned originals and extraction recipes keep passages traceable after reprocessing.",
        description="Proposed ingestion flow: upload, validation, private original storage, queued job, extraction or OCR, location-aware chunks, embeddings, and PostgreSQL persistence. Processing states and failures are visible.",
        nodes=(
            Node("upload", 64, 206, "Upload", "PDF · DOCX · TXT · MD"),
            Node("validate", 304, 206, "Validate", "type + limits", "focus"),
            Node("original", 544, 206, "Original", "immutable version", "data"),
            Node("queue", 784, 206, "Queue job", "visible state + retry"),
            Node("extract", 784, 422, "Extract / OCR", "ordered source blocks"),
            Node("chunks", 544, 422, "Chunk + locate", "stable ID · page/offset"),
            Node("embed", 304, 422, "Embed", "model + recipe ID"),
            Node("persist", 64, 422, "Persist", "text + vector index", "data"),
        ),
        edges=(
            Edge(((264, 254), (304, 254))),
            Edge(((504, 254), (544, 254)), accent=True),
            Edge(((744, 254), (784, 254))),
            Edge(((884, 302), (884, 422)), dashed=True),
            Edge(((784, 470), (744, 470))),
            Edge(((544, 470), (504, 470))),
            Edge(((304, 470), (264, 470))),
        ),
        footer="PDF page coordinates are used only when extraction can support them; text fallback remains available.",
    ),
    Figure(
        slug="answer-path",
        eyebrow="03 / QUESTION PATH",
        title="An answer must carry inspectable evidence",
        subtitle="Authorization comes before retrieval; insufficient evidence ends in an explicit abstention.",
        description="Proposed question path: question, authorized document scope, hybrid lexical and vector search, evidence threshold, bounded context to a model, citation ID validation, cited answer or abstention. Source passages can be opened in their original version.",
        nodes=(
            Node("question", 64, 206, "Question", "Spanish or English"),
            Node("scope", 304, 206, "Access scope", "allowed versions only", "focus"),
            Node("retrieve", 544, 206, "Hybrid search", "full text + vector"),
            Node("evidence", 784, 206, "Evidence gate", "passages sufficient?"),
            Node("generate", 784, 422, "Generate", "bounded context"),
            Node("citations", 544, 422, "Check citations", "IDs in retrieved set"),
            Node("answer", 304, 422, "Answer + sources", "open exact passage", "data"),
            Node("abstain", 1024, 422, "Abstain", "state the evidence gap", "data"),
        ),
        edges=(
            Edge(((264, 254), (304, 254))),
            Edge(((504, 254), (544, 254)), accent=True),
            Edge(((744, 254), (784, 254))),
            Edge(((884, 302), (884, 422))),
            Edge(((984, 254), (1124, 254), (1124, 422)), dashed=True),
            Edge(((784, 470), (744, 470))),
            Edge(((544, 470), (504, 470))),
        ),
        footer="Citation ID validity is structural; semantic claim support is a later evaluation and product feature.",
    ),
    Figure(
        slug="access-and-deletion",
        eyebrow="04 / TRUST + LIFECYCLE",
        title="Access and deletion cross every data path",
        subtitle="The backend checks visibility on reads and hides documents before cleanup runs.",
        description="Proposed access path: session, document grants, scoped read endpoints, source preview. Proposed deletion path: request, tombstone, cleanup job, audit event. Cleanup covers originals, extracted passages, vectors, and previews.",
        nodes=(
            Node("session", 64, 206, "Session", "identity + workspace"),
            Node("grants", 304, 206, "Document grants", "FastAPI decision", "focus"),
            Node("read", 544, 206, "Scoped reads", "library · search · chat"),
            Node("preview", 784, 206, "Source preview", "recheck on open", "data"),
            Node("delete", 64, 422, "Delete request", "owner confirmation"),
            Node("tombstone", 304, 422, "Tombstone", "hide immediately"),
            Node("cleanup", 544, 422, "Cleanup job", "files + derived data"),
            Node("audit", 784, 422, "Audit event", "outcome, no content", "data"),
        ),
        edges=(
            Edge(((264, 254), (304, 254))),
            Edge(((504, 254), (544, 254)), accent=True),
            Edge(((744, 254), (784, 254))),
            Edge(((264, 470), (304, 470))),
            Edge(((504, 470), (544, 470))),
            Edge(((744, 470), (784, 470))),
        ),
        footer="Public readiness depends on two-user isolation, full deletion, limits, privacy, and adversarial tests.",
    ),
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--exporter",
        type=Path,
        default=Path.home() / ".agents/skills/diagram-design/scripts/export_svg.py",
        help="Path to the installed diagram-design export_svg.py",
    )
    args = parser.parse_args()
    if not args.exporter.is_file():
        parser.error(f"diagram-design exporter not found: {args.exporter}")
    for figure in FIGURES:
        html_path = HERE / f"{figure.slug}.html"
        svg_path = HERE / f"{figure.slug}.svg"
        markup = svg(figure)
        html_path.write_text(
            "<!doctype html>\n<html lang=\"en\">\n<head><meta charset=\"utf-8\">"
            f"<title>{esc(figure.title)}</title></head>\n"
            "<body style=\"margin:0;background:#F7F3EA\">\n"
            f"{markup}\n</body></html>\n",
            encoding="utf-8",
        )
        subprocess.run(
            [sys.executable, str(args.exporter), "--system-fonts", str(html_path), str(svg_path)],
            check=True,
        )
        print(f"Built {svg_path.name}")


if __name__ == "__main__":
    main()
