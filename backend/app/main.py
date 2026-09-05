from fastapi import FastAPI

app = FastAPI(title="PiggyBank")

@app.get("/health")
async def health_check():
    return {"status": "ok"}