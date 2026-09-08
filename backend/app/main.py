from fastapi import FastAPI

from app.api.routes import auth
from app.api.routes import savings_goals
from app.api.routes import users

app = FastAPI(title="PiggyBank")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(savings_goals.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}