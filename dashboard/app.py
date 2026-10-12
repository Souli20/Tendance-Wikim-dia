from datetime import datetime, timedelta, timezone

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pymongo import MongoClient

from analytics import (
    ajouter_colonnes, anomalies, filtrer, pouls, projection,
    serie_par_minute, sujets_emergents, synthese,
)
from style import appliquer_style, carte, encadre, entete

st.set_page_config(page_title="Wikimédia Pulse", page_icon="📡", layout="wide")
appliquer_style()
entete(
    "Wikimédia Pulse",
    '<span class="live">● EN DIRECT</span> &nbsp;·&nbsp; Activité éditoriale mondiale, minute par minute '
    "&nbsp;·&nbsp; Kafka → Spark Streaming → MongoDB",
)


@st.cache_resource
def get_collection():
    client = MongoClient("mongodb://localhost:27017")
    return client["wiki_db"]["trends_per_minute"]


def charger(minutes):
    debut = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=minutes)
    lignes = list(get_collection().find({"window_start": {"$gte": debut}}, {"_id": 0}))
    return pd.DataFrame(lignes)


def fmt(n):
    return f"{n:,}".replace(",", " ")


def habiller(fig, hauteur=380):
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=30, b=10), height=hauteur,
        legend=dict(orientation="h", y=1.12),
    )
    return fig


def etat(variation):
    if variation is None:
        return "Indéterminé", "#8FA3C4"
    if variation > 25:
        return "En forte hausse", "#EF4444"
    if variation < -25:
        return "En baisse", "#F59E0B"
    return "Stable", "#22C55E"


# ----- Filtres -----
st.sidebar.header("Filtres")
minutes = st.sidebar.select_slider("Période (minutes)", options=[15, 30, 60, 180, 360], value=60)
exclure_techniques = st.sidebar.checkbox("Exclure Commons, Wikidata et wikis de test", value=True)
humains_seulement = st.sidebar.checkbox("Modifications humaines uniquement", value=False)
recherche = st.sidebar.text_input("Rechercher un sujet (titre de page)")
top_n = st.sidebar.slider("Taille des classements", 5, 30, 10)
volume_min = st.sidebar.slider("Volume minimal d'un sujet émergent", 3, 30, 5)
rafraichissement = st.sidebar.select_slider("Rafraîchissement (secondes)", options=[5, 10, 30, 60], value=10)


