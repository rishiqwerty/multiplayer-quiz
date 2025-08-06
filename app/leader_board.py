from app.models import Player, PlayerScore, SessionLocal
from sqlalchemy import func, desc


async def get_global_leaderboard(user_id: str = "", country: str = ""):
    db = SessionLocal()
    if user_id:
        country = db.query(Player.country).filter_by(id=user_id).first()
        if country:
            country = country.country.lower()
    query = (
        db.query(
            Player.user_name,
            Player.country,
            func.sum(PlayerScore.score).label("total_score"),
        )
        .join(PlayerScore, Player.id == PlayerScore.player_id)
        .filter(Player.country == country.lower() if country else True)
        .group_by(Player.id)
        .order_by(desc("total_score"))
        .limit(10)
    )
    leaderboard = [
        {"user_name": row.user_name, "score": row.total_score, "country": row.country}
        for row in query
    ]
    db.close()
    return leaderboard
