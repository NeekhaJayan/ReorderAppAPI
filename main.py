from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models
from starlette.responses import RedirectResponse
from routers import auth
from starlette import status

app = FastAPI()
origins = [
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "https://characteristic-tunnel-uniprotkb-bind.trycloudflare.com",
    "http://127.0.0.1:8000/auth/shopify",
    "https://deca-development-store.myshopify.com","https://deca-development-store.myshopify.com/admin/oauth/authorize"
]
# Allow CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow specific origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)
@app.get("/")
async def root():
    return RedirectResponse(url="/auth",status_code=status.HTTP_302_FOUND)

app.include_router(auth.router)

