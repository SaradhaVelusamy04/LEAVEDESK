from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.user import User


class UserRepository:
    """Repository handling database operations for User accounts."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Fetch user by primary key."""
        stmt = select(User).where(User.id == user_id)
        return self.db.scalars(stmt).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Fetch user by email (case-insensitive)."""
        stmt = select(User).where(User.email.ilike(email.strip()))
        return self.db.scalars(stmt).first()

    def get_direct_reports(self, manager_id: int) -> List[User]:
        """Fetch all employees reporting directly to the manager."""
        stmt = select(User).where(User.reports_to_id == manager_id)
        return list(self.db.scalars(stmt).all())

    def create(
        self,
        name: str,
        email: str,
        hashed_password: str,
        role: str,
        reports_to_id: Optional[int] = None
    ) -> User:
        """Create and persist a new user record."""
        user = User(
            name=name.strip(),
            email=email.strip().lower(),
            hashed_password=hashed_password,
            role=role,
            reports_to_id=reports_to_id
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
