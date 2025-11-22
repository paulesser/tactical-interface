from contextlib import asynccontextmanager
from io import BytesIO

import easyocr
import torch
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from PIL import Image

reader: None | easyocr.Reader = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global reader
    if torch.cuda.is_available():
        print("running on cuda")
    reader = easyocr.Reader(["de", "en"])
    torch.cuda.empty_cache()


app = FastAPI(
    lifespan=lifespan,
    title="OCR Backend for Sankt Interface",
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
    pil_image = Image.open(BytesIO(file)).convert("RGB")
    result = reader.readtext(image=pil_image)
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
