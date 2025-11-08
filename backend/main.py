from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import csv
import os

from .score import score_lead
from .llm import generate_summary

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Path to CSV file
DATA_FILE = "data/leads.csv"


def save_lead(data, score, label):
    """Save each lead submission into a CSV file."""
    # Make sure the data folder exists
    os.makedirs("data", exist_ok=True)

    file_exists = os.path.exists(DATA_FILE)

    with open(DATA_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(
                [
                    "Company",
                    "Website",
                    "Service",
                    "Budget",
                    "Timeline",
                    "Goal",
                    "Email",
                    "Phone",
                    "Company_Size",
                    "Score",
                    "Label",
                ]
            )
        writer.writerow(
            [
                data["company"],
                data["website"],
                data["service"],
                data["budget"],
                data["timeline"],
                data["goal"],
                data["email"],
                data["phone"],
                data["company_size"],
                score,
                label,
            ]
        )


@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/submit", response_class=HTMLResponse)
async def submit_lead(
    request: Request,
    company: str = Form(""),
    website: str = Form(""),
    service: str = Form("SEO"),
    budget: str = Form("<2k"),
    timeline: str = Form("now"),
    goal: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    company_size: str = Form("1-10"),
):
    data = {
        "company": company,
        "website": website,
        "service": service,
        "budget": budget,
        "timeline": timeline,
        "goal": goal,
        "email": email,
        "phone": phone,
        "company_size": company_size,
    }

    # scoring + summary
    score, label = score_lead(budget, timeline, company_size, goal)
    summary = generate_summary(data, score, label)

    # ✅ save to CSV
    save_lead(data, score, label)

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "data": data,
            "score": score,
            "label": label,
            "summary": summary,
        },
    )

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    headers = []
    rows = []

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader, [])
            rows = list(reader)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "headers": headers,
            "rows": rows,
        },
    )
