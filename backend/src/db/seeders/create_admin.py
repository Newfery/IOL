from getpass import getpass

from pydantic import EmailStr, TypeAdapter
from sqlalchemy.exc import IntegrityError

from src.db.connection import SessionLocal
from src.db.models.user_model import User
from src.utils.hash import hash_password


def main() -> None:
    email = TypeAdapter(EmailStr).validate_python(
        input("Email del administrador: ").strip()
    )
    password = getpass("Contraseña (8 a 72 bytes): ")
    if not 8 <= len(password.encode("utf-8")) <= 72:
        raise SystemExit("La contraseña debe tener entre 8 y 72 bytes.")

    with SessionLocal() as db:
        if db.query(User).filter(User.email == str(email)).first() is not None:
            raise SystemExit("Ya existe una cuenta con ese email.")

        db.add(
            User(
                email=str(email),
                password_hash=hash_password(password),
                age=18,
                is_admin=True,
            )
        )
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise SystemExit("No se pudo crear la cuenta administrativa.") from exc

    print("Cuenta administrativa creada.")


if __name__ == "__main__":
    main()
