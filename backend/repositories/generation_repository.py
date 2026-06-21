from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models.generation import Generation


class GenerationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, generation: Generation) -> Generation:
        self.session.add(generation)
        self.session.flush()
        return generation

    def get_by_id(self, generation_id: str) -> Generation | None:
        return self.session.get(Generation, generation_id)

    def list(self, limit: int, offset: int) -> list[Generation]:
        statement = (
            select(Generation)
            .order_by(Generation.created_at.desc(), Generation.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(statement))

    def count(self) -> int:
        statement = select(func.count()).select_from(Generation)
        return int(self.session.scalar(statement) or 0)

    def delete(self, generation: Generation) -> None:
        self.session.delete(generation)
        self.session.flush()
