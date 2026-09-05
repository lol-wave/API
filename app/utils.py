"""Utility functions for the application"""
import random
from sqlalchemy.orm import Session
from . import models


def generate_student_code(db: Session) -> str:
    """
    Generate a unique five-digit student code.
    """
    while True:
        student_code = str(random.randint(10000, 99999))
        
        existing = db.query(models.User).filter(
            models.User.student_code == student_code
        ).first()
        
        if not existing:
            return student_code
