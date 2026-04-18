#!/usr/bin/env python3
"""Create a test user for Munich Rental Assistant.

Run from backend/ directory:
    python3 ../scripts/create_test_user.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.db import SessionLocal, engine, Base
from app.models import User, SearchProfile
from app.services.auth import hash_password


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        existing = db.scalars(
            select(User).where(User.email == "test@munich-rental.de")
        ).first()

        if existing:
            print("✅ Test user already exists: test@munich-rental.de")
            return

        user = User(
            email="test@munich-rental.de",
            hashed_password=hash_password("test1234"),
            full_name="Max Mustermann",
        )
        db.add(user)
        db.flush()

        profile = SearchProfile(
            user_id=user.id,
            name="WG bis 800€ in München",
            city="München",
            price_max=800,
            size_min_sqm=18,
            wg_type="wg",
            preferred_districts='["Maxvorstadt","Schwabing","Haidhausen"]',
        )
        db.add(profile)
        db.commit()

        print("✅ Test user created:")
        print("   Email:    test@munich-rental.de")
        print("   Password: test1234")

    finally:
        db.close()


if __name__ == "__main__":
    main()
