import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db


class GameScore(db.Model):
    __tablename__ = 'game_scores'

    id: so.Mapped[int] = so.mapped_column(
        sa.Integer, primary_key=True, autoincrement=True
    )
    name: so.Mapped[str] = so.mapped_column(sa.String(64), unique=False)
    score: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)
    timestamp: so.Mapped[sa.DateTime] = so.mapped_column(
        sa.DateTime, server_default=sa.func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<GameScore(id={self.id}, name='{self.name}', score={self.score}, timestamp={self.timestamp})>"

    @classmethod
    def add_game_score(cls, name: str, score: int):
        """Adds a new game score to the database."""
        new_score = cls(name=name, score=score)
        db.session.add(new_score)
        db.session.commit()

    @classmethod
    def get_high_scores(cls, limit: int = 10):
        """Fetches the top scores from the database."""
        return db.session.query(cls).order_by(cls.score.desc()).limit(limit).all()

    @classmethod
    def get_highest_score(cls):
        """Fetches the highest score from the database."""
        return db.session.query(cls).order_by(cls.score.desc()).first()

    @classmethod
    def delete_score_by_id(cls, score_id: int):
        """Deletes a score by its ID."""
        score = db.session.get(cls, score_id)
        if score:
            db.session.delete(score)
            db.session.commit()
            return True
        return False

    @classmethod
    def delete_all_scores(cls):
        """Deletes all game scores from the database."""
        db.session.query(cls).delete()
        db.session.commit()