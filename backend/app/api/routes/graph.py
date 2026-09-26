from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Edge
from app.schemas.graph import GraphData, GraphEdge, GraphNode

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/search", response_model=list[GraphNode])
def search_nodes(
    q: str = Query(..., min_length=1, description="노드 이름 검색어"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[GraphNode]:
    """이름(source_name/target_name)에 검색어가 포함된 노드 후보를 찾는다.

    그래프 탐색의 시작 노드를 고르기 위한 용도.
    """
    like = f"%{q}%"
    seen: dict[str, GraphNode] = {}

    src = db.execute(
        select(Edge.source_id, Edge.source_name, Edge.source_class)
        .where(Edge.source_name.ilike(like))
        .limit(limit)
    ).all()
    tgt = db.execute(
        select(Edge.target_id, Edge.target_name, Edge.target_class)
        .where(Edge.target_name.ilike(like))
        .limit(limit)
    ).all()

    for node_id, name, node_class in [*src, *tgt]:
        if node_id not in seen:
            seen[node_id] = GraphNode(
                id=node_id, label=name or node_id, node_class=node_class
            )

    return list(seen.values())[:limit]


@router.get("", response_model=GraphData)
def get_graph(
    node_id: str = Query(..., description="중심 노드 id"),
    db: Session = Depends(get_db),
) -> GraphData:
    """중심 노드에 직접 연결된 엣지와 이웃 노드를 반환한다 (1-hop)."""
    stmt = select(Edge).where(or_(Edge.source_id == node_id, Edge.target_id == node_id))
    edges = list(db.scalars(stmt))

    nodes: dict[str, GraphNode] = {}
    result_edges: list[GraphEdge] = []

    for e in edges:
        if e.source_id not in nodes:
            nodes[e.source_id] = GraphNode(
                id=e.source_id,
                label=e.source_name or e.source_id,
                node_class=e.source_class,
            )
        if e.target_id not in nodes:
            nodes[e.target_id] = GraphNode(
                id=e.target_id,
                label=e.target_name or e.target_id,
                node_class=e.target_class,
            )
        result_edges.append(
            GraphEdge(
                id=str(e.id),
                source=e.source_id,
                target=e.target_id,
                relation=e.relation,
            )
        )

    return GraphData(nodes=list(nodes.values()), edges=result_edges)
