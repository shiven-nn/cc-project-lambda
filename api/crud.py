from sqlalchemy.orm import Session
from .models import Function

def create_function(db: Session, func: dict):
    db_func = Function(**func)
    db.add(db_func)
    db.commit()
    db.refresh(db_func)
    return db_func

def get_functions(db: Session):
    return db.query(Function).all()

def get_function(db: Session, func_id: int):
    return db.query(Function).filter(Function.id == func_id).first()

def update_function(db: Session, func_id: int, func: dict):
    db_func = get_function(db, func_id)
    if db_func:
        for key, value in func.items():
            setattr(db_func, key, value)
        db.commit()
        db.refresh(db_func)
    return db_func

def delete_function(db: Session, func_id: int):
    db_func = get_function(db, func_id)
    if db_func:
        db.delete(db_func)
        db.commit()
    return db_func