"""User CRUD endpoints."""
import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.orm import Session

from app import repository
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserOut, UserUpdate
from app.security import require_api_key
from app.states import normalize_state

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/users", tags=["users"])

DB = Annotated[Session, Depends(get_db)]
UserId = Annotated[int, Path(ge=1, le=2_147_483_647)]  # fits the INTEGER primary key


def _get_or_404(db: Session, user_id: UserId):
    user = repository.get_user(db, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"User {user_id} not found")
    return user


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_api_key)])
def create_user(payload: UserCreate, db: DB, response: Response) -> User:
    user = repository.create_user(db, **payload.model_dump())
    logger.info("user_created", extra={"user_id": user.id})
    response.headers["Location"] = f"/api/users/{user.id}"
    return user


@router.get("", response_model=list[UserOut])
def list_users(
    db: DB,
    response: Response,
    birth_state: Annotated[str | None, Query(description="Filter by state code or full name")] = None,
    name: Annotated[str | None, Query(max_length=100, description="Case-insensitive substring")] = None,
    min_age: Annotated[int | None, Query(ge=0, le=150)] = None,
    max_age: Annotated[int | None, Query(ge=0, le=150)] = None,
    sort_by: Literal["id", "name", "age", "birth_state"] = "id",
    order: Literal["asc", "desc"] = "asc",
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[User]:
    state = None
    if birth_state:
        try:
            state = normalize_state(birth_state)
        except ValueError as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    if min_age is not None and max_age is not None and min_age > max_age:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "min_age cannot exceed max_age")
    users, total = repository.list_users(
        db, birth_state=state, name=name, min_age=min_age, max_age=max_age,
        sort_by=sort_by, order=order, limit=limit, offset=offset,
    )
    response.headers["X-Total-Count"] = str(total)
    return users


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: UserId, db: DB) -> User:
    return _get_or_404(db, user_id)


@router.put("/{user_id}", response_model=UserOut, dependencies=[Depends(require_api_key)])
def update_user(user_id: UserId, payload: UserUpdate, db: DB) -> User:
    user = repository.update_user(db, _get_or_404(db, user_id), **payload.model_dump())
    logger.info("user_updated", extra={"user_id": user.id})
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_api_key)])
def delete_user(user_id: UserId, db: DB) -> Response:
    repository.delete_user(db, _get_or_404(db, user_id))
    logger.info("user_deleted", extra={"user_id": user_id})
    return Response(status_code=status.HTTP_204_NO_CONTENT)
