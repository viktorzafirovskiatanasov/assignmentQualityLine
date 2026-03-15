from datetime import datetime, timedelta
from pathlib import Path
from typing import Generator, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy import case, func
from sqlalchemy.orm import Session
from starlette.requests import Request

from database import Base, ManualTest, SessionLocal, engine

app = FastAPI(title="Yield Monitor")
Base.metadata.create_all(bind=engine)

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

PART_NUMBERS = ["001PN001", "002PN002", "003PN003"]


class ManualTestCreate(BaseModel):
    serial_number: str = Field(..., min_length=1, max_length=100)
    part_number: str
    status: bool


class ManualTestOut(BaseModel):
    id: int
    serial_number: str
    part_number: str
    timestamp: datetime
    status: bool

    class Config:
        from_attributes = True


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def read_index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "part_numbers": PART_NUMBERS,
        },
    )


@app.get("/script")
def get_script_file():
    return FileResponse(BASE_DIR / "test_yield.py", media_type="text/plain", filename="test_yield.py")


@app.post("/tests", response_model=ManualTestOut)
def create_test(payload: ManualTestCreate, db: Session = Depends(get_db)):
    if payload.part_number not in PART_NUMBERS:
        raise HTTPException(status_code=400, detail="Invalid part number")

    cleaned_serial = payload.serial_number.strip()
    if not cleaned_serial:
        raise HTTPException(status_code=400, detail="Serial number is required")

    record = ManualTest(
        serial_number=cleaned_serial,
        part_number=payload.part_number,
        status=payload.status,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@app.get("/tests", response_model=list[ManualTestOut])
def get_tests(db: Session = Depends(get_db)):
    return db.query(ManualTest).order_by(ManualTest.timestamp.desc(), ManualTest.id.desc()).all()


@app.get("/stats")
def get_stats(selected_part: Optional[str] = None, db: Session = Depends(get_db)):
    rows = (
        db.query(
            ManualTest.part_number.label("part_number"),
            func.count(ManualTest.id).label("total_tested"),
            func.sum(case((ManualTest.status.is_(True), 1), else_=0)).label("passed_units"),
        )
        .group_by(ManualTest.part_number)
        .all()
    )

    stats = []
    for part_number in PART_NUMBERS:
        match = next((row for row in rows if row.part_number == part_number), None)
        total = int(match.total_tested) if match else 0
        passed = int(match.passed_units) if match and match.passed_units is not None else 0
        yield_percentage = round((passed / total) * 100, 2) if total else 0.0
        stats.append(
            {
                "part_number": part_number,
                "total_tested": total,
                "passed_units": passed,
                "failed_units": total - passed,
                "yield_percentage": yield_percentage,
            }
        )

    if selected_part:
        part_stat = next((item for item in stats if item["part_number"] == selected_part), None)
        if not part_stat:
            raise HTTPException(status_code=404, detail="Part number not found")
        return part_stat

    return stats


@app.get("/daily")
def get_daily(db: Session = Depends(get_db)):
    today = datetime.now().date()
    start_date = today - timedelta(days=6)

    rows = (
        db.query(
            func.date(ManualTest.timestamp).label("day"),
            func.count(ManualTest.id).label("count"),
        )
        .filter(ManualTest.timestamp >= datetime.combine(start_date, datetime.min.time()))
        .group_by(func.date(ManualTest.timestamp))
        .all()
    )

    row_map = {str(row.day): int(row.count) for row in rows}
    result = []
    for offset in range(7):
        current_day = start_date + timedelta(days=offset)
        result.append({"date": current_day.isoformat(), "count": row_map.get(current_day.isoformat(), 0)})
    return result
