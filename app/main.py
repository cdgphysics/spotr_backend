from fastapi import FastAPI

app = FastAPI(title="Spottr_Api")


@app.get("/")
def root():
    return {"message": "Spottr is up!"}