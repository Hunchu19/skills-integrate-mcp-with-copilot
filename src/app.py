"""
High School Management System API

A simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
This version persists activities and domain collections in MongoDB.
"""

from datetime import datetime
from pathlib import Path
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import EmailStr
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

app = FastAPI(
    title="Mergington High School API",
    description="API for viewing and signing up for extracurricular activities",
)

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=current_dir / "static"), name="static")

# MongoDB persistence configuration
mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(mongo_uri)
db = client["mergington_high"]
activities_collection = db["activities"]
students_collection = db["students"]
staff_collection = db["staff"]
class_details_collection = db["class_details"]
payment_collection = db["payments"]
registration_details_collection = db["registration_details"]


def seed_database() -> None:
    activities_collection.create_index("name", unique=True)

    if activities_collection.count_documents({}) == 0:
        sample_activities = [
            {
                "name": "Chess Club",
                "description": "Learn strategies and compete in chess tournaments",
                "schedule": "Fridays, 3:30 PM - 5:00 PM",
                "max_participants": 12,
                "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
            },
            {
                "name": "Programming Class",
                "description": "Learn programming fundamentals and build software projects",
                "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
                "max_participants": 20,
                "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
            },
            {
                "name": "Gym Class",
                "description": "Physical education and sports activities",
                "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
                "max_participants": 30,
                "participants": ["john@mergington.edu", "olivia@mergington.edu"],
            },
            {
                "name": "Soccer Team",
                "description": "Join the school soccer team and compete in matches",
                "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
                "max_participants": 22,
                "participants": ["liam@mergington.edu", "noah@mergington.edu"],
            },
            {
                "name": "Basketball Team",
                "description": "Practice and play basketball with the school team",
                "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
                "max_participants": 15,
                "participants": ["ava@mergington.edu", "mia@mergington.edu"],
            },
            {
                "name": "Art Club",
                "description": "Explore your creativity through painting and drawing",
                "schedule": "Thursdays, 3:30 PM - 5:00 PM",
                "max_participants": 15,
                "participants": ["amelia@mergington.edu", "harper@mergington.edu"],
            },
            {
                "name": "Drama Club",
                "description": "Act, direct, and produce plays and performances",
                "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
                "max_participants": 20,
                "participants": ["ella@mergington.edu", "scarlett@mergington.edu"],
            },
            {
                "name": "Math Club",
                "description": "Solve challenging problems and participate in math competitions",
                "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
                "max_participants": 10,
                "participants": ["james@mergington.edu", "benjamin@mergington.edu"],
            },
            {
                "name": "Debate Team",
                "description": "Develop public speaking and argumentation skills",
                "schedule": "Fridays, 4:00 PM - 5:30 PM",
                "max_participants": 12,
                "participants": ["charlotte@mergington.edu", "henry@mergington.edu"],
            },
        ]

        try:
            activities_collection.insert_many(sample_activities)
        except DuplicateKeyError:
            pass

    if students_collection.count_documents({}) == 0:
        students_collection.insert_many([
            {
                "email": "michael@mergington.edu",
                "first_name": "Michael",
                "last_name": "Jordan",
                "enrolled_activities": ["Chess Club"],
            },
            {
                "email": "emma@mergington.edu",
                "first_name": "Emma",
                "last_name": "Wong",
                "enrolled_activities": ["Programming Class"],
            },
        ])

    if staff_collection.count_documents({}) == 0:
        staff_collection.insert_many([
            {
                "email": "coach.smith@mergington.edu",
                "name": "Coach Smith",
                "role": "Athletics Coordinator",
            },
            {
                "email": "ms.martin@mergington.edu",
                "name": "Ms. Martin",
                "role": "Computer Science Teacher",
            },
        ])

    if class_details_collection.count_documents({}) == 0:
        class_details_collection.insert_many([
            {
                "class_name": "Programming Fundamentals",
                "description": "Introductory programming curriculum for new students.",
                "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            },
            {
                "class_name": "Physical Fitness",
                "description": "Sports, conditioning, and teamwork exercises.",
                "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            },
        ])

    if payment_collection.count_documents({}) == 0:
        payment_collection.insert_many([
            {
                "student_email": "emma@mergington.edu",
                "amount": 50,
                "currency": "USD",
                "date": datetime.utcnow(),
                "status": "paid",
            },
        ])

    if registration_details_collection.count_documents({}) == 0:
        registration_details_collection.insert_many([
            {
                "student_email": "michael@mergington.edu",
                "activity_name": "Chess Club",
                "registered_on": datetime.utcnow(),
            },
        ])


seed_database()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    activities = list(activities_collection.find({}, {"_id": 0}))
    return {activity["name"]: activity for activity in activities}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: EmailStr = Query(...)):
    """Sign up a student for an activity"""
    activity = activities_collection.find_one({"name": activity_name})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student is already signed up")

    if len(activity["participants"]) >= activity["max_participants"]:
        raise HTTPException(status_code=400, detail="Activity is full")

    activities_collection.update_one(
        {"name": activity_name},
        {"$push": {"participants": str(email)}},
    )

    registration_details_collection.insert_one(
        {
            "student_email": str(email),
            "activity_name": activity_name,
            "registered_on": datetime.utcnow(),
        }
    )

    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: EmailStr = Query(...)):
    """Unregister a student from an activity"""
    activity = activities_collection.find_one({"name": activity_name})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    if email not in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    activities_collection.update_one(
        {"name": activity_name},
        {"$pull": {"participants": str(email)}},
    )

    registration_details_collection.delete_one(
        {"student_email": str(email), "activity_name": activity_name}
    )

    return {"message": f"Unregistered {email} from {activity_name}"}
