"""Data-access layer for users."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import User

SORTABLE = {"id": User.id, "name": User.name, "age": User.age, "birth_state": User.birth_state}


def list_users(
    db: Session,
    *,
    birth_state: str | None,
    name: str | None,
    min_age: int | None,
    max_age: int | None,
    sort_by: str,
    order: str,
    limit: int,
    offset: int,
) -> tuple[list[User], int]:
    stmt = select(User)
    if birth_state:
        stmt = stmt.where(User.birth_state == birth_state)
    if name:
        stmt = stmt.where(func.lower(User.name).contains(name.lower(), autoescape=True))
    if min_age is not None:
        stmt = stmt.where(User.age >= min_age)
    if max_age is not None:
        stmt = stmt.where(User.age <= max_age)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    col = SORTABLE[sort_by]
    stmt = stmt.order_by(col.desc() if order == "desc" else col.asc(), User.id.asc())
    return list(db.scalars(stmt.limit(limit).offset(offset))), total


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def create_user(db: Session, *, name: str, age: int, birth_state: str) -> User:
    user = User(name=name, age=age, birth_state=birth_state)
    db.add(user)
    db.commit()
    return user


def update_user(db: Session, user: User, *, name: str, age: int, birth_state: str) -> User:
    user.name, user.age, user.birth_state = name, age, birth_state
    db.commit()
    return user


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()
