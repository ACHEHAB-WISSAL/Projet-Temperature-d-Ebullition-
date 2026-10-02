# -*- coding: utf-8 -*-
"""
Application web Python (Streamlit) : acétone
  1) Débits après séparation
  2) Température d'ébullition
  3) Énergie pour vaporiser le flux chauffé
  4) Courbe Téb = f(P) (P de 0,1 à 3 atm, 25 points par défaut)

Installation :   pip install streamlit numpy pandas matplotlib
Lancement    :   python acetone_app.py   (ou : streamlit run acetone_app.py)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# Si le fichier est lancé avec "python fichier.py" (et non "streamlit run"),
# on relance automatiquement l'application dans le navigateur.
import sys
import subprocess
from streamlit.runtime.scriptrunner import get_script_run_ctx

if get_script_run_ctx() is None:
    subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])
    sys.exit()

st.set_page_config(page_title="Acétone – Ébullition et énergie", page_icon="🧪",
                   layout="wide")

st.markdown(
    """
    <style>
        .stApp {
            background: linear-gradient(180deg, #fff5fb 0%, #fdf2f8 100%);
        }

        .stApp, .stApp * {
            color: #5a2a3d;
        }

        h1, h2, h3, h4, h5, h6 {
            color: #a11d5b !important;
        }

        .stSidebar {
            background: linear-gradient(180deg, #ffe6f3 0%, #f9d9ea 100%);
        }

        .stSidebar * {
            color: #5a2a3d !important;
        }

        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.45);
            border: 1px solid #f3bfd8;
            border-radius: 10px;
            padding: 12px;
        }

        div[data-testid="stAlert"] {
            border-radius: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

ATM_TO_BAR = 1.01325

# Valeurs par défaut de tous les paramètres
DEFAUTS = {
    "T0": 10.0, "P": 1.0, "debit": 38.0, "frac": 40.0,
    "pmin": 0.1, "pmax": 3.0, "n": 25,
    "cp": 2.18, "dHnb": 501.0, "Tnb": 329.2, "Tc": 508.2,
    "A": 4.42448, "B": 1312.253, "C": -32.445,
}
for k, v in DEFAUTS.items():
    st.session_state.setdefault(k, v)


def reinitialiser():
    for k, v in DEFAUTS.items():
        st.session_state[k] = v


# ============================================================
# BARRE LATÉRALE : paramètres modifiables (boutons + / -)
# ============================================================
sb = st.sidebar
sb.header("Paramètres du procédé")
T0 = sb.number_input("Température initiale (°C)", -20.0, 50.0, step=0.5, key="T0")
P = sb.number_input("Pression de travail (atm)", 0.01, 10.0, step=0.05,
                    format="%.3f", key="P")
debit = sb.number_input("Débit massique initial (kg/h)", 0.1, 10000.0,
                        step=1.0, key="debit")
frac = sb.number_input("Part du flux haut, non chauffé (%)", 0.0, 100.0,
                       step=1.0, key="frac")

sb.header("Courbe Téb = f(P)")
pmin = sb.number_input("Pression minimale (atm)", 0.01, 10.0, step=0.05,
                       format="%.3f", key="pmin")
pmax = sb.number_input("Pression maximale (atm)", 0.01, 10.0, step=0.05,
                       format="%.3f", key="pmax")
n = sb.number_input("Nombre de points", 2, 500, step=1, key="n")

with sb.expander("Propriétés de l'acétone (avancé)"):
    cp = st.number_input("Cp liquide (kJ/kg/K)", 1.0, 4.0, step=0.01, key="cp")
    dHnb = st.number_input("Chaleur latente à Tnb (kJ/kg)", 300.0, 700.0,
                           step=1.0, key="dHnb")
    Tnb = st.number_input("Point d'ébullition normal (K)", 300.0, 360.0,
                          step=0.1, key="Tnb")
    Tc = st.number_input("Température critique (K)", 450.0, 560.0,
                         step=0.1, key="Tc")
    A = st.number_input("Antoine A", 3.0, 6.0, step=0.0001, format="%.5f", key="A")
    B = st.number_input("Antoine B", 800.0, 2000.0, step=0.1, format="%.3f", key="B")
    C = st.number_input("Antoine C", -80.0, 0.0, step=0.1, format="%.3f", key="C")

sb.button("Réinitialiser", on_click=reinitialiser)


# ============================================================
# FONCTIONS DE CALCUL
# ============================================================
def T_ebullition_K(p_atm):
    """Équation d'Antoine inversée : log10(P[bar]) = A - B/(T[K]+C)."""
    p_bar = np.asarray(p_atm, dtype=float) * ATM_TO_BAR
    return B / (A - np.log10(p_bar)) - C


def dHvap(T_K):
    """Chaleur latente (kJ/kg) à T, corrélation de Watson."""
    return dHnb * ((1 - T_K / Tc) / (1 - Tnb / Tc)) ** 0.38


# ============================================================
# CALCULS
# ============================================================
m_haut = frac / 100 * debit
m_chauff = debit - m_haut

Teb_K = float(T_ebullition_K(P))
Teb_C = Teb_K - 273.15
lat = float(dHvap(Teb_K))

Q_sensible = m_chauff * cp * max(Teb_C - T0, 0.0)   # kJ/h
Q_latent = m_chauff * lat                           # kJ/h
Q_total = Q_sensible + Q_latent                     # kJ/h

# ============================================================
# AFFICHAGE
# ============================================================
st.title("🧪 Acétone : ébullition et énergie de vaporisation")
st.caption("Modifiez un paramètre dans la barre latérale : tout se met à jour.")

st.subheader("1) Débits")
c1, c2, c3 = st.columns(3)
c1.metric("Débit initial", f"{debit:.2f} kg/h")
c2.metric("Flux haut (liquide)", f"{m_haut:.2f} kg/h")
c3.metric("Flux chauffé (vapeur)", f"{m_chauff:.2f} kg/h")

st.subheader("2) Température d'ébullition")
c1, c2, c3 = st.columns(3)
c1.metric(f"À {P:.3f} atm", f"{Teb_C:.2f} °C")
c2.metric("En kelvin", f"{Teb_K:.2f} K")
c3.metric("Chaleur latente", f"{lat:.1f} kJ/kg")

if T0 >= Teb_C:
    st.warning("La température initiale est ≥ à la température d'ébullition "
               "(pas de chaleur sensible).")
if Teb_K >= Tc:
    st.error("Pression hors du domaine de validité du modèle.")

st.subheader("3) Énergie pour vaporiser le flux chauffé")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Chaleur sensible", f"{Q_sensible:,.1f} kJ/h")
c2.metric("Chaleur latente", f"{Q_latent:,.1f} kJ/h")
c3.metric("Énergie totale", f"{Q_total:,.1f} kJ/h")
c4.metric("Puissance", f"{Q_total / 3600:.3f} kW")

st.subheader("4) Courbe de la température d'ébullition")
a, b = min(pmin, pmax), max(pmin, pmax)
P_vals = np.linspace(a, b, int(n))
Teb_vals = T_ebullition_K(P_vals) - 273.15

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(P_vals, Teb_vals, "o-", color="tab:blue", label="Téb (Antoine)")
ax.plot(P, Teb_C, "r*", markersize=15, label=f"P = {P:.2f} atm → {Teb_C:.1f} °C")
ax.set_xlabel("Pression (atm)")
ax.set_ylabel("Température d'ébullition (°C)")
ax.set_title("Température d'ébullition de l'acétone en fonction de la pression")
ax.grid(True, alpha=0.3)
ax.legend()
st.pyplot(fig)

with st.expander("Tableau des points"):
    st.dataframe(pd.DataFrame({"P (atm)": P_vals, "Téb (°C)": Teb_vals}),
                 width='stretch')