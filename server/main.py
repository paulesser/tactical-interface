from contextlib import asynccontextmanager

import easyocr
import torch
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pyinstrument import Profiler

reader: None | easyocr.Reader = None
PROFILING = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    global reader
    reader = easyocr.Reader(["de", "en"])
    yield
    reader = None
    torch.cuda.empty_cache()


app = FastAPI(
    title="OCR Backend for Sankt Interface",
    lifespan=lifespan,
    description="""

    """,
)

# Handle CORS
origins = [
    r"http://localhost(:[0-9]+)?",
    r"http://127\.0\.0\.1(:[0-9]+)?",
    r"file://.*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex="|".join(origins),  # Joining regex patterns
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if PROFILING:

    @app.middleware("http")
    async def profile_request(request: Request, call_next):
        profiling = request.query_params.get("profile", False)
        if profiling:
            profiler = Profiler()
            profiler.start()
            await call_next(request)
            profiler.stop()
            return HTMLResponse(profiler.output_html())
        else:
            return await call_next(request)


@app.get(
    "/",
    response_class=RedirectResponse,
    include_in_schema=False,
)
async def index():
    return "/docs"


@app.post(
    "/ocr",
    description="""

    """,
)
async def ocr(
    image: UploadFile = File(...),
) -> str:
    assert reader is not None
    file = image.file.read()
    result = reader.readtext(image=file)
    stringResult = ""
    for r in result:
        if isinstance(r, tuple):
            for key in r[1]:
                if type(key) is str and (
                    key.encode("ascii", errors="ignore").decode("ascii")
                ):
                    if key != " ":
                        stringResult += key

    return stringResult
