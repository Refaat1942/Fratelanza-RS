import argparse

from sqlalchemy import select

from app.core.rbac import SystemRole
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import User, UserStatus


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a FRATELANZA Super Admin user.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--name", default="Platform Owner")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.email == args.email))
        if existing:
            print(f"User already exists: {args.email}")
            return

        user = User(
            company_id=None,
            full_name=args.name,
            email=args.email,
            password_hash=hash_password(args.password),
            role=SystemRole.SUPER_ADMIN,
            status=UserStatus.ACTIVE,
            locale="ar",
        )
        db.add(user)
        db.commit()
        print(f"Created Super Admin: {args.email}")


if __name__ == "__main__":
    main()
