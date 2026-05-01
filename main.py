from fastapi import FastAPI, Body
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import requests
import json
import re
import os
import shutil

from app.kb_service import search_knowledge_base, build_kb_index
from app.ai_service import generate_ai_reply

app = FastAPI()

class EmailBookingRequest(BaseModel):
    message: str

@app.on_event("startup")
def startup_event():
    print("Voice and Email AI unified server starting up...")
    os.makedirs("bookings", exist_ok=True)
    os.makedirs("archive", exist_ok=True)


BACKEND_FORWARD_URL = "https://your-backend-colleague.com/api/new-booking"

ALLOWED_ACTIVITIES = [
    "Bubble Soccer",
    "Combat Archery",
    "Dodgeball",
    "Nerf Wars",
    "Football Darts",
    "Goggle Football",
    "Sports Day",
    "Glowball Disco UV"
]

LAST_SUBMISSION = {}

class BookingLead(BaseModel):
    name: str
    planning: str
    city: str
    people: str
    experience: str
    activity: str = ""
    date: str
    time: str
    email: EmailStr
    phone: str


def normalize_date(raw_date: str):
    today = datetime.utcnow().date()
    text = raw_date.lower().strip()

    if text == "today":
        return str(today)

    if text == "tomorrow":
        return str(today + timedelta(days=1))

    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6
    }

    for day, idx in weekdays.items():
        if f"next {day}" in text or text == day:
            days_ahead = (idx - today.weekday() + 7) % 7
            if days_ahead == 0:
                days_ahead = 7
            # if "next" in text:
            #     days_ahead += 7
            # if days_ahead == 0:
            #     days_ahead = 7
            return str(today + timedelta(days=days_ahead))

    match = re.search(r"(\d{1,2})\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)", text)
    if match:
        return raw_date

    return raw_date


def normalize_activity(activity: str):
    for item in ALLOWED_ACTIVITIES:
        if item.lower() in activity.lower():
            return item
    return "Bubble Soccer"

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "Spartacus Unified AI Middleware",
    }

def smart_faq_rules(question: str):
    q = question.lower()

    # PAYMENT
    if any(k in q for k in ["pay", "payment", "deposit", "cost", "price"]):
        return "We don’t take payment on the day. A forty nine pound deposit secures the booking and the remaining balance is due before the event."

    # CHANGE NUMBERS
    if any(k in q for k in ["change numbers", "change people", "final numbers", "update numbers"]):
        return "Final numbers can usually be adjusted up to 14 days before the event. Within 14 days numbers are normally locked."

    # WEATHER
    if any(k in q for k in ["rain", "weather", "snow", "storm"]):
        return "Sessions usually run in rain on all-weather pitches. Only severe weather may affect bookings."

    # WHAT TO WEAR
    if any(k in q for k in ["wear", "clothes", "shoes", "attire"]):
        return "Please wear sportswear and trainers or astros. No metal studs or blades."

    # LIVERPOOL FOOD
    if any(k in q for k in ["food", "eat", "catering", "cake", "meal"]) and "liverpool" in q:
        return "Liverpool offers a private party room for £50. You may bring your own food, bring cake, or order food in."

    # MANCHESTER FOOD
    if any(k in q for k in ["food", "eat", "catering", "cake", "meal"]) and "manchester" in q:
        return "Manchester offers pizza at £11 each with pre-order. Birthday cake is allowed."

    # GENERIC FOOD/DRINK
    if any(k in q for k in ["food", "eat", "catering", "cake", "meal", "drink", "alcohol", "beverage"]):
        return "Food and drink options vary by city. For example, Liverpool allows bringing your own food and cake in a party room, while Manchester offers pre-ordered pizza and allows birthday cakes. Our team can confirm the exact food options for your chosen location by email."

    # BEST PACKAGE
    if any(k in q for k in ["best package", "18 people", "large group", "big group"]):
        return "For larger groups, Spartacus Cup or Spartacus Cup Max are usually the best options for maximum game time and value."

    # HOW LONG
    if any(k in q for k in ["how long", "duration", "time limits", "how many hours"]):
        return "Packages are usually 60, 90, or 120 minutes depending on the option selected."

    return None

