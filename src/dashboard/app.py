import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# ── Config page ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Ligue 1 — Dashboard",
    page_icon="⚽",
    layout="wide",
)

SAISON = "2025"

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5433)),
    "dbname":   os.getenv("DB_NAME", "football_dw"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}


@st.cache_data(ttl=300)
def query(sql):
    conn = psycopg2.connect(**DB_CONFIG)
    df = pd.read_sql(sql, conn)
    conn.close()
    return df


# ── Navigation ────────────────────────────────────────────────────────────────

st.sidebar.title("⚽ Ligue 1")
st.sidebar.caption(f"Saison {SAISON}")
page = st.sidebar.radio(
    "Navigation",
    ["🏆 Classement", "📅 Matchs", "🔍 Équipes", "👟 Buteurs"],
)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — CLASSEMENT
# ══════════════════════════════════════════════════════════════════════════════

if page == "🏆 Classement":
    st.title("🏆 Classement Ligue 1")

    df = query(f"""
        SELECT s.position, t.name AS equipe, t.tla,
               s.played, s.won, s.draw, s.lost,
               s.goals_for, s.goals_against, s.goal_diff, s.points,
               ts.market_value_m
        FROM standings s
        JOIN teams t ON s.team_id = t.id
        LEFT JOIN team_stats_scraped ts ON ts.team_id = t.id AND ts.season = s.season
        WHERE s.season = '{SAISON}'
        ORDER BY s.position
    """)

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    leader = df.iloc[0]
    meilleure_attaque = df.loc[df["goals_for"].idxmax()]
    meilleure_defense = df.loc[df["goals_against"].idxmin()]

    scorers_df = query(f"""
        SELECT player_name, goals FROM scorers
        WHERE season = '{SAISON}' ORDER BY goals DESC LIMIT 1
    """)
    top_buteur = scorers_df.iloc[0] if not scorers_df.empty else None

    col1.metric("🥇 Leader", leader["equipe"], f"{leader['points']} pts")
    col2.metric("⚡ Meilleure attaque", meilleure_attaque["equipe"], f"{meilleure_attaque['goals_for']} buts")
    col3.metric("🛡️ Meilleure défense", meilleure_defense["equipe"], f"{meilleure_defense['goals_against']} encaissés")
    if top_buteur is not None:
        col4.metric("👟 Top buteur", top_buteur["player_name"], f"{top_buteur['goals']} buts")

    st.divider()

    # Tableau de classement
    st.subheader("Tableau")
    df_affichage = df[["position", "equipe", "played", "won", "draw", "lost",
                        "goals_for", "goals_against", "goal_diff", "points"]].copy()
    df_affichage.columns = ["#", "Équipe", "J", "V", "N", "D", "BP", "BC", "Diff", "Pts"]

    def colorier_ligne(row):
        pos = row["#"]
        if pos <= 3:
            return ["background-color: #0d3a5c"] * len(row)   # Champions League
        elif pos == 4:
            return ["background-color: #1a4a1a"] * len(row)   # Barrage C1
        elif pos <= 6:
            return ["background-color: #3a2d00"] * len(row)   # Conference League
        elif pos >= 16:
            return ["background-color: #4a0a0a"] * len(row)   # Relégation
        return [""] * len(row)

    st.dataframe(
        df_affichage.style.apply(colorier_ligne, axis=1),
        use_container_width=True,
        hide_index=True,
    )

    st.caption("🔵 Champions League  🟢 Barrage C1  🟡 Conference League  🔴 Relégation")

    st.divider()

    # Graphique buts
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Buts marqués par équipe")
        fig = px.bar(
            df.sort_values("goals_for", ascending=True),
            x="goals_for", y="equipe",
            orientation="h",
            color="goals_for",
            color_continuous_scale="Blues",
            labels={"goals_for": "Buts marqués", "equipe": ""},
        )
        fig.update_layout(showlegend=False, coloraxis_showscale=False, height=500)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Points vs Valeur marchande")
        df_val = df.dropna(subset=["market_value_m"])
        if not df_val.empty:
            fig2 = px.scatter(
                df_val, x="market_value_m", y="points",
                text="tla",
                labels={"market_value_m": "Valeur marchande (M€)", "points": "Points"},
                color="points",
                color_continuous_scale="RdYlGn",
            )
            fig2.update_traces(textposition="top center", marker_size=10)
            fig2.update_layout(coloraxis_showscale=False, height=500)
            st.plotly_chart(fig2, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — MATCHS
# ══════════════════════════════════════════════════════════════════════════════

elif page == "📅 Matchs":
    st.title("📅 Résultats et Calendrier")

    df_matchs = query(f"""
        SELECT m.matchday, m.utc_date::date AS date, m.status,
               ht.name AS domicile, m.home_score,
               at.name AS exterieur, m.away_score
        FROM matches m
        JOIN teams ht ON m.home_team_id = ht.id
        JOIN teams at ON m.away_team_id = at.id
        WHERE m.season = '{SAISON}'
        ORDER BY m.matchday, m.utc_date
    """)

    journees = sorted(df_matchs["matchday"].unique())
    journee = st.select_slider("Journée", options=journees, value=journees[-1] if journees else 1)

    df_j = df_matchs[df_matchs["matchday"] == journee].copy()
    joues = df_j[df_j["status"] == "FINISHED"]
    a_venir = df_j[df_j["status"] != "FINISHED"]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"Résultats — J{journee}")
        if joues.empty:
            st.info("Pas encore de résultats pour cette journée.")
        for _, row in joues.iterrows():
            score = f"{int(row['home_score'])} — {int(row['away_score'])}"
            winner_home = row['home_score'] > row['away_score']
            winner_away = row['away_score'] > row['home_score']
            dom = f"**{row['domicile']}**" if winner_home else row['domicile']
            ext = f"**{row['exterieur']}**" if winner_away else row['exterieur']
            st.markdown(f"{dom} &nbsp; `{score}` &nbsp; {ext}")

    with col2:
        st.subheader(f"À venir — J{journee}")
        if a_venir.empty:
            st.info("Tous les matchs de cette journée sont joués.")
        for _, row in a_venir.iterrows():
            st.markdown(f"{row['domicile']} vs {row['exterieur']}  \n📅 {row['date']}")

    st.divider()
    st.subheader("Résultats de toutes les journées jouées")
    df_finis = df_matchs[df_matchs["status"] == "FINISHED"].copy()
    df_finis["Score"] = df_finis["home_score"].astype(int).astype(str) + " — " + df_finis["away_score"].astype(int).astype(str)
    st.dataframe(
        df_finis[["matchday", "date", "domicile", "Score", "exterieur"]].rename(columns={
            "matchday": "J", "date": "Date", "domicile": "Domicile", "exterieur": "Extérieur"
        }),
        use_container_width=True,
        hide_index=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — ÉQUIPES
# ══════════════════════════════════════════════════════════════════════════════

elif page == "🔍 Équipes":
    st.title("🔍 Comparaison d'Équipes")

    df_equipes = query(f"""
        SELECT s.position, t.id, t.name, t.tla, t.founded, t.venue,
               s.played, s.won, s.draw, s.lost,
               s.goals_for, s.goals_against, s.goal_diff, s.points,
               ts.market_value_m, ts.squad_size, ts.avg_age, ts.foreigners
        FROM standings s
        JOIN teams t ON s.team_id = t.id
        LEFT JOIN team_stats_scraped ts ON ts.team_id = t.id AND ts.season = s.season
        WHERE s.season = '{SAISON}'
        ORDER BY s.position
    """)

    noms = df_equipes["name"].tolist()
    col1, col2 = st.columns(2)
    equipe1 = col1.selectbox("Équipe 1", noms, index=0)
    equipe2 = col2.selectbox("Équipe 2", noms, index=1)

    e1 = df_equipes[df_equipes["name"] == equipe1].iloc[0]
    e2 = df_equipes[df_equipes["name"] == equipe2].iloc[0]

    st.divider()

    # Infos générales
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(equipe1)
        st.metric("Classement", f"#{int(e1['position'])}")
        st.metric("Points", int(e1["points"]))
        st.metric("Bilan", f"{int(e1['won'])}V / {int(e1['draw'])}N / {int(e1['lost'])}D")
        if e1["market_value_m"]:
            st.metric("Valeur marchande", f"{e1['market_value_m']:.0f} M€")
        if e1["founded"]:
            st.caption(f"Fondé en {int(e1['founded'])} · {e1['venue']}")

    with col2:
        st.subheader(equipe2)
        st.metric("Classement", f"#{int(e2['position'])}")
        st.metric("Points", int(e2["points"]))
        st.metric("Bilan", f"{int(e2['won'])}V / {int(e2['draw'])}N / {int(e2['lost'])}D")
        if e2["market_value_m"]:
            st.metric("Valeur marchande", f"{e2['market_value_m']:.0f} M€")
        if e2["founded"]:
            st.caption(f"Fondé en {int(e2['founded'])} · {e2['venue']}")

    st.divider()

    # Radar chart
    st.subheader("Radar de comparaison")

    categories = ["Points", "Buts marqués", "Défense", "Diff. buts", "Valeur marchande"]

    max_pts  = df_equipes["points"].max()
    max_gf   = df_equipes["goals_for"].max()
    max_gc   = df_equipes["goals_against"].max()
    max_gd   = df_equipes["goal_diff"].max()
    min_gd   = df_equipes["goal_diff"].min()
    max_val  = df_equipes["market_value_m"].max() if df_equipes["market_value_m"].notna().any() else 1

    def normaliser(equipe):
        defense = (max_gc - equipe["goals_against"]) / max_gc * 100 if max_gc > 0 else 0
        gd = (equipe["goal_diff"] - min_gd) / (max_gd - min_gd) * 100 if max_gd != min_gd else 50
        val = equipe["market_value_m"] / max_val * 100 if pd.notna(equipe["market_value_m"]) else 0
        return [
            equipe["points"] / max_pts * 100,
            equipe["goals_for"] / max_gf * 100,
            defense,
            gd,
            val,
        ]

    v1 = normaliser(e1)
    v2 = normaliser(e2)

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=v1 + [v1[0]], theta=categories + [categories[0]],
                                   fill="toself", name=equipe1, line_color="#4da6ff"))
    fig.add_trace(go.Scatterpolar(r=v2 + [v2[0]], theta=categories + [categories[0]],
                                   fill="toself", name=equipe2, line_color="#ff7043"))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Confrontations directes
    st.subheader("Confrontations directes cette saison")
    df_confr = query(f"""
        SELECT m.matchday, m.utc_date::date AS date,
               ht.name AS domicile, m.home_score,
               at.name AS exterieur, m.away_score, m.status
        FROM matches m
        JOIN teams ht ON m.home_team_id = ht.id
        JOIN teams at ON m.away_team_id = at.id
        WHERE m.season = '{SAISON}'
          AND m.status = 'FINISHED'
          AND (
              (ht.name = '{equipe1}' AND at.name = '{equipe2}')
              OR (ht.name = '{equipe2}' AND at.name = '{equipe1}')
          )
        ORDER BY m.utc_date
    """)
    if df_confr.empty:
        st.info("Pas encore de confrontation directe cette saison.")
    else:
        for _, row in df_confr.iterrows():
            st.markdown(f"J{row['matchday']} — **{row['domicile']}** {int(row['home_score'])} — {int(row['away_score'])} **{row['exterieur']}**")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — BUTEURS
