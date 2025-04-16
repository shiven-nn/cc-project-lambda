from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .models import Base, Function, get_db, engine
from .crud import create_function, get_function, get_functions, update_function, delete_function
from .execution import execute_function
from .metrics import Metrics

app = FastAPI()
metrics = Metrics()

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {"message": "Serverless Platform"}

@app.post("/functions/")
async def create_func(func: dict, db: Session = Depends(get_db)):
    return create_function(db, func)

@app.get("/functions/")
async def list_funcs(db: Session = Depends(get_db)):
    return get_functions(db)

@app.get("/functions/{func_id}")
async def read_func(func_id: int, db: Session = Depends(get_db)):
    func = get_function(db, func_id)
    if not func:
        raise HTTPException(status_code=404, detail="Function not found")
    return func

@app.put("/functions/{func_id}")
async def update_func(func_id: int, func: dict, db: Session = Depends(get_db)):
    return update_function(db, func_id, func)

@app.delete("/functions/{func_id}")
async def delete_func(func_id: int, db: Session = Depends(get_db)):
    return delete_function(db, func_id)

@app.post("/execute/{func_id}")
async def execute(func_id: int, payload: dict, db: Session = Depends(get_db)):
    func = get_function(db, func_id)
    if not func:
        raise HTTPException(status_code=404, detail="Function not found")
    result, response_time, errors, resources = await execute_function(func, payload)
    metrics.record(func_id, response_time, errors, resources)
    return {"result": result}

@app.get("/metrics/")
async def get_metrics(func_id: int = None):
    return metrics.get_metrics(func_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)