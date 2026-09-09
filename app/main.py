from fastapi import FastAPI

app = FastAPI(title="Banco Digital Acadêmico")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