# ══════════════════════════════════════════════════════════════════════════════

elif page == "👟 Buteurs":
    st.title("👟 Top Buteurs")

    df_sc = query(f"""
        SELECT sc.player_name, t.name AS equipe, t.tla,
               sc.goals, sc.assists,
               COALESCE(sc.penalties, 0) AS penalties
        FROM scorers sc
        JOIN teams t ON sc.team_id = t.id
        WHERE sc.season = '{SAISON}'
        ORDER BY sc.goals DESC, sc.assists DESC
    """)

    # KPIs
    if not df_sc.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("🥇 Meilleur buteur", df_sc.iloc[0]["player_name"],
                    f"{df_sc.iloc[0]['goals']} buts")
        top_passeur = df_sc.loc[df_sc["assists"].idxmax()]
        col2.metric("🎯 Top passeur", top_passeur["player_name"],
                    f"{top_passeur['assists']} passes")
        col3.metric("👥 Équipes représentées", df_sc["equipe"].nunique())

    st.divider()

    # Filtre par équipe
    equipes = ["Toutes"] + sorted(df_sc["equipe"].unique().tolist())
    filtre = st.selectbox("Filtrer par équipe", equipes)
    if filtre != "Toutes":
        df_sc = df_sc[df_sc["equipe"] == filtre]

    col_a, col_b = st.columns([2, 1])

    with col_a:
        st.subheader("Classement des buteurs")
        df_affichage = df_sc.copy()
        df_affichage.index = range(1, len(df_affichage) + 1)
        df_affichage.columns = ["Joueur", "Équipe", "Abrév.", "Buts", "Passes D.", "Pénaltys"]
        st.dataframe(df_affichage, use_container_width=True)

    with col_b:
        st.subheader("Buts par équipe")
        buts_par_equipe = df_sc.groupby("equipe")["goals"].sum().sort_values(ascending=True)
        fig = px.bar(
            buts_par_equipe,
            orientation="h",
            labels={"value": "Buts", "equipe": ""},
            color=buts_par_equipe.values,
            color_continuous_scale="Oranges",
        )
        fig.update_layout(showlegend=False, coloraxis_showscale=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Buts vs Passes décisives")
    fig2 = px.scatter(
        df_sc, x="goals", y="assists",
        text="player_name", color="equipe",
        labels={"goals": "Buts", "assists": "Passes décisives"},
        size="goals",
    )
    fig2.update_traces(textposition="top center")
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, use_container_width=True)
