"""Database seed script for LeaveDesk."""
import logging
from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models.user import User
from app.domain.enums import RoleEnum

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("seed")


def seed_database():
    """Seed initial sample users: Priya Manager, Arjun Employee, and Meera Employee."""
    logger.info("Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Seed Priya Manager
        priya_email = "priya.manager@leavedesk.test"
        priya = db.query(User).filter(User.email == priya_email).first()
        if not priya:
            logger.info("Creating manager Priya Manager...")
            priya = User(
                name="Priya Manager",
                email=priya_email,
                role=RoleEnum.MANAGER.value,
                hashed_password=get_password_hash("Manager@123"),
                reports_to_id=None
            )
            db.add(priya)
            db.commit()
            db.refresh(priya)
            logger.info(f"Priya Manager created with ID: {priya.id}")
        else:
            logger.info(f"Priya Manager already exists with ID: {priya.id}")

        # 2. Seed Arjun Employee
        arjun_email = "arjun@leavedesk.test"
        arjun = db.query(User).filter(User.email == arjun_email).first()
        if not arjun:
            logger.info("Creating employee Arjun Employee...")
            arjun = User(
                name="Arjun Employee",
                email=arjun_email,
                role=RoleEnum.EMPLOYEE.value,
                hashed_password=get_password_hash("Employee@123"),
                reports_to_id=priya.id
            )
            db.add(arjun)
            db.commit()
            logger.info("Arjun Employee created (reports to Priya Manager).")
        else:
            arjun.reports_to_id = priya.id
            db.commit()
            logger.info("Arjun Employee already exists.")

        # 3. Seed Meera Employee
        meera_email = "meera@leavedesk.test"
        meera = db.query(User).filter(User.email == meera_email).first()
        if not meera:
            logger.info("Creating employee Meera Employee...")
            meera = User(
                name="Meera Employee",
                email=meera_email,
                role=RoleEnum.EMPLOYEE.value,
                hashed_password=get_password_hash("Employee@123"),
                reports_to_id=priya.id
            )
            db.add(meera)
            db.commit()
            logger.info("Meera Employee created (reports to Priya Manager).")
        else:
            meera.reports_to_id = priya.id
            db.commit()
            logger.info("Meera Employee already exists.")

        logger.info("Database seeding completed successfully!")
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
