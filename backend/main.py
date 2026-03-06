from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from routers import auth, workspaces, boards, lists, tasks, members
from routers import websocket as ws_router

app = FastAPI(title="ArtyrTask API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth.router)
app.include_router(workspaces.router)
app.include_router(boards.router)
app.include_router(boards.board_router)
app.include_router(lists.router)
app.include_router(lists.list_router)
app.include_router(tasks.router)
app.include_router(tasks.task_router)
app.include_router(members.router)
app.include_router(ws_router.router)

@app.get("/")
def root():
    return {"message": "Welcome to ArtyrTask API"}
