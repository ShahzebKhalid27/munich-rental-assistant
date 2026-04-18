#!/usr/bin/env python3
"""
Create a test user for Munich Rental Assistant.
Run from backend/ directory: python3 ../scripts/create_test_user.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import SessionLocal, engine, Base
from app.models import User, SearchProfile
from app.services.auth import hash_password

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if test user exists
        existing = db.scalars(
            __import__("sqlalchemy").select(User).where(User.email == "test@munich-rental.de")
        ).first()

        if existing:
            print("✅ Test user already exists: test@munich-rental.de")
            return

        # Create test user
        user = User(
            email="test@munich-rental.de",
            hashed_password=hash_password("test1234"),
            full_name="Max Mustermann",
        )
        db.add(user)
        db.flush()

        # Create a default search profile
        profile = SearchProfile(
            user_id=user.id,
            name="WG bis 800€ in München",
            city="München",
            price_max=800,
            price_min=0,
            size_min_sqm=18,
            size_max_sqm=50,
            wg_type="wg",
            preferred_districts='["Maxvorstadt","Schwabing","Haidhausen"]',
        )
        db.add(profile)
        db.commit()

        print("✅ Test user created:")
        print("   Email:    test@munich-rental.de")
        print("   Password: test1234")
        print("   (München, bis 800€, WG-Zimmer, Maxvorstadt/Schwabing/Haidhausen)")

    finally:
        db.close()


if __name__ == "__main__":
    main()
