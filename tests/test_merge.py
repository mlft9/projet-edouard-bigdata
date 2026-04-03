import pytest
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from transformation.merge import fusionner, NOM_TRANSFERMARKT_VERS_API


# --- Tests du dictionnaire de mapping ---

class TestMapping:
    def test_psg_mappe_correctement(self):
        assert NOM_TRANSFERMARKT_VERS_API["Paris Saint-Germain"] == "Paris Saint-Germain FC"

    def test_lyon_mappe_correctement(self):
        assert NOM_TRANSFERMARKT_VERS_API["Olympique Lyon"] == "Olympique Lyonnais"

    def test_marseille_mappe_correctement(self):
        assert NOM_TRANSFERMARKT_VERS_API["Olympique Marseille"] == "Olympique de Marseille"

    def test_18_equipes_dans_le_mapping(self):
        assert len(NOM_TRANSFERMARKT_VERS_API) == 18


# --- Données de test pour fusionner ---

def make_df_standings():
    return pd.DataFrame([
        {"team_name": "Paris Saint-Germain FC", "position": 1, "points": 70},
        {"team_name": "AS Monaco FC",           "position": 2, "points": 60},
    ])

def make_df_market():
    return pd.DataFrame([
        {
            "team_name": "Paris Saint-Germain",
            "squad_size": 33,
            "avg_age": 26.5,
            "foreigners": 19,
            "market_value_m": 1210.0,
        },
        {
            "team_name": "AS Monaco",
            "squad_size": 28,
            "avg_age": 24.1,
            "foreigners": 15,
            "market_value_m": 391.55,
        },
    ])


# --- Tests fusionner ---

class TestFusionner:
    def test_retourne_dataframe(self):
        df = fusionner(make_df_standings(), make_df_market())
        assert isinstance(df, pd.DataFrame)

    def test_colonnes_standings_presentes(self):
        df = fusionner(make_df_standings(), make_df_market())
        assert "team_name" in df.columns
        assert "position" in df.columns
        assert "points" in df.columns

    def test_colonnes_market_presentes(self):
        df = fusionner(make_df_standings(), make_df_market())
        assert "market_value_m" in df.columns
        assert "squad_size" in df.columns

    def test_team_name_api_absente_apres_merge(self):
        df = fusionner(make_df_standings(), make_df_market())
        assert "team_name_api" not in df.columns

    def test_nombre_lignes_conserve(self):
        df = fusionner(make_df_standings(), make_df_market())
        assert len(df) == 2

    def test_valeurs_market_correctes(self):
        df = fusionner(make_df_standings(), make_df_market())
        psg = df[df["team_name"] == "Paris Saint-Germain FC"].iloc[0]
        assert psg["market_value_m"] == pytest.approx(1210.0)
        assert psg["squad_size"] == 33

    def test_equipe_sans_correspondance_nan(self):
        df_standings = pd.DataFrame([
            {"team_name": "Equipe Inconnue FC", "position": 1, "points": 50}
        ])
        df = fusionner(df_standings, make_df_market())
        assert pd.isna(df.iloc[0]["market_value_m"])

    def test_ne_modifie_pas_df_market_original(self):
        df_market = make_df_market()
        fusionner(make_df_standings(), df_market)
        assert "team_name_api" not in df_market.columns
