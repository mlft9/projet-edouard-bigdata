import pandas as pd


def transformer_classement(data):
    competition_id = data["competition"]["id"]
    season = data["filters"]["season"]
    table = data["standings"][0]["table"]

    rows = []
    for entry in table:
        rows.append({
            "competition_id": competition_id,
            "season": season,
            "team_id": entry["team"]["id"],
            "team_name": entry["team"]["name"],
            "position": entry["position"],
            "played": entry["playedGames"],
            "won": entry["won"],
            "draw": entry["draw"],
            "lost": entry["lost"],
            "goals_for": entry["goalsFor"],
            "goals_against": entry["goalsAgainst"],
            "goal_diff": entry["goalDifference"],
            "points": entry["points"],
        })

    return pd.DataFrame(rows)


def transformer_matchs(data):
    competition_id = data["competition"]["id"]
    season = data["filters"]["season"]

    rows = []
    for m in data["matches"]:
        rows.append({
            "id": m["id"],
            "competition_id": competition_id,
            "season": season,
            "matchday": m["matchday"],
            "utc_date": m["utcDate"],
            "status": m["status"],
            "home_team_id": m["homeTeam"]["id"],
            "away_team_id": m["awayTeam"]["id"],
            "home_score": m["score"]["fullTime"]["home"],
            "away_score": m["score"]["fullTime"]["away"],
        })

    df = pd.DataFrame(rows)
    df["utc_date"] = pd.to_datetime(df["utc_date"])
    return df


def transformer_equipes(data):
    rows = []
    for t in data["teams"]:
        rows.append({
            "id": t["id"],
            "name": t["name"],
            "short_name": t["shortName"],
            "tla": t["tla"],
            "area": t["area"]["name"],
            "founded": t.get("founded"),
            "venue": t.get("venue"),
        })

    return pd.DataFrame(rows)


def transformer_buteurs(data):
    competition_id = data["competition"]["id"]
    season = data["filters"]["season"]

    rows = []
    for s in data["scorers"]:
        rows.append({
            "competition_id": competition_id,
            "season": season,
            "player_name": s["player"]["name"],
            "team_id": s["team"]["id"],
            "goals": s.get("goals", 0),
            "assists": s.get("assists", 0),
            "penalties": s.get("penalties", 0),
        })

    return pd.DataFrame(rows)
