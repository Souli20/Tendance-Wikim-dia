from datetime import timedelta

import numpy as np
import pandas as pd

MINUTES_INCOMPLETES = 2


def ajouter_colonnes(df):
    df = df.copy()
    df["humains"] = df["nb_modifs"] - df["nb_bots"]
    df["sujet"] = df["wiki"].astype(str) + " | " + df["title"].astype(str)
    return df


def filtrer(df, exclure_techniques, recherche):
    if exclure_techniques:
        df = df[~df["wiki"].str.contains("wikidata|commons|test", case=False, na=False)]
    if recherche:
        df = df[df["title"].str.contains(recherche, case=False, na=False, regex=False)]
    return df


def serie_par_minute(df, colonne="nb_modifs"):
    s = df.groupby("window_start")[colonne].sum().sort_index()
    if s.empty:
        return s
    minutes = pd.date_range(s.index.min(), s.index.max(), freq="1min")
    s = s.reindex(minutes, fill_value=0)
    return s.iloc[:-MINUTES_INCOMPLETES]


def pouls(serie, fenetre=10):
    recent = serie.tail(fenetre).mean()
    reference = serie.iloc[:-fenetre].tail(fenetre * 3).mean()
    if pd.isna(reference) or reference == 0:
        return recent, None, None
    variation = 100 * (recent - reference) / reference
    return recent, reference, variation


def sujets_emergents(df, colonne="nb_modifs", fenetre=10, volume_min=5, top=10):
    if df.empty:
        return pd.DataFrame()
    limite = df["window_start"].max() - timedelta(minutes=MINUTES_INCOMPLETES)
    d = df[df["window_start"] <= limite]
    debut_recent = limite - timedelta(minutes=fenetre)
    debut_precedent = debut_recent - timedelta(minutes=fenetre)
    recent = d[d["window_start"] > debut_recent].groupby("sujet")[colonne].sum()
    precedent = (
        d[(d["window_start"] > debut_precedent) & (d["window_start"] <= debut_recent)]
        .groupby("sujet")[colonne].sum()
    )
    t = pd.concat([recent.rename("recent"), precedent.rename("precedent")], axis=1).fillna(0)
    t.index.name = "sujet"
    t = t[t["recent"] >= volume_min]
    if t.empty:
        return pd.DataFrame()
    t["ecart"] = t["recent"] - t["precedent"]
    t["variation"] = 100 * t["ecart"] / t["precedent"].clip(lower=1)
    t = t[t["ecart"] > 0]
    return t.sort_values(["ecart", "variation"], ascending=False).head(top).reset_index()


def anomalies(serie, seuil=3.0, fenetre=30):
    if len(serie) < 15:
        return pd.DataFrame()
    moyenne = serie.rolling(fenetre, min_periods=10).mean().shift(1)
    ecart_type = serie.rolling(fenetre, min_periods=10).std().shift(1).replace(0, np.nan)
    z = (serie - moyenne) / ecart_type
    a = pd.DataFrame({
        "minute": serie.index,
        "modifications": serie.values,
        "normale": moyenne.values,
        "score": z.values,
    })
    return a[a["score"] > seuil].sort_values("minute", ascending=False)


def projection(serie, horizon=15, fenetre=30):
    recent = serie.tail(fenetre)
    if len(recent) < 15:
        return pd.DataFrame()
    x = np.arange(len(recent))
    pente, ordonnee = np.polyfit(x, recent.values, 1)
    ajuste = pente * x + ordonnee
    sigma = float(np.std(recent.values - ajuste))
    futur_x = np.arange(len(recent), len(recent) + horizon)
    valeurs = np.clip(pente * futur_x + ordonnee, 0, None)
    minutes = pd.date_range(recent.index[-1] + pd.Timedelta(minutes=1), periods=horizon, freq="1min")
    marge = 1.96 * sigma
    return pd.DataFrame({
        "minute": minutes,
        "projection": valeurs,
        "bas": np.clip(valeurs - marge, 0, None),
        "haut": valeurs + marge,
    })


def synthese(total, minutes, sujet_top, variation, proj):
    phrases = [
        f"Sur les {minutes} dernières minutes, {total:,} modifications ont été enregistrées.".replace(",", " ")
    ]
    if sujet_top:
        phrases.append(f"Le sujet qui progresse le plus est « {sujet_top} ».")
    if variation is not None:
        if variation > 25:
            tendance = "en forte hausse"
        elif variation < -25:
            tendance = "en baisse"
        else:
            tendance = "stable"
        phrases.append(f"L'activité récente est {tendance} ({variation:+.0f} % par rapport à la normale).")
    if proj is not None and not proj.empty:
        phrases.append(
            f"Si la tendance se poursuit, on devrait observer environ {proj['projection'].iloc[-1]:.0f} "
            "modifications par minute dans 15 minutes (extrapolation à très court terme)."
        )
    return " ".join(phrases)
