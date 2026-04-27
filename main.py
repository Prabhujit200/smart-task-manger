from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from passlib.context import CryptContext

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = "sqlite:///./tasks.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------- USERS TABLE ----------------
class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(String)

# ---------------- TASK TABLE ----------------
class TaskDB(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    due_date = Column(String)
    priority = Column(String)
    status = Column(String)
    username = Column(String)

Base.metadata.create_all(bind=engine)

# ---------------- MODELS ----------------
class User(BaseModel):
    username: str
    password: str

class Task(BaseModel):
    title: str
    description: str
    due_date: str
    priority: str
    status: str
    username: str

# ---------------- AUTH APIs ----------------
@app.post("/signup")
def signup(user: User):
    db = SessionLocal()

    existing = db.query(UserDB).filter(UserDB.username == user.username).first()
    if existing:
        db.close()
        return {"error": "User already exists"}

    hashed_password = pwd_context.hash(user.password)

    new_user = UserDB(username=user.username, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.close()

    return {"message": "User created successfully"}

@app.post("/login")
def login(user: User):
    db = SessionLocal()

    existing = db.query(UserDB).filter(UserDB.username == user.username).first()

    if not existing:
        db.close()
        return {"error": "Invalid username or password"}

    if not pwd_context.verify(user.password, existing.password):
        db.close()
        return {"error": "Invalid username or password"}

    db.close()
    return {"message": "Login successful"}

# ---------------- TASK APIs ----------------
@app.get("/tasks/{username}")
def get_tasks(username: str):
    db = SessionLocal()
    tasks = db.query(TaskDB).filter(TaskDB.username == username).all()

    result = []
    for task in tasks:
        result.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "due_date": task.due_date,
            "priority": task.priority,
            "status": task.status,
            "username": task.username
        })

    db.close()
    return result

@app.post("/tasks")
def create_task(task: Task):
    db = SessionLocal()

    new_task = TaskDB(
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        priority=task.priority,
        status=task.status,
        username=task.username
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    db.close()
    return {"message": "Task added"}

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: Task):
    db = SessionLocal()
    existing_task = db.query(TaskDB).filter(TaskDB.id == task_id).first()

    if not existing_task:
        db.close()
        return {"error": "Task not found"}

    existing_task.title = task.title
    existing_task.description = task.description
    existing_task.due_date = task.due_date
    existing_task.priority = task.priority
    existing_task.status = task.status
    existing_task.username = task.username

    db.commit()
    db.close()

    return {"message": "Task updated"}

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    db = SessionLocal()
    task = db.query(TaskDB).filter(TaskDB.id == task_id).first()

    if not task:
        db.close()
        return {"error": "Task not found"}

    db.delete(task)
    db.commit()
    db.close()

    return {"message": "Task deleted"}