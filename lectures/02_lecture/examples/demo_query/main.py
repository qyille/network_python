from fastapi import FastAPI, Request
from demo_query import posts
from fastapi.responses import JSONResponse

app = FastAPI(debug=True)
app.include_router(posts.router, prefix="/posts", tags=["posts"])


@app.exception_handler(IndexError)
def index_error_handler(request: Request, exc: IndexError):
    return JSONResponse(status_code=404, content={"message": "No such element"})


@app.get("/")
def get_index():
    return "Hello!"
