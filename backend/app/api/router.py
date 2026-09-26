from fastapi import APIRouter

from app.api.routes import books, chat, graph

api_router = APIRouter()
api_router.include_router(books.router)
api_router.include_router(chat.router)
api_router.include_router(graph.router)