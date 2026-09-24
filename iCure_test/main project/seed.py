from db.database import SessionLocal
from db.models import User

session = SessionLocal()

GUEST_EMAIL = "guest@icure.local"

guest = session.query(User).filter_by(email=GUEST_EMAIL).first()

if guest is None:
    guest = User(email=GUEST_EMAIL, pass_hash="-")
    session.add(guest)
    session.commit()
    print("Created guest user with id:", guest.id)
else:
    print("Guest user already exists with id:", guest.id)

session.close()