from .models import Base, engine

def init_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database tables dropped and recreated.")

if __name__ == "__main__":
    init_db()