@app.post("/api/faq/ask")
def ask_faq(payload: dict = Body(...)):
    # Log the raw payload to a file so we can debug exactly what the Voice AI is sending
    with open("faq_logs.txt", "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    print(f"\nRAW PAYLOAD: {payload}")

    question = payload.get("question") or payload.get("query") or payload.get("text") or payload.get("faq_question") or payload.get("message") or ""
    # In case it's nested:
    if not question and "args" in payload:
        args = payload["args"]
        question = args.get("question") or args.get("query") or args.get("text") or ""
        
    question = str(question).strip()
    print(f"\nFAQ Question Extracted: {question}")

    # STEP 1: Smart Rules
    answer = smart_faq_rules(question)

    # STEP 2: KB Search
    if not answer:
        kb_results = search_knowledge_base(question, top_k=1)
        if kb_results and kb_results[0]['score'] > 0.30:  # Lowered threshold from 0.4 to 0.30 to catch valid semantic matches
            answer = kb_results[0]['text']

    # STEP 3: Fallback
    if not answer:
        answer = "I’m sorry, I don’t have that exact detail right now. Our team can confirm it for you by email."

    print(f"FAQ Answer: {answer}")

    return {
        "success": True,
        "question": question,
        "answer": answer,
        "done": True
    }

# @app.post("/api/faq/ask")
# def ask_faq(payload: dict = Body(...)):

#     question = payload.get("question", "").strip()
#     print(f"\nFAQ Question: {question}")

#     answer = search_kb(question)

#     if not answer:
#         answer = "I’m sorry, I don’t have that exact detail right now. Our team can confirm it for you by email."

#     print(f"FAQ Answer: {answer}")

#     return {
#         "success": True,
#         "question": question,
#         "answer": answer
#     }

@app.post("/api/voice/booking-lead")
def receive_booking(data: BookingLead):

    payload = data.dict()

    payload["date"] = normalize_date(payload["date"])
    payload["activity"] = normalize_activity(payload["activity"])
    payload["source"] = "voice_ai"
    payload["received_at"] = datetime.utcnow().isoformat()

    unique_key = payload["phone"] + payload["date"] + payload["time"]

    if LAST_SUBMISSION.get(unique_key):
        return {
            "success": True,
            "message": "Duplicate booking ignored"
        }

    LAST_SUBMISSION[unique_key] = True

    print("\n===== FINAL BOOKING RECEIVED =====")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    booking_id = f"booking_{payload['phone']}_{payload['date']}_{payload['time']}".replace(":", "").replace(" ", "_")
    file_path = os.path.join("bookings", f"{booking_id}.json")
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)

    try:
        response = requests.post(
            BACKEND_FORWARD_URL,
            json=payload,
            timeout=10
        )

        return {
            "success": True,
            "message": "Booking received and forwarded",
            "backend_status": response.status_code
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@app.get("/api/bookings")
def get_bookings():
    bookings_list = []
    if os.path.exists("bookings"):
        for filename in os.listdir("bookings"):
            if filename.endswith(".json"):
                file_path = os.path.join("bookings", filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        data["booking_id"] = filename.replace(".json", "")
                        bookings_list.append(data)
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
    return {"success": True, "data": bookings_list}

@app.post("/api/bookings/{booking_id}/acknowledge")
def acknowledge_booking(booking_id: str):
    source_path = os.path.join("bookings", f"{booking_id}.json")
    dest_path = os.path.join("archive", f"{booking_id}.json")
    
    if not os.path.exists(source_path):
        return {"success": False, "message": "Booking not found or already acknowledged"}
        
    try:
        shutil.move(source_path, dest_path)
        return {"success": True, "message": f"Booking {booking_id} acknowledged and archived"}
    except Exception as e:
        return {"success": False, "message": f"Error archiving booking: {e}"}

@app.post("/reply")
def reply_to_customer(request: EmailBookingRequest):
    # Search knowledge base for FAQs based on the message
    kb_results = search_knowledge_base(request.message)

    # Compile context including the backend's single message
    context = {
        "backend_message": request.message,
        "knowledge_base_results": kb_results,
    }

    # Generate AI Reply based on context
    ai_reply = generate_ai_reply(context)

    return {
        "status": "success",
        "reply": ai_reply,
    }

@app.post("/rebuild-kb")
def rebuild_knowledge_base():
    chunks_count = build_kb_index()

    return {
        "status": "success",
        "chunks_indexed": chunks_count,
    }