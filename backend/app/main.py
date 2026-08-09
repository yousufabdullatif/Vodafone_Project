from fastapi import FastAPI


app = FastAPI(
    title="Telecom Cell Health API",
    version="1.0.0"
)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok"
    }

    