import pandas as pd


def convertir_valeur(val):
    """Convertit '€1.21bn' → 1210.0 et '€391.55m' → 391.55 (en millions)."""
    try:
        if pd.isna(val) or val == "":
            return None
        val = str(val).replace("€", "").strip()
        if "bn" in val:
            return float(val.replace("bn", "")) * 1000
        if "m" in val:
            return float(val.replace("m", ""))
        return None
    except Exception as e:
        print(f"Erreur conversion valeur '{val}' : {e}")
        return None


def transformer_valeurs_marche(df):
    try:
        df = df.copy()
        df["market_value_m"] = df["market_value"].apply(convertir_valeur)
        df["squad_size"] = pd.to_numeric(df["squad_size"], errors="coerce")
        df["avg_age"] = pd.to_numeric(df["avg_age"], errors="coerce")
        df["foreigners"] = pd.to_numeric(df["foreigners"], errors="coerce")
        df.drop(columns=["market_value"], inplace=True)
        return df
    except Exception as e:
        print(f"Erreur transformation valeurs marchandes : {e}")
        return pd.DataFrame()
