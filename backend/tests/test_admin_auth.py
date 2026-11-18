import unittest

from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.db.connection import Base
from src.db.models.user_model import User
from src.dtos.auth_dto import LoginDTO
from src.middlewares.auth_middleware import get_current_admin, get_current_user
from src.services.auth_service import AuthService
from src.utils.errors import ForbiddenError, UnauthorizedError
from src.utils.hash import hash_password
from src.utils.jwt import create_access_token


class AdminAuthTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.admin = User(
            email="admin@example.com",
            password_hash=hash_password("admin-password"),
            age=30,
            is_admin=True,
        )
        self.db.add(self.admin)
        self.db.commit()
        self.db.refresh(self.admin)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_admin_login_token_authorizes_admin_dependency(self):
        login = AuthService(self.db).login_admin(
            LoginDTO(email="admin@example.com", password="admin-password")
        )

        current_admin = get_current_admin(
            current_user=get_current_user(
                credentials=HTTPAuthorizationCredentials(
                    scheme="Bearer",
                    credentials=login.token,
                ),
                db=self.db,
            )
        )

        self.assertEqual(current_admin.id, self.admin.id)
        self.assertEqual(login.user.email, self.admin.email)

    def test_investor_token_cannot_authorize_admin_dependency(self):
        investor_token = create_access_token(
            {"sub": str(self.admin.id), "role": "inversor"}
        )

        with self.assertRaises(ForbiddenError):
            get_current_user(
                credentials=HTTPAuthorizationCredentials(
                    scheme="Bearer",
                    credentials=investor_token,
                ),
                db=self.db,
            )

    def test_missing_bearer_token_is_unauthorized(self):
        with self.assertRaises(UnauthorizedError):
            get_current_user(credentials=None, db=self.db)

    def test_non_admin_cannot_login_through_admin_endpoint(self):
        self.admin.is_admin = False
        self.db.commit()

        with self.assertRaises(UnauthorizedError):
            AuthService(self.db).login_admin(
                LoginDTO(email="admin@example.com", password="admin-password")
            )


if __name__ == "__main__":
    unittest.main()
