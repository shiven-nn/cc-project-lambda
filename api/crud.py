from sqlalchemy.orm import Session
from . import models
import uuid

def create_function(db: Session, func: dict):
    unique_id = str(uuid.uuid4())[:8]
    route = f"/fn/{unique_id}/{func.get('route', 'default')}"
    db_func = models.Function(
        name=func['name'],
        language=func['language'],
        code=func['code'],
        timeout=func['timeout'],
        route=route,
        runtime=func.get('runtime', 'runc')  # Add runtime
    )
    db.add(db_func)
    db.commit()
    db.refresh(db_func)
    return {
        "id": db_func.id,
        "name": db_func.name,
        "language": db_func.language,
        "code": db_func.code,
        "timeout": db_func.timeout,
        "route": db_func.route,
        "runtime": db_func.runtime
    }

def get_functions(db: Session):
    funcs = db.query(models.Function).all()
    return [
        {
            "id": f.id,
            "name": f.name,
            "language": f.language,
            "code": f.code,
            "timeout": f.timeout,
            "route": f.route,
            "runtime": f.runtime
        } for f in funcs
    ]

def get_function_by_id(db: Session, func_id: int):
    func = db.query(models.Function).filter(models.Function.id == func_id).first()
    if func:
        return {
            "id": func.id,
            "name": func.name,
            "language": func.language,
            "code": func.code,
            "timeout": func.timeout,
            "route": func.route,
            "runtime": func.runtime
        }
    return None

def get_function_by_route(db: Session, route: str):
    func = db.query(models.Function).filter(models.Function.route == route).first()
    if func:
        return {
            "id": func.id,
            "name": func.name,
            "language": func.language,
            "code": func.code,
            "timeout": func.timeout,
            "route": func.route,
            "runtime": func.runtime
        }
    return None

def update_function(db: Session, func_id: int, func: dict):
    db_func = db.query(models.Function).filter(models.Function.id == func_id).first()
    if not db_func:
        return None
    unique_id = db_func.route.split('/')[2]
    route = f"/fn/{unique_id}/{func.get('route', 'default')}"
    db_func.name = func['name']
    db_func.language = func['language']
    db_func.code = func['code']
    db_func.timeout = func['timeout']
    db_func.route = route
    db_func.runtime = func.get('runtime', 'runc')  # Add runtime
    db.commit()
    db.refresh(db_func)
    return {
        "id": db_func.id,
        "name": db_func.name,
        "language": db_func.language,
        "code": db_func.code,
        "timeout": db_func.timeout,
        "route": db_func.route,
        "runtime": db_func.runtime
    }

def delete_function(db: Session, func_id: int):
    db_func = db.query(models.Function).filter(models.Function.id == func_id).first()
    if not db_func:
        return None
    db.delete(db_func)
    db.commit()
    return {"status": "success"}