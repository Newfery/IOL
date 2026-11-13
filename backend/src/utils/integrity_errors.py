import sqlite3

from sqlalchemy.exc import IntegrityError


def is_unique_violation(exc: IntegrityError) -> bool:
    original = exc.orig
    sqlstate = getattr(original, "pgcode", None) or getattr(
        original, "sqlstate", None
    )
    if sqlstate == "23505":
        return True

    sqlite_errorcode = getattr(original, "sqlite_errorcode", None)
    unique_codes = {
        getattr(sqlite3, "SQLITE_CONSTRAINT_UNIQUE", -1),
        getattr(sqlite3, "SQLITE_CONSTRAINT_PRIMARYKEY", -1),
    }
    if sqlite_errorcode in unique_codes:
        return True

    message = str(original).lower()
    return "unique constraint failed" in message or "unique violation" in message
