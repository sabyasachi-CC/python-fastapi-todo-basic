from pathlib import Path
from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import User, Task
from passlib.context import CryptContext

# create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# registration
@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", {})

@app.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse(request, "register.html", {"error": "Username already exists"})

    hash_password = pwd_context.hash(password)
    user = User(username=username, hash_password=hash_password)
    db.add(user)
    db.commit()

    return RedirectResponse(url="/login", status_code=303)

# login
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {})

@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()

    if not user:
        return templates.TemplateResponse(request, "login.html", {"error": "User not found"})

    if not pwd_context.verify(password, user.hash_password):
        return templates.TemplateResponse(request, "login.html", {"error": "Incorrect password"})

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="user_id", value=str(user.id), httponly=True)

    return response

# logout
@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("user_id")
    return response

# home page
@app.get("/", response_class=HTMLResponse)
def read_index(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    user = None
    tasks = []

    if user_id:
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user:
            tasks = db.query(Task).filter(Task.owner_id == int(user_id)).all()

    return templates.TemplateResponse(request, "index.html", {"tasks": tasks, "user": user})

# add task
@app.post("/tasks")
def add_task(request: Request, title: str = Form(...), db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    task = Task(title=title, owner_id = int(user_id))
    db.add(task)
    db.commit()

    return RedirectResponse(url="/", status_code=303)

# toggle complete
@app.post("/tasks/{task_id}/toggle")
def toggle_task(task_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == int(user_id)).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.completed = not task.completed
    db.commit()

    return RedirectResponse(url="/", status_code=303)

# delete task
@app.post("/tasks/{task_id}/delete")
def delete_task(task_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == int(user_id)).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()

    return RedirectResponse(url="/", status_code=303)

# update task
@app.post("/tasks/{task_id}/update")
def update_task(task_id: int, request: Request, title = Form(...), db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == int(user_id)).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.title = title
    db.commit()

    return RedirectResponse(url="/", status_code=303)

@app.get("/add-task", response_class=HTMLResponse)
def add_task_page(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    user = db.query(User).filter(User.id == int(user_id)).first()

    if not user:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(request, "add_task.html", {"user": user})
