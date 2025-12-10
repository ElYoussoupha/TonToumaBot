from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.api.v1.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"/api/v1/openapi.json"
)

# Set all CORS enabled origins
if True: # settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix="/api/v1")

# Serve uploaded files (audio) statically
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print(f"Validation Error: {exc}")
    # Log to file
    with open("validation_errors.txt", "a") as f:
        f.write(f"Validation Error: {exc}\n")
        f.write(f"Errors: {exc.errors()}\n")
        
    # Filter out binary data from error details to avoid UnicodeDecodeError
    errors = []
    for error in exc.errors():
        new_error = error.copy()
        if "input" in new_error:
            input_val = new_error["input"]
            if isinstance(input_val, bytes):
                new_error["input"] = f"<binary data: {len(input_val)} bytes>"
            elif isinstance(input_val, str) and len(input_val) > 1000:
                 new_error["input"] = input_val[:100] + "..."
        errors.append(new_error)
        
    return JSONResponse(
        status_code=422,
        content={"detail": jsonable_encoder(errors)},
    )

@app.get("/")
async def root():
    return RedirectResponse(url="/admin")

