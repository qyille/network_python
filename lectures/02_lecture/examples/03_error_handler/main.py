from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI(debug=True)


POSTS = ["Hello world!", "Some other post"]


@app.exception_handler(IndexError)
def index_error_handler(request: Request, exc: IndexError):
    return JSONResponse(status_code=404, content={"message": "No such element"})


@app.exception_handler(ValueError)
def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"message": "Invalid argument"})


@app.get("/")
def get_index():
    return "Hello!"


@app.get("/posts")
async def get_posts():
    return {"posts": POSTS}


@app.get("/posts/mine")
def get_post_mine():
    return {"posts": ["User posts"]}


@app.get("/posts/{post_id}")
async def get_post(post_id: int):
    if post_id == 42:
        raise HTTPException(status_code=418, detail="42 is forbidden.")
    if post_id == 67:
        raise ValueError()
    return {"post": POSTS[post_id]}
