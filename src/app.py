"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from sqlmodel import Session, select, create_engine
from .models import Activity, Participant, SQLModel


app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


# Database (SQLite) setup
DB_FILE = os.path.join(current_dir, "data", "dev.db")
DB_DIR = os.path.dirname(DB_FILE)
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR, exist_ok=True)

sqlite_url = f"sqlite:///{DB_FILE}"
# SQLite needs check_same_thread False when used with SQLModel in FastAPI
engine = create_engine(sqlite_url, echo=False, connect_args={"check_same_thread": False})


def init_db_and_seed():
    SQLModel.metadata.create_all(engine)

    # Seed default activities if none exist
    with Session(engine) as session:
        count = session.exec(select(Activity)).first()
        if not count:
            seed_activities = {
                "Chess Club": {
                    "description": "Learn strategies and compete in chess tournaments",
                    "schedule": "Fridays, 3:30 PM - 5:00 PM",
                    "max_participants": 12,
                    "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
                },
                "Programming Class": {
                    "description": "Learn programming fundamentals and build software projects",
                    "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
                    "max_participants": 20,
                    "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
                },
                "Gym Class": {
                    "description": "Physical education and sports activities",
                    "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
                    "max_participants": 30,
                    "participants": ["john@mergington.edu", "olivia@mergington.edu"]
                },
                "Soccer Team": {
                    "description": "Join the school soccer team and compete in matches",
                    "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
                    "max_participants": 22,
                    "participants": ["liam@mergington.edu", "noah@mergington.edu"]
                },
                "Basketball Team": {
                    "description": "Practice and play basketball with the school team",
                    "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
                    "max_participants": 15,
                    "participants": ["ava@mergington.edu", "mia@mergington.edu"]
                },
                "Art Club": {
                    "description": "Explore your creativity through painting and drawing",
                    "schedule": "Thursdays, 3:30 PM - 5:00 PM",
                    "max_participants": 15,
                    "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
                },
                "Drama Club": {
                    "description": "Act, direct, and produce plays and performances",
                    "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
                    "max_participants": 20,
                    "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
                },
                "Math Club": {
                    "description": "Solve challenging problems and participate in math competitions",
                    "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
                    "max_participants": 10,
                    "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
                },
                "Debate Team": {
                    "description": "Develop public speaking and argumentation skills",
                    "schedule": "Fridays, 4:00 PM - 5:30 PM",
                    "max_participants": 12,
                    "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
                }
            }

            for name, info in seed_activities.items():
                activity = Activity(name=name,
                                    description=info["description"],
                                    schedule=info["schedule"],
                                    max_participants=info["max_participants"])
                session.add(activity)
                session.commit()
                # add participants
                for email in info["participants"]:
                    participant = Participant(email=email, activity_id=activity.id)
                    session.add(participant)
                session.commit()


init_db_and_seed()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    with Session(engine) as session:
        activities = session.exec(select(Activity)).all()
        result = {}
        for a in activities:
            # load participants
            participants = session.exec(select(Participant).where(Participant.activity_id == a.id)).all()
            result[a.name] = {
                "description": a.description,
                "schedule": a.schedule,
                "max_participants": a.max_participants,
                "participants": [p.email for p in participants]
            }
        return result


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity (persisted)
    """
    with Session(engine) as session:
        activity = session.exec(select(Activity).where(Activity.name == activity_name)).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        participants = session.exec(select(Participant).where(Participant.activity_id == activity.id)).all()
        if any(p.email == email for p in participants):
            raise HTTPException(status_code=400, detail="Student is already signed up")

        if len(participants) >= activity.max_participants:
            raise HTTPException(status_code=400, detail="Activity is full")

        new_p = Participant(email=email, activity_id=activity.id)
        session.add(new_p)
        session.commit()
        return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity (persisted)
    """
    with Session(engine) as session:
        activity = session.exec(select(Activity).where(Activity.name == activity_name)).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        participant = session.exec(select(Participant).where(Participant.activity_id == activity.id, Participant.email == email)).first()
        if not participant:
            raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

        session.delete(participant)
        session.commit()
        return {"message": f"Unregistered {email} from {activity_name}"}

