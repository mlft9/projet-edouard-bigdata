import pytest
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from transformation.transform_api import (
    transformer_classement,
    transformer_matchs,
    transformer_equipes,
    transformer_buteurs,
)

# --- Données de test ---

CLASSEMENT_DATA = {
    "competition": {"id": 2015},
    "filters": {"season": "2024"},
    "standings": [
        {
            "table": [
                {
                    "team": {"id": 524, "name": "Paris Saint-Germain FC"},
                    "position": 1,
                    "playedGames": 30,
                    "won": 22,
                    "draw": 4,
                    "lost": 4,
                    "goalsFor": 70,
                    "goalsAgainst": 30,
                    "goalDifference": 40,
                    "points": 70,
                }
            ]
        }
    ],
}

MATCHS_DATA = {
    "competition": {"id": 2015},
    "filters": {"season": "2024"},
    "matches": [
        {
            "id": 1001,
            "matchday": 1,
            "utcDate": "2024-08-18T19:00:00Z",
            "status": "FINISHED",
            "homeTeam": {"id": 524},
            "awayTeam": {"id": 548},
            "score": {"fullTime": {"home": 3, "away": 1}},
        }
    ],
}

EQUIPES_DATA = {
    "teams": [
        {
            "id": 524,
            "name": "Paris Saint-Germain FC",
            "shortName": "PSG",
            "tla": "PSG",
            "area": {"name": "France"},
            "founded": 1970,
            "venue": "Parc des Princes",
        }
    ]
}

BUTEURS_DATA = {
    "competition": {"id": 2015},
    "filters": {"season": "2024"},
    "scorers": [
        {
            "player": {"name": "Kylian Mbappé"},
            "team": {"id": 524},
            "goals": 27,
            "assists": 7,
            "penalties": 3,
        }
    ],
}


# --- Tests transformer_classement ---

class TestTransformerClassement:
    def test_retourne_dataframe(self):
        df = transformer_classement(CLASSEMENT_DATA)
        assert isinstance(df, pd.DataFrame)

    def test_colonnes_presentes(self):
        df = transformer_classement(CLASSEMENT_DATA)
        colonnes_attendues = [
            "competition_id", "season", "team_id", "team_name",
            "position", "played", "won", "draw", "lost",
            "goals_for", "goals_against", "goal_diff", "points",
        ]
        for col in colonnes_attendues:
            assert col in df.columns

    def test_valeurs_correctes(self):
        df = transformer_classement(CLASSEMENT_DATA)
        assert df.iloc[0]["team_id"] == 524
        assert df.iloc[0]["team_name"] == "Paris Saint-Germain FC"
        assert df.iloc[0]["position"] == 1
        assert df.iloc[0]["points"] == 70

    def test_une_ligne(self):
        df = transformer_classement(CLASSEMENT_DATA)
        assert len(df) == 1

    def test_donnees_invalides_retourne_dataframe_vide(self):
        df = transformer_classement({})
        assert isinstance(df, pd.DataFrame)
        assert df.empty


# --- Tests transformer_matchs ---

class TestTransformerMatchs:
    def test_retourne_dataframe(self):
        df = transformer_matchs(MATCHS_DATA)
        assert isinstance(df, pd.DataFrame)

    def test_colonnes_presentes(self):
        df = transformer_matchs(MATCHS_DATA)
        colonnes_attendues = [
            "id", "competition_id", "season", "matchday",
            "utc_date", "status", "home_team_id", "away_team_id",
            "home_score", "away_score",
        ]
        for col in colonnes_attendues:
            assert col in df.columns

    def test_date_convertie_en_datetime(self):
        df = transformer_matchs(MATCHS_DATA)
        assert pd.api.types.is_datetime64_any_dtype(df["utc_date"])

    def test_scores_corrects(self):
        df = transformer_matchs(MATCHS_DATA)
        assert df.iloc[0]["home_score"] == 3
        assert df.iloc[0]["away_score"] == 1

    def test_donnees_invalides_retourne_dataframe_vide(self):
        df = transformer_matchs({})
        assert isinstance(df, pd.DataFrame)
        assert df.empty


# --- Tests transformer_equipes ---

class TestTransformerEquipes:
    def test_retourne_dataframe(self):
        df = transformer_equipes(EQUIPES_DATA)
        assert isinstance(df, pd.DataFrame)

    def test_colonnes_presentes(self):
        df = transformer_equipes(EQUIPES_DATA)
        colonnes_attendues = ["id", "name", "short_name", "tla", "area", "founded", "venue"]
        for col in colonnes_attendues:
            assert col in df.columns

    def test_valeurs_correctes(self):
        df = transformer_equipes(EQUIPES_DATA)
        assert df.iloc[0]["id"] == 524
        assert df.iloc[0]["name"] == "Paris Saint-Germain FC"
        assert df.iloc[0]["tla"] == "PSG"
        assert df.iloc[0]["founded"] == 1970

    def test_champs_optionnels_absents(self):
        data = {"teams": [{"id": 1, "name": "Test FC", "shortName": "TFC", "tla": "TFC", "area": {"name": "France"}}]}
        df = transformer_equipes(data)
        assert df.iloc[0]["founded"] is None
        assert df.iloc[0]["venue"] is None

    def test_donnees_invalides_retourne_dataframe_vide(self):
        df = transformer_equipes({})
        assert isinstance(df, pd.DataFrame)
        assert df.empty


# --- Tests transformer_buteurs ---

class TestTransformerButeurs:
    def test_retourne_dataframe(self):
        df = transformer_buteurs(BUTEURS_DATA)
        assert isinstance(df, pd.DataFrame)

    def test_colonnes_presentes(self):
        df = transformer_buteurs(BUTEURS_DATA)
        colonnes_attendues = [
            "competition_id", "season", "player_name", "team_id",
            "goals", "assists", "penalties",
        ]
        for col in colonnes_attendues:
            assert col in df.columns

    def test_valeurs_correctes(self):
        df = transformer_buteurs(BUTEURS_DATA)
        assert df.iloc[0]["player_name"] == "Kylian Mbappé"
        assert df.iloc[0]["goals"] == 27
        assert df.iloc[0]["assists"] == 7

    def test_donnees_invalides_retourne_dataframe_vide(self):
        df = transformer_buteurs({})
        assert isinstance(df, pd.DataFrame)
        assert df.empty
