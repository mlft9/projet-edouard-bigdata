NOM_TRANSFERMARKT_VERS_API = {
    "Paris Saint-Germain":  "Paris Saint-Germain FC",
    "AS Monaco":            "AS Monaco FC",
    "Olympique Marseille":  "Olympique de Marseille",
    "RC Strasbourg Alsace": "RC Strasbourg Alsace",
    "Olympique Lyon":       "Olympique Lyonnais",
    "LOSC Lille":           "Lille OSC",
    "Stade Rennais FC":     "Stade Rennais FC 1901",
    "RC Lens":              "Racing Club de Lens",
    "OGC Nice":             "OGC Nice",
    "FC Toulouse":          "Toulouse FC",
    "Paris FC":             "Paris FC",
    "FC Nantes":            "FC Nantes",
    "FC Lorient":           "FC Lorient",
    "Stade Brestois 29":    "Stade Brestois 29",
    "AJ Auxerre":           "AJ Auxerre",
    "Le Havre AC":          "Le Havre AC",
    "Angers SCO":           "Angers SCO",
    "FC Metz":              "FC Metz",
}


def fusionner(df_standings, df_market):
    df_market = df_market.copy()
    df_market["team_name_api"] = df_market["team_name"].map(NOM_TRANSFERMARKT_VERS_API)

    non_mappes = df_market[df_market["team_name_api"].isna()]["team_name"].tolist()
    if non_mappes:
        print(f"Attention : équipes sans correspondance : {non_mappes}")

    merged = df_standings.merge(
        df_market[["team_name_api", "squad_size", "avg_age", "foreigners", "market_value_m"]],
        left_on="team_name",
        right_on="team_name_api",
        how="left"
    ).drop(columns=["team_name_api"])

    return merged
