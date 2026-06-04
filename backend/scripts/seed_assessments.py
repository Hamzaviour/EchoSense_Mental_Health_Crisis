"""Seed PHQ-9, GAD-7, and WHO-5 assessment questions."""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.extensions import db
from app.models import Assessment

LIKERT_4 = [
    {"value": 0, "label": "Not at all"},
    {"value": 1, "label": "Several days"},
    {"value": 2, "label": "More than half the days"},
    {"value": 3, "label": "Nearly every day"},
]

LIKERT_6 = [
    {"value": 0, "label": "At no time"},
    {"value": 1, "label": "Some of the time"},
    {"value": 2, "label": "Less than half"},
    {"value": 3, "label": "More than half"},
    {"value": 4, "label": "Most of the time"},
    {"value": 5, "label": "All of the time"},
]

PHQ9_QUESTIONS = [
    "Little interest or pleasure in doing things",
    "Feeling down, depressed, or hopeless",
    "Trouble falling or staying asleep, or sleeping too much",
    "Feeling tired or having little energy",
    "Poor appetite or overeating",
    "Feeling bad about yourself — or that you are a failure",
    "Trouble concentrating on things",
    "Moving or speaking slowly/being fidgety or restless",
    "Thoughts that you would be better off dead or of hurting yourself",
]

GAD7_QUESTIONS = [
    "Feeling nervous, anxious, or on edge",
    "Not being able to stop or control worrying",
    "Worrying too much about different things",
    "Trouble relaxing",
    "Being so restless that it is hard to sit still",
    "Becoming easily annoyed or irritable",
    "Feeling afraid, as if something awful might happen",
]

WHO5_QUESTIONS = [
    "I have felt cheerful and in good spirits",
    "I have felt calm and relaxed",
    "I have felt active and vigorous",
    "I woke up feeling fresh and rested",
    "My daily life has been filled with things that interest me",
]


def seed():
    app = create_app()
    with app.app_context():
        if Assessment.query.first():
            print("Assessments already seeded.")
            return
        for i, text in enumerate(PHQ9_QUESTIONS, 1):
            db.session.add(Assessment(assessment_type="PHQ9", question_number=i, question_text=text, options=LIKERT_4))
        for i, text in enumerate(GAD7_QUESTIONS, 1):
            db.session.add(Assessment(assessment_type="GAD7", question_number=i, question_text=text, options=LIKERT_4))
        for i, text in enumerate(WHO5_QUESTIONS, 1):
            db.session.add(Assessment(assessment_type="WHO5", question_number=i, question_text=text, options=LIKERT_6))
        db.session.commit()
        print("Seeded PHQ-9, GAD-7, WHO-5 questions.")


if __name__ == "__main__":
    seed()
