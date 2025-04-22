from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from . import crud
from .models import get_db
from .execution import execute_function
import logging
import time  # Add for timestamp

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def register_dynamic_route(app: FastAPI, route: str, func_id: int):
    async def dynamic_endpoint(payload: dict, db: Session = Depends(get_db)):
        func_data = crud.get_function_by_route(db, route)
        if not func_data:
            raise HTTPException(status_code=404, detail="Function not found")
        result, response_time, errors, resources = await execute_function(func_data, payload)
        if errors:
            raise HTTPException(status_code=500, detail=errors)
        # Log metrics
        logger.info(f"Metrics for {route}: response_time={response_time}, resources={resources}, errors={errors}")
        return {"result": result}
    app.add_api_route(
        path=route,
        endpoint=dynamic_endpoint,
        methods=["POST"],
        response_model=dict,
        name=f"execute_{func_id}"
    )
    logger.info(f"Registered route: {route}")

@app.on_event("startup")
async def startup():
    db = next(get_db())
    for func in crud.get_functions(db):
        register_dynamic_route(app, func["route"], func["id"])

@app.get("/")
async def root():
    return {"message": "Serverless Platform"}

@app.post("/functions/")
async def create_func(func: dict, db: Session = Depends(get_db)):
    result = crud.create_function(db, func)
    register_dynamic_route(app, result["route"], result["id"])
    return result

@app.get("/functions/")
async def list_funcs(db: Session = Depends(get_db)):
    return crud.get_functions(db)

@app.get("/functions/{func_id}")
async def read_func(func_id: int, db: Session = Depends(get_db)):
    func = crud.get_function_by_id(db, func_id)
    if not func:
        raise HTTPException(status_code=404, detail="Function not found")
    return func

@app.put("/functions/{func_id}")
async def update_func(func_id: int, func: dict, db: Session = Depends(get_db)):
    result = crud.update_function(db, func_id, func)
    if not result:
        raise HTTPException(status_code=404, detail="Function not found")
    return result

@app.delete("/functions/{func_id}")
async def delete_func(func_id: int, db: Session = Depends(get_db)):
    result = crud.delete_function(db, func_id)
    if not result:
        raise HTTPException(status_code=404, detail="Function not found")
    return result

@app.post("/execute/{func_id}")
async def execute(func_id: int, payload: dict, db: Session = Depends(get_db)):
    func = crud.get_function_by_id(db, func_id)
    if not func:
        raise HTTPException(status_code=404, detail="Function not found")
    result, response_time, errors, resources = await execute_function(func, payload)
    if errors:
        raise HTTPException(status_code=500, detail=errors)
    logger.info(f"Metrics for func_id {func_id}: response_time={response_time}, resources={resources}, errors={errors}")
    return {"result": result}

@app.get("/metrics/")
async def get_metrics(route: str = Query(None), db: Session = Depends(get_db)):
    if route:
        func = crud.get_function_by_route(db, route)
        if not func:
            raise HTTPException(status_code=404, detail="Function not found")
        # Return a single metric as a list for consistency
        metrics = [{
            "route": route,
            "function_id": func["id"],
            "response_time": 0.1,  # Placeholder (replace with real data)
            "cpu_usage": "0.1 cores",
            "memory_usage": "128Mi",
            "resources": {"cpu": "0.1 cores", "memory": "128Mi"},
            "timestamp": int(time.time()),  # Unix timestamp
            "errors": None  # Placeholder
        }]
    else:
        # Return metrics for all functions (placeholder)
        funcs = crud.get_functions(db)
        metrics = [
            {
                "route": func["route"],
                "function_id": func["id"],
                "response_time": 0.1,
                "cpu_usage": "0.1 cores",
                "memory_usage": "128Mi",
                "resources": {"cpu": "0.1 cores", "memory": "128Mi"},
                "timestamp": int(time.time()),
                "errors": None
            } for func in funcs
        ]
    return metrics