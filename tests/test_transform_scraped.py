import pytest
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from transformation.transform_scraped import convertir_valeur, transformer_valeurs_marche


# --- Tests convertir_valeur ---

class TestConvertirValeur:
    def test_milliards(self):
        assert convertir_valeur("€1.21bn") == pytest.approx(1210.0)

    def test_millions(self):
        assert convertir_valeur("€391.55m") == 391.55

    def test_petite_valeur_millions(self):
        assert convertir_valeur("€45.00m") == 45.0

    def test_valeur_vide(self):
        assert convertir_valeur("") is None

    def test_valeur_none(self):
        assert convertir_valeur(None) is None

    def test_valeur_nan(self):
        assert convertir_valeur(float("nan")) is None

    def test_valeur_sans_unite(self):
        assert convertir_valeur("€500") is None

    def test_valeur_inconnue(self):
        assert convertir_valeur("inconnu") is None


# --- Tests transformer_valeurs_marche ---

class TestTransformerValeursMarchees:
    def _make_df(self):
        return pd.DataFrame([
            {
                "team_name": "Paris Saint-Germain",
                "squad_size": "33",
                "avg_age": "26.5",
                "foreigners": "19",
                "market_value": "€1.21bn",
            },
            {
                "team_name": "AS Monaco",
                "squad_size": "28",
                "avg_age": "24.1",
                "foreigners": "15",
                "market_value": "€391.55m",
            },
        ])

    def test_retourne_dataframe(self):
        df = transformer_valeurs_marche(self._make_df())
        assert isinstance(df, pd.DataFrame)

    def test_colonne_market_value_m_creee(self):
        df = transformer_valeurs_marche(self._make_df())
        assert "market_value_m" in df.columns

    def test_colonne_market_value_supprimee(self):
        df = transformer_valeurs_marche(self._make_df())
        assert "market_value" not in df.columns

    def test_conversion_milliards(self):
        df = transformer_valeurs_marche(self._make_df())
        assert df.iloc[0]["market_value_m"] == pytest.approx(1210.0)

    def test_conversion_millions(self):
        df = transformer_valeurs_marche(self._make_df())
        assert df.iloc[1]["market_value_m"] == 391.55

    def test_squad_size_numerique(self):
        df = transformer_valeurs_marche(self._make_df())
        assert pd.api.types.is_numeric_dtype(df["squad_size"])

    def test_avg_age_numerique(self):
        df = transformer_valeurs_marche(self._make_df())
        assert pd.api.types.is_numeric_dtype(df["avg_age"])

    def test_ne_modifie_pas_df_original(self):
        df_original = self._make_df()
        transformer_valeurs_marche(df_original)
        assert "market_value" in df_original.columns
