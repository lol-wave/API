"""Utility functions for the application"""
import random
import string
from sqlalchemy.orm import Session
from . import models


def generate_student_code(db: Session, prefix: str = "STU") -> str:
    """
    Generate a unique student code.
    
    Args:
        db: Database session for checking uniqueness
        prefix: Prefix for the student code (default: "STU")
    
    Returns:
        A unique student code string (e.g., "STU12345678")
    """
    while True:
        # Generate random 8-digit number
        random_part = ''.join(random.choices(string.digits, k=8))
        student_code = f"{prefix}{random_part}"
        
        # Check if this code already exists in the database
        existing = db.query(models.User).filter(
            models.User.student_code == student_code
        ).first()
        
        if not existing:
            return student_code
