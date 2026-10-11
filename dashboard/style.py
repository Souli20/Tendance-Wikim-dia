import streamlit as st

CSS = """
#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1400px;}
.hero {
    padding: 1.4rem 1.8rem; border-radius: 16px; margin-bottom: 1.2rem;
    background: linear-gradient(120deg, #0F2A4A 0%, #11335C 55%, #0B1220 100%);
    border: 1px solid #1F2C47;
}
.hero h1 {margin: 0; font-size: 2rem; letter-spacing: 0.3px;}
.hero p {margin: 0.3rem 0 0 0; color: #8FA3C4; font-size: 0.95rem;}
.live {color: #22C55E; font-weight: 600; font-size: 0.85rem;}
.carte {
    background: #111B2E; border: 1px solid #1F2C47; border-radius: 14px;
    padding: 1rem 1.2rem; height: 100%;
}
.carte .titre {color: #8FA3C4; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px;}
.carte .valeur {font-size: 2rem; font-weight: 700; margin: 0.2rem 0;}
.carte .detail {font-size: 0.85rem; color: #8FA3C4;}
.synthese {
    background: #0F2A4A; border-left: 4px solid #00D4FF; border-radius: 10px;
    padding: 1rem 1.3rem; margin: 0.5rem 0 1.2rem 0; font-size: 1.05rem; line-height: 1.5;
}
"""


def appliquer_style():
    st.markdown("<style>" + CSS + "</style>", unsafe_allow_html=True)


def entete(titre, sous_titre):
    st.markdown(
        '<div class="hero"><h1>' + titre + "</h1><p>" + sous_titre + "</p></div>",
        unsafe_allow_html=True,
    )


def carte(titre, valeur, detail="", couleur="#E6EDF7"):
    st.markdown(
        '<div class="carte"><div class="titre">' + titre + "</div>"
        '<div class="valeur" style="color:' + couleur + '">' + valeur + "</div>"
        '<div class="detail">' + detail + "</div></div>",
        unsafe_allow_html=True,
    )


def encadre(texte):
    st.markdown('<div class="synthese">' + texte + "</div>", unsafe_allow_html=True)
