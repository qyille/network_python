from fastapi import FastAPI, Request, HTTPException
from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(debug=True)


class Post(BaseModel):
    id: int
    text: str


POSTS = [
    Post(id=0, text="post"),
    Post(id=1, text="Some other post"),
]


@app.exception_handler(IndexError)
def index_error_handler(request: Request, exc: IndexError):
    return JSONResponse(status_code=404, content={"message": "No such element"})


@app.get("/")
def get_index():
    return "Hello!"


@app.get("/posts")
async def get_posts():
    return {"posts": POSTS}


@app.post("/posts", status_code=status.HTTP_201_CREATED)
async def create_post(post: Post):
    for p in POSTS:
        if p.id == post.id:
            return {"message": "Post already added"}
    POSTS.append(post)
    return {"message": "Post added"}


@app.get("/posts/mine")
def get_post_mine():
    return {"posts": ["User posts"]}


@app.get("/posts/{post_id}")
async def get_post(post_id: int):
    if post_id == 42:
        raise HTTPException(status_code=418, detail="42 is forbidden.")
    for post in POSTS:
        if post.id == post_id:
            return {"post": post}