def afficher():
    brut = charger(minutes)
    if brut.empty:
        st.warning("Aucune donnée dans MongoDB pour cette période.")
        return

    df = filtrer(ajouter_colonnes(brut), exclure_techniques, recherche)
    colonne = "humains" if humains_seulement else "nb_modifs"
    if df.empty or df[colonne].sum() == 0:
        st.info("Aucune ligne ne correspond aux filtres.")
        return

    total = int(df[colonne].sum())
    pages = df.loc[df[colonne] > 0, "sujet"].nunique()
    total_brut = int(df["nb_modifs"].sum())
    bots = int(df["nb_bots"].sum())
    part_bots = 100 * bots / total_brut if total_brut else 0
    derniere = df["window_start"].max()

    serie = serie_par_minute(df, colonne)
    recent, normale, variation = (None, None, None)
    proj = pd.DataFrame()
    if len(serie) >= 15:
        recent, normale, variation = pouls(serie)
        proj = projection(serie)
    anom = anomalies(serie)
    emergents = sujets_emergents(df, colonne, volume_min=volume_min, top=top_n)
    libelle, couleur = etat(variation)
    sujet_top = emergents.iloc[0]["sujet"] if not emergents.empty else None

    onglet1, onglet2, onglet3 = st.tabs(["Synthèse", "Sujets", "Détails"])

    # ========== ONGLET 1 : SYNTHÈSE ==========
    with onglet1:
        encadre(synthese(total, minutes, sujet_top, variation, proj))

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            carte("Modifications", fmt(total), f"sur les {minutes} dernières minutes", "#00D4FF")
        with c2:
            carte("Sujets touchés", fmt(pages), "pages différentes")
        with c3:
            couleur_bots = "#F59E0B" if part_bots > 60 else "#22C55E"
            carte("Part des bots", f"{part_bots:.0f} %", "du total des modifications", couleur_bots)
        with c4:
            detail = f"{variation:+.0f} % vs normale" if variation is not None else "historique insuffisant"
            carte("État de l'activité", libelle, detail, couleur)

        st.write("")
        gauche, droite = st.columns([1, 2])

        with gauche:
            st.subheader("Pouls")
            if variation is None:
                st.info("Historique insuffisant (il faut au moins 15 minutes de données continues).")
            else:
                jauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=max(min(variation, 200), -100),
                    number={"suffix": " %", "valueformat": "+.0f"},
                    title={"text": "Écart à la normale"},
                    gauge={
                        "axis": {"range": [-100, 200]},
                        "bar": {"color": couleur},
                        "steps": [
                            {"range": [-100, -25], "color": "#3B2A12"},
                            {"range": [-25, 25], "color": "#12351F"},
                            {"range": [25, 200], "color": "#3B1616"},
                        ],
                    },
                ))
                st.plotly_chart(habiller(jauge, 260), width="stretch")
                st.caption(f"Activité récente : {recent:.0f} modifications par minute.")

            st.subheader("Alertes")
            if anom.empty:
                st.success("Aucune anomalie détectée.")
            else:
                for _, ligne in anom.head(5).iterrows():
                    st.error(
                        f"{ligne['minute']:%H:%M} UTC : {ligne['modifications']:.0f} modifications "
                        f"(normale ≈ {ligne['normale']:.0f}, score {ligne['score']:.1f})"
                    )

        with droite:
            st.subheader("Activité par minute et projection à 15 minutes")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=serie.index, y=serie.values, mode="lines", name="Activité",
                line=dict(color="#00D4FF", width=2.5),
                fill="tozeroy", fillcolor="rgba(0,212,255,0.10)",
            ))
            if not proj.empty:
                fig.add_trace(go.Scatter(
                    x=proj["minute"], y=proj["haut"], mode="lines",
                    line=dict(width=0), showlegend=False, hoverinfo="skip",
                ))
                fig.add_trace(go.Scatter(
                    x=proj["minute"], y=proj["bas"], mode="lines", line=dict(width=0),
                    fill="tonexty", fillcolor="rgba(245,158,11,0.20)",
                    name="Marge d'incertitude", hoverinfo="skip",
                ))
                fig.add_trace(go.Scatter(
                    x=proj["minute"], y=proj["projection"], mode="lines", name="Projection",
                    line=dict(color="#F59E0B", dash="dash", width=2),
                ))
            if not anom.empty:
                fig.add_trace(go.Scatter(
                    x=anom["minute"], y=anom["modifications"], mode="markers", name="Anomalie",
                    marker=dict(color="#EF4444", size=10),
                ))
            fig.update_layout(xaxis_title="Minute (UTC)", yaxis_title="Modifications")
            st.plotly_chart(habiller(fig, 420), width="stretch")
            st.caption(
                "La projection est une extrapolation linéaire de la tendance des 30 dernières minutes. "
                "Elle n'a de valeur qu'à très court terme."
            )

    # ========== ONGLET 2 : SUJETS ==========
    with onglet2:
        st.subheader("Sujets émergents : ceux qui accélèrent le plus")
        if emergents.empty:
            st.info("Aucun sujet émergent pour le moment (essayez de baisser le volume minimal).")
        else:
            g, d = st.columns([3, 2])
            with g:
                tableau = emergents.rename(columns={
                    "sujet": "Sujet", "recent": "10 dernières min",
                    "precedent": "10 min précédentes", "ecart": "Écart", "variation": "Variation %",
                })
                tableau["Variation %"] = tableau["Variation %"].round(0)
                st.dataframe(tableau, width="stretch", hide_index=True)
            with d:
                fig = px.bar(
                    emergents.sort_values("ecart"), x="ecart", y="sujet", orientation="h",
                    color="variation", color_continuous_scale="Sunset",
                    labels={"ecart": "Gain de modifications", "sujet": "", "variation": "Variation %"},
                )
                st.plotly_chart(habiller(fig, 380), width="stretch")

        g, d = st.columns(2)
        with g:
            st.subheader(f"Top {top_n} des sujets les plus modifiés")
            top = df.groupby("sujet", as_index=False)[colonne].sum().nlargest(top_n, colonne)
            fig = px.bar(
                top.sort_values(colonne), x=colonne, y="sujet", orientation="h",
                labels={colonne: "Modifications", "sujet": ""},
            )
            fig.update_traces(marker_color="#00D4FF")
            st.plotly_chart(habiller(fig, 420), width="stretch")
        with d:
            st.subheader("Répartition par wiki (top 10)")
            par_wiki = df.groupby("wiki", as_index=False)[colonne].sum().nlargest(10, colonne)
            fig = px.bar(par_wiki, x="wiki", y=colonne, labels={colonne: "Modifications", "wiki": ""})
            fig.update_traces(marker_color="#7C3AED")
            st.plotly_chart(habiller(fig, 420), width="stretch")

        st.subheader("Carte des sujets (taille = nombre de modifications)")
        arbre = df.groupby(["wiki", "title"], as_index=False)[colonne].sum().nlargest(40, colonne)
        fig = px.treemap(arbre, path=[px.Constant("Wikimédia"), "wiki", "title"], values=colonne)
        st.plotly_chart(habiller(fig, 450), width="stretch")

        st.subheader("Carte thermique : activité par wiki et par tranche de 5 minutes")
        top_wikis = df.groupby("wiki")[colonne].sum().nlargest(8).index
        h = df[df["wiki"].isin(top_wikis)].copy()
        h["tranche"] = h["window_start"].dt.floor("5min")
        pivot = h.pivot_table(index="wiki", columns="tranche", values=colonne, aggfunc="sum", fill_value=0)
        pivot.columns = pivot.columns.strftime("%H:%M")
        fig = px.imshow(
            pivot, aspect="auto", color_continuous_scale="Blues",
            labels=dict(x="Tranche de 5 min (UTC)", y="Wiki", color="Modifs"),
        )
        st.plotly_chart(habiller(fig, 380), width="stretch")

    # ========== ONGLET 3 : DÉTAILS ==========
    with onglet3:
        g, d = st.columns([1, 2])
        with g:
            st.subheader("Bots contre humains")
            repartition = pd.DataFrame({
                "Type": ["Humains", "Bots"],
                "Modifications": [int(df["humains"].sum()), bots],
            })
            fig = px.pie(
                repartition, names="Type", values="Modifications", hole=0.45,
                color="Type", color_discrete_map={"Humains": "#22C55E", "Bots": "#F59E0B"},
            )
            st.plotly_chart(habiller(fig, 360), width="stretch")
        with d:
            st.subheader("Données détaillées (200 lignes les plus récentes)")
            detail = df.drop(columns=["sujet"]).sort_values("window_start", ascending=False)
            st.dataframe(detail.head(200), width="stretch", hide_index=True)

    st.caption(
        "Dernière minute reçue : " + derniere.strftime("%H:%M") + " UTC · Mise à jour : "
        + datetime.now(timezone.utc).strftime("%H:%M:%S") + " UTC · Les 2 dernières minutes, "
        "encore incomplètes, sont exclues des calculs de tendance."
    )


st.fragment(run_every=f"{rafraichissement}s")(afficher)()
