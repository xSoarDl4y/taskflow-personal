import os
from datetime import date
from typing import Literal
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import select
from .database import Base, engine, get_db
from .models import User, Task
from .auth import hash_password, verify_password, create_token, get_current_user
from google import genai
from dotenv import load_dotenv
import time

load_dotenv()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TaskFlow Personal API", version="1.0.0")
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:8501").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

Priority = Literal["low", "medium", "high"]

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    description: str = Field(default="", max_length=10000)
    due_date: date | None = None
    priority: Priority = "medium"
    completed: bool = False

class TaskOut(BaseModel):
    id: int
    title: str
    description: str
    due_date: date | None
    priority: str
    completed: bool
    class Config:
        from_attributes = True

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/auth/register", response_model=TokenOut)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = data.email.lower().strip()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email này đã được đăng ký.")
    user = User(email=email, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_token(user), email=user.email)

@app.post("/auth/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    email = data.email.lower().strip()
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng.")
    return TokenOut(access_token=create_token(user), email=user.email)

@app.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email}

@app.get("/tasks", response_model=list[TaskOut])
def list_tasks(
    due_on: date | None = Query(default=None),
    completed: bool | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(Task).where(Task.user_id == user.id)
    if due_on is not None:
        query = query.where(Task.due_date == due_on)
    if completed is not None:
        query = query.where(Task.completed == completed)
    query = query.order_by(Task.completed.asc(), Task.due_date.asc().nullslast(), Task.id.desc())
    return list(db.scalars(query).all())

@app.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(data: TaskIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    title = data.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="Tên công việc không được để trống.")
    task = Task(user_id=user.id, title=title, description=data.description, due_date=data.due_date, priority=data.priority, completed=data.completed)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@app.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, data: TaskIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.scalar(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    if not task:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc.")
    for field, value in data.model_dump().items():
        setattr(task, field, value)
    task.title = task.title.strip()
    if not task.title:
        raise HTTPException(status_code=422, detail="Tên công việc không được để trống.")
    db.commit()
    db.refresh(task)
    return task

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.scalar(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    if not task:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc.")
    db.delete(task)
    db.commit()
    return {"deleted": True}

class PlanIn(BaseModel):
    goal: str = Field(min_length=3, max_length=4000)
    available_hours: float = Field(default=3, ge=0.5, le=16)


@app.post("/ai/plan")
def ai_plan(
    data: PlanIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    load_dotenv(override=True)
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Chưa cấu hình GEMINI_API_KEY ở backend. Các tính năng task vẫn hoạt động."
        )

    from google import genai

    tasks = db.scalars(
        select(Task)
        .where(
            Task.user_id == user.id,
            Task.completed == False
        )
        .order_by(Task.due_date.asc().nullslast())
        .limit(30)
    ).all()

    task_text = "\n".join(
        f"- {t.title} | hạn: {t.due_date or 'chưa đặt'} | ưu tiên: {t.priority}"
        for t in tasks
    ) or "Chưa có công việc hiện tại."

    prompt = f"""
Bạn là trợ lý quản lý công việc cá nhân.
Trả lời bằng tiếng Việt, thực tế, có thứ tự ưu tiên,
ước lượng thời gian và nghỉ giải lao.
Không bịa rằng đã thay đổi dữ liệu.

Mục tiêu/ngữ cảnh: {data.goal}
Thời gian có: {data.available_hours} giờ.

Các task chưa hoàn thành:
{task_text}

Hãy lập kế hoạch hành động theo từng bước.
"""

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
            contents=prompt,
            config={
                "temperature": 0.4,
            },
        )

        plan = response.text or "Gemini chưa trả về nội dung."

        return {"plan": plan}

    
    except Exception as exc:
        print(f"Gemini error: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=502,
            detail=(
                f"Gemini error: {type(exc).__name__}: {str(exc)[:500]}"
            )
        )
    

