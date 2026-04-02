import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pg8000.dbapi
from config.config import DB_CONFIG
from transformation.merge import NOM_TRANSFERMARKT_VERS_API


def to_int(val):
    """Convertit un float pandas (ex: 5.0) en int, None si NaN."""
    if val is None or str(val) == "nan":
        return None
    return int(val)


def get_connexion():
    return pg8000.dbapi.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["dbname"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )


def charger_competition(data):
    comp = data["competition"]
    conn = get_connexion()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO competitions (id, name, code, area, type)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
    """, (comp["id"], comp["name"], comp["code"], data["area"]["name"], comp["type"]))
    conn.commit()
    cur.close()
    conn.close()
    print(f"Compétition chargée : {comp['name']}")


def charger_equipes(df):
    rows = df.to_dict("records")
    conn = get_connexion()
    cur = conn.cursor()
    for r in rows:
        cur.execute("""
            INSERT INTO teams (id, name, short_name, tla, area, founded, venue)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
        """, (r["id"], r["name"], r["short_name"], r["tla"], r["area"], r.get("founded"), r.get("venue")))
    conn.commit()
    cur.close()
    conn.close()
    print(f"{len(rows)} équipes chargées.")


def charger_classement(df):
    rows = df.to_dict("records")
    conn = get_connexion()
    cur = conn.cursor()
    for r in rows:
        cur.execute("""
            INSERT INTO standings
                (competition_id, season, team_id, position, played, won, draw, lost,
                 goals_for, goals_against, goal_diff, points)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (competition_id, season, team_id)
            DO UPDATE SET position = EXCLUDED.position, points = EXCLUDED.points,
                played = EXCLUDED.played, won = EXCLUDED.won, draw = EXCLUDED.draw,
                lost = EXCLUDED.lost, goals_for = EXCLUDED.goals_for,
                goals_against = EXCLUDED.goals_against, goal_diff = EXCLUDED.goal_diff
        """, (r["competition_id"], r["season"], r["team_id"], r["position"],
              r["played"], r["won"], r["draw"], r["lost"],
              r["goals_for"], r["goals_against"], r["goal_diff"], r["points"]))
    conn.commit()
    cur.close()
    conn.close()
    print(f"{len(rows)} lignes de classement chargées.")


def charger_matchs(df):
    rows = df.to_dict("records")
    conn = get_connexion()
    cur = conn.cursor()
    for r in rows:
        home = to_int(r.get("home_score"))
        away = to_int(r.get("away_score"))
        cur.execute("""
            INSERT INTO matches
                (id, competition_id, season, matchday, utc_date, status,
                 home_team_id, away_team_id, home_score, away_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET status = EXCLUDED.status,
                home_score = EXCLUDED.home_score, away_score = EXCLUDED.away_score
        """, (r["id"], r["competition_id"], r["season"], r["matchday"], r["utc_date"],
              r["status"], r["home_team_id"], r["away_team_id"], home, away))
    conn.commit()
    cur.close()
    conn.close()
    print(f"{len(rows)} matchs chargés.")


def charger_buteurs(df):
    rows = df.to_dict("records")
    conn = get_connexion()
    cur = conn.cursor()
    for r in rows:
        cur.execute("""
            INSERT INTO scorers (competition_id, season, player_name, team_id, goals, assists, penalties)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (competition_id, season, player_name)
            DO UPDATE SET goals = EXCLUDED.goals, assists = EXCLUDED.assists
        """, (r["competition_id"], r["season"], r["player_name"], r["team_id"],
              to_int(r["goals"]), to_int(r["assists"]), to_int(r["penalties"])))
    conn.commit()
    cur.close()
    conn.close()
    print(f"{len(rows)} buteurs chargés.")


def charger_valeurs_marche(df, df_teams):
    nom_vers_id = dict(zip(df_teams["name"], df_teams["id"]))
    rows = df.to_dict("records")
    conn = get_connexion()
    cur = conn.cursor()
    for r in rows:
        nom_api = NOM_TRANSFERMARKT_VERS_API.get(r["team_name"], r["team_name"])
        team_id = nom_vers_id.get(nom_api)
        if not team_id:
            continue
        cur.execute("""
            INSERT INTO team_stats_scraped
                (team_id, season, squad_size, avg_age, foreigners, market_value_m)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (team_id, season)
            DO UPDATE SET market_value_m = EXCLUDED.market_value_m,
                squad_size = EXCLUDED.squad_size, avg_age = EXCLUDED.avg_age
        """, (team_id, "2025", r.get("squad_size"), r.get("avg_age"),
              r.get("foreigners"), r.get("market_value_m")))
    conn.commit()
    cur.close()
    conn.close()
    print(f"{len(rows)} valeurs marchandes chargées.")
