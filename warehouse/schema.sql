-- ============================================================
-- Data Warehouse Football — Ligue 1
-- ============================================================

CREATE TABLE IF NOT EXISTS competitions (
    id          INTEGER PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    code        VARCHAR(10)  NOT NULL UNIQUE,
    area        VARCHAR(100),
    type        VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS teams (
    id          INTEGER PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    short_name  VARCHAR(100),
    tla         VARCHAR(10),
    area        VARCHAR(100),
    founded     INTEGER,
    venue       VARCHAR(150)
);

CREATE TABLE IF NOT EXISTS standings (
    id              SERIAL PRIMARY KEY,
    competition_id  INTEGER REFERENCES competitions(id),
    season          VARCHAR(20),
    team_id         INTEGER REFERENCES teams(id),
    position        INTEGER,
    played          INTEGER,
    won             INTEGER,
    draw            INTEGER,
    lost            INTEGER,
    goals_for       INTEGER,
    goals_against   INTEGER,
    goal_diff       INTEGER,
    points          INTEGER,
    UNIQUE (competition_id, season, team_id)
);

CREATE TABLE IF NOT EXISTS matches (
    id              INTEGER PRIMARY KEY,
    competition_id  INTEGER REFERENCES competitions(id),
    season          VARCHAR(20),
    matchday        INTEGER,
    utc_date        TIMESTAMP,
    status          VARCHAR(30),
    home_team_id    INTEGER REFERENCES teams(id),
    away_team_id    INTEGER REFERENCES teams(id),
    home_score      INTEGER,
    away_score      INTEGER
);

CREATE TABLE IF NOT EXISTS scorers (
    id              SERIAL PRIMARY KEY,
    competition_id  INTEGER REFERENCES competitions(id),
    season          VARCHAR(20),
    player_name     VARCHAR(150),
    team_id         INTEGER REFERENCES teams(id),
    goals           INTEGER,
    assists         INTEGER,
    penalties       INTEGER,
    UNIQUE (competition_id, season, player_name)
);

-- Données enrichies issues du scraping
CREATE TABLE IF NOT EXISTS team_stats_scraped (
    id              SERIAL PRIMARY KEY,
    team_id         INTEGER REFERENCES teams(id),
    season          VARCHAR(20),
    xg              NUMERIC(6,2),
    xg_against      NUMERIC(6,2),
    possession_pct  NUMERIC(5,2),
    passes_completed INTEGER,
    source_url      TEXT,
    UNIQUE (team_id, season)
);
