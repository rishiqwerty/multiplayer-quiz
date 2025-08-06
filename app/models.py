from sqlalchemy import Column, Integer, String, JSON, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship


Base = declarative_base()


class GameResult(Base):
    __tablename__ = "game_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String, unique=True, index=True)
    team1 = Column(String)
    team2 = Column(String)
    team1_score = Column(Integer)
    team2_score = Column(Integer)
    winner = Column(String)
    final_scores = Column(JSON)
    players = relationship("PlayerScore", back_populates="game")


class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String, unique=True, index=True)
    country = Column(String, nullable=True)
    games = relationship("PlayerScore", back_populates="player")


class PlayerScore(Base):
    __tablename__ = "player_scores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey("game_results.id"))
    player_id = Column(String, ForeignKey("players.id"))
    score = Column(Integer)

    game = relationship("GameResult", back_populates="players")
    player = relationship("Player", back_populates="games")


DATABASE_URL = "sqlite:///./quiz.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
