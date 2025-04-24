import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import folium
from streamlit_folium import st_folium

# --- Configuration de la page ---
st.set_page_config(page_title="City Fighting", layout="wide")

# --- Palette de couleurs ---
palette = ["#390099", "#9E0059", "#FF0054", "#FF5400", "#FFBD00"]

# --- Thème Plotly ---
plotly_theme = {
    "layout": {
        "colorway": palette,
        "font": {"family": "Arial", "size": 12, "color": "#333"},
        "title": {"font": {"size": 20, "color": "#333"}},
        "xaxis": {"titlefont": {"size": 14, "color": "#333"}},
        "yaxis": {"titlefont": {"size": 14, "color": "#333"}},
        "plot_bgcolor": "rgba(0,0,0,0)",
        "paper_bgcolor": "rgba(0,0,0,0)",
    }
}

# --- Initialisation session ---
if "page" not in st.session_state:
    st.session_state.page = "Accueil"

# Force l'état de la page à 'Accueil' au démarrage
if not st.session_state.get("app_started", False):
    st.session_state["page"] = "Accueil"
    st.session_state["app_started"] = True

# --- Fonction pour charger les données ---
@st.cache_data
def charger_villes():
    df = pd.read_csv("base_comparateur.csv", sep=";", encoding='cp1252', dtype={"CODGEO": str})
    df = df[df["P21_POP"] > 20000]
    return df

# --- CSS pour le style global ---
st.markdown(
    """
    <style>
    .stApp {color: #333; font-family: 'Arial', sans-serif;}
    .center {display: flex; justify-content: center; align-items: center; text-align: center;}
    </style>
    """,
    unsafe_allow_html=True
)

# --- Barre latérale ---
with st.sidebar:
    accueil_clicked = st.button("🏠 Accueil")
    if accueil_clicked:
        st.session_state.page = "Accueil"

    df_villes = charger_villes()
    villes = df_villes["LIBGEO"].sort_values().unique()
    ville1 = st.selectbox("Choisis la première ville 🌆", villes, key="ville1")
    ville2 = st.selectbox("Choisis la seconde ville 🌇", villes, index=1, key="ville2")
    df_ville1 = df_villes[df_villes["LIBGEO"] == ville1].iloc[0]
    df_ville2 = df_villes[df_villes["LIBGEO"] == ville2].iloc[0]

    st.markdown('<h2 class="center">Que cherches-tu?</h2>', unsafe_allow_html=True)

    selected_menu = st.radio(
        "Choisir une section",
        ("Démographie", "Emploi", "Logement", "Climat", "Niveau de vie", "Tourisme"),
        key="menu_radio"
    )

    # Mise à jour de la page seulement si l'utilisateur n'a pas cliqué sur Accueil
    if not accueil_clicked:
        st.session_state.page = selected_menu

# --- Définition des fonctions ---
def get_openweather(city, api_key):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&lang=fr&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temp_c = data['main']['temp']
        humidity = data['main']['humidity']
        pressure = data['main']['pressure']
        weather_desc = data['weather'][0]['description'].capitalize()
        wind = data['wind']['speed']
        icon = data['weather'][0]['icon']
        return {
            "temp_c": round(temp_c, 1),
            "humidity": humidity,
            "pressure": pressure,
            "description": weather_desc,
            "wind": wind,
            "icon": icon
        }
    else:
        return None

def get_forecast(city, api_key):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&lang=fr&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['list']  # Liste des prévisions (toutes les 3 heures)
    else:
        return None

def meteo_emoji(description):
    description = description.lower()
    if "soleil" in description or "dégagé" in description:
        return "☀️"
    elif "pluie" in description or "averse" in description:
        return "🌧️"
    elif "nuage" in description:
        return "☁️"
    elif "orage" in description:
        return "⛈️"
    elif "neige" in description:
        return "❄️"
    elif "brume" in description or "brouillard" in description:
        return "🌫️"
    else:
        return "🌡️"

# Fonction pour récupérer les données touristiques avec l'API DATAtourisme
def get_tourism_data(city_name, api_key):
    # Requête GraphQL pour les POI touristiques d'une ville (exemple pour Paris)
    query = """
    {
      poi(
        first: 30,
        where: {
          address: {city: "%s"},
          category: {in: ["MUSEE", "MONUMENT", "PARC_JARDIN", "SITE_NATUREL"]}
        }
      ) {
        name
        category
        address {city, postalCode, streetAddress}
        latitude
        longitude
        description
        url
      }
    }
    """ % city_name

    headers = {"Content-Type": "application/json"}
    # Jeton d'API public (limité), pour usage réel demander un token sur datatourisme.fr
    url = "https://api.datatourisme.fr/graphql"
    response = requests.post(url, json={"query": query}, headers=headers)
    if response.status_code == 200:
        data = response.json()
        pois = data["data"]["poi"]
        return pois
    else:
        return []

# --- Contenu principal de l'application ---
if st.session_state.page == "Accueil":
    st.markdown('<h1 class="center"> 🌍 Comparaison entre 2 grandes villes françaises 🔍 </h1>', unsafe_allow_html=True)
    st.markdown('<h3 class="center">Explorez les données pour comparer ces deux villes</h3>', unsafe_allow_html=True)
    st.markdown("---")
    st.write("Utilisez le menu latéral pour naviguer entre les différentes sections.")
    st.write("- **Démographie** : Découvrez les chiffres clés.")
    st.write("- **Emploi** : Comparez les opportunités.")
    st.write("- **Logement** : Analysez le marché.")
    st.write("- **Climat** : Consultez la météo.")
    st.write("- **Niveau de vie** : Évaluez les conditions.")
    st.write("- **Tourisme** : Comparez les sites touristiques.")
    st.markdown("---")
    st.write("""Crédits:
    \nAya El-Yaouti, Mariam N'Diaye, Lorynda Loufoua.
    \nIUT Paris Rives de Seine""")

elif st.session_state.page == "Démographie":
    st.header("Démographie")
    # Barres : Population, Naissances, Décès
    demo_df = pd.DataFrame({
        "Ville": [ville1, ville2],
        "Population 2021": [df_ville1["P21_POP"], df_ville2["P21_POP"]],
        "Population 2015": [df_ville1["P15_POP"], df_ville2["P15_POP"]],
        "Naissances 2015-2020": [df_ville1["NAIS1520"], df_ville2["NAIS1520"]],
        "Décès 2015-2020": [df_ville1["DECE1520"], df_ville2["DECE1520"]],
        "Naissances 2023": [df_ville1["NAISD23"], df_ville2["NAISD23"]],
        "Décès 2023": [df_ville1["DECESD23"], df_ville2["DECESD23"]],
        "15-64 ans": [df_ville1["P21_POP1564"], df_ville2["P21_POP1564"]],
        "Chômeurs 15-64 ans": [df_ville1["P21_CHOM1564"], df_ville2["P21_CHOM1564"]],
        "Actifs 15-64 ans": [df_ville1["P21_ACT1564"], df_ville2["P21_ACT1564"]],
    })

    # Calcul de la densité pour chaque ville
    densite1 = df_ville1["P21_POP"] / df_ville1["SUPERF"]
    densite2 = df_ville2["P21_POP"] / df_ville2["SUPERF"]

    # Affichage des indicateurs principaux
    st.markdown(f"## 📌 Chiffres clés")

    # Affichage des indicateurs principaux
    col1, col2, col3 = st.columns(3)
    with col1:
        ville1
        st.metric(label=f"#### Population 👥 ", value=df_ville1["P21_POP"])
        st.metric(label=f"#### Superficie (km²) 📐 ", value=float(df_ville1["SUPERF"]))
        st.metric(label=f"#### Densité 🚶‍♂️)", value=round(densite1, 1))
    with col2:
        ville2
        st.metric(label=f"#### Population 👥 ", value=df_ville2["P21_POP"])
        st.metric(label=f"#### Superficie (km²) 📐", value=float(df_ville2["SUPERF"]))
        st.metric(label=f"#### Densité 🚶‍♂️", value=round(densite2, 1))

    # Population
    fig_pop = px.bar(demo_df, x="Ville", y=["Population 2015", "Population 2021"], barmode="group",
                    title="Évolution de la population", color_discrete_sequence=palette)
    st.plotly_chart(fig_pop, use_container_width=True)

    # Naissances et décès
    fig_naiss_deces = px.bar(demo_df, x="Ville",
        y=["Naissances 2015-2020", "Décès 2015-2020", "Naissances 2023", "Décès 2023"],
        barmode="group", title="Naissances et décès", color_discrete_sequence=palette)
    st.plotly_chart(fig_naiss_deces, use_container_width=True)


elif st.session_state.page == "Emploi":
    st.header("Emploi")
    # 1. Comparaison du nombre d’emplois
    emploi_df = pd.DataFrame({
        "Ville": [ville1, ville2],
        "Emplois salariés et non-salariés": [df_ville1["P21_EMPLT"], df_ville2["P21_EMPLT"]],
        "Emplois salariés": [df_ville1["P21_EMPLT_SAL"], df_ville2["P21_EMPLT_SAL"]],
        "Chômeurs 15-64 ans": [df_ville1["P21_CHOM1564"], df_ville2["P21_CHOM1564"]],
        "Actifs 15-64 ans": [df_ville1["P21_ACT1564"], df_ville2["P21_ACT1564"]],
        "Taux de pauvreté (%)": [df_ville1["TP6021"], df_ville2["TP6021"]],
        "Médiane niveau de vie (€)": [df_ville2["MED21"],df_ville2["MED21"]],
        "Établissements actifs 2022": [df_ville1["ETTOT22"], df_ville2["ETTOT22"]],
        "Agriculture": [df_ville1["ETAZ22"], df_ville2["ETAZ22"]],
        "Industrie": [df_ville1["ETBE22"], df_ville2["ETBE22"]],
        "Construction": [df_ville1["ETFZ22"], df_ville2["ETFZ22"]],
        "Commerce/Services": [df_ville1["ETGU22"], df_ville2["ETGU22"]],
        "Commerce auto": [df_ville1["ETGZ22"], df_ville2["ETGZ22"]],
        "Admin/Santé/Éducation": [df_ville1["ETOQ22"], df_ville2["ETOQ22"]],
        "1-9 salariés": [df_ville1["ETTEF122"], df_ville2["ETTEF122"]],
        "10+ salariés": [df_ville1["ETTEFP1022"], df_ville2["ETTEFP1022"]],
    })

    # Barres : Emplois et établissements
    fig1 = px.bar(emploi_df.melt(id_vars="Ville",
                 value_vars=["Emplois salariés et non-salariés", "Emplois salariés"]),
                 x="variable", y="value", color="Ville", barmode="group",
                 title="Comparaison des emplois (2021)", color_discrete_sequence=palette)


    # Pie chart : Répartition Actifs/Chômeurs pour chaque ville
    col1, col2 = st.columns(2)
    with col1:
        pie1 = px.pie(
            names=["Actifs occupés", "Chômeurs"],
            values=[
                df_ville1["P21_ACT1564"] - df_ville1["P21_CHOM1564"],
                df_ville1["P21_CHOM1564"]
            ],
            title=f"Répartition actifs/chômeurs - {ville1}"
        ).update_layout(plotly_theme["layout"])
        st.plotly_chart(pie1, use_container_width=True)
    with col2:
        pie2 = px.pie(
            names=["Actifs occupés", "Chômeurs"],
            values=[
                df_ville2["P21_ACT1564"] - df_ville2["P21_CHOM1564"],
                df_ville2["P21_CHOM1564"]
            ],
            title=f"Répartition actifs/chômeurs - {ville2}"
        ).update_layout(plotly_theme["layout"])
        st.plotly_chart(pie2, use_container_width=True)

    # Taux de chômage (barres)
    taux_chom1 = 100 * df_ville1["P21_CHOM1564"] / df_ville1["P21_ACT1564"] if df_ville1["P21_ACT1564"] else 0
    taux_chom2 = 100 * df_ville2["P21_CHOM1564"] / df_ville2["P21_ACT1564"] if df_ville2["P21_ACT1564"] else 0
    taux_df = pd.DataFrame({
        "Ville": [ville1, ville2],
        "Taux de chômage (%)": [taux_chom1, taux_chom2]
    })
    fig3 = px.bar(
        taux_df, x="Ville", y="Taux de chômage (%)", color="Ville",
        title="Taux de chômage des 15-64 ans (2021)"
    ).update_layout(plotly_theme["layout"])
    st.plotly_chart(fig3, use_container_width=True)

    # Barres : Répartition des établissements par secteur
    fig4 = px.bar(emploi_df.melt(id_vars="Ville", value_vars=["Agriculture", "Industrie", "Construction", "Commerce/Services", "Commerce auto", "Admin/Santé/Éducation"]),
                      x="variable", y="value", color="Ville", barmode="group",
                      labels={"variable": "Secteur", "value": "Nombre d'établissements"},
                      title="Établissements actifs par secteur (2022)").update_layout(plotly_theme["layout"])
    st.plotly_chart(fig4, use_container_width=True)

    # Barres : Taille des établissements
    fig5 = px.bar(emploi_df.melt(id_vars="Ville", value_vars=["1-9 salariés", "10+ salariés"]),
                        x="variable", y="value", color="Ville", barmode="group",
                        labels={"variable": "Taille", "value": "Établissements"},
                        title="Taille des établissements actifs (2022)").update_layout(plotly_theme["layout"])
    st.plotly_chart(fig5, use_container_width=True)

elif st.session_state.page == "Logement":
    st.header("Logement")

    logement_df = pd.DataFrame({
        "Ville": [ville1, ville2],
        "Logements": [df_ville1["P21_LOG"], df_ville2["P21_LOG"]],
        "Résidences principales": [df_ville1["P21_RP"], df_ville2["P21_RP"]],
        "Résidences secondaires": [df_ville1["P21_RSECOCC"], df_ville2["P21_RSECOCC"]],
        "Logements vacants": [df_ville1["P21_LOGVAC"], df_ville2["P21_LOGVAC"]],
        "Occupé par les propriétaires": [df_ville1["P21_RP_PROP"], df_ville2["P21_RP_PROP"]],
    })

    # Barres : Répartition des logements
    fig_log = px.bar(logement_df.melt(id_vars="Ville"), x="variable", y="value", color="Ville", barmode="group",
                     labels={"variable": "Type de logement", "value": "Nombre"},
                     title="Répartition des logements en 2021").update_layout(plotly_theme["layout"])
    st.plotly_chart(fig_log, use_container_width=True)

    # Camembert : Structure du parc de logements pour chaque ville
    col1, col2 = st.columns(2)
    with col1:
        pie1 = px.pie(
            names=["Résidences principales", "Résidences secondaires", "Logements vacants"],
            values=[df_ville1["P21_RP"], df_ville1["P21_RSECOCC"], df_ville1["P21_LOGVAC"]],
            title=f"Structure du parc de logements - {ville1}"
        ).update_layout(plotly_theme["layout"])
        st.plotly_chart(pie1, use_container_width=True)
    with col2:
        pie2 = px.pie(
            names=["Résidences principales", "Résidences secondaires", "Logements vacants"],
            values=[df_ville2["P21_RP"], df_ville2["P21_RSECOCC"], df_ville2["P21_LOGVAC"]],
            title=f"Structure du parc - {ville2}"
        ).update_layout(plotly_theme["layout"])
        st.plotly_chart(pie2, use_container_width=True)

elif st.session_state.page == "Climat":
    st.header("Climat")
    API_KEY = "9e86cfd9a711bbbc18064c42b7948771"

    col1, col2 = st.columns(2)

    with col1:
        city1_weather = get_openweather(ville1 + ",FR", API_KEY)
        if city1_weather:
            st.subheader(f"{ville1}")
            st.write(f"**{city1_weather['description']}**")
            st.image(f"http://openweathermap.org/img/wn/{city1_weather['icon']}@2x.png", width=150)
            st.metric("🌡️ Température", f"{city1_weather['temp_c']}°C")
            st.metric("💧 Humidité", f"{city1_weather['humidity']}%")
            st.metric("🌬️ Vent", f"{city1_weather['wind']} m/s")

        else:
            st.error(f"Données météo {ville1} indisponibles.")

    with col2:
        city2_weather = get_openweather(ville2 + ",FR", API_KEY)
        if city2_weather:
            st.subheader(f"{ville2}")
            st.write(f"**{city2_weather['description']}**")
            st.image(f"http://openweathermap.org/img/wn/{city2_weather['icon']}@2x.png", width=150)
            st.metric("🌡️ Température", f"{city2_weather['temp_c']}°C")
            st.metric("💧 Humidité", f"{city2_weather['humidity']}%")
            st.metric("🌬️ Vent", f"{city2_weather['wind']} m/s")
        else:
            st.error(f"Données météo {ville2} indisponibles.")

    # Prévisions météo
    st.subheader("Prévisions météo sur 5 jours")
    forecast1 = get_forecast(ville1 + ",FR", API_KEY)
    forecast2 = get_forecast(ville2 + ",FR", API_KEY)

    if forecast1 and forecast2:
        # Préparation des données pour les tableaux
        forecast_data1 = []
        forecast_data2 = []

        days = ["Aujourd'hui", "Demain", "Après-demain", "Dans 3 jours", "Dans 4 jours"]
        forecast_data1 = []
        forecast_data2 = []

        for i, day in enumerate(days):
            midday_forecast1 = forecast1[i * 8 + 4]
            midday_forecast2 = forecast2[i * 8 + 4]
            desc1 = midday_forecast1['weather'][0]['description'].capitalize()
            desc2 = midday_forecast2['weather'][0]['description'].capitalize()
            forecast_data1.append({
                "Jour": day,
                "Météo": f"{meteo_emoji(desc1)} {desc1}",
                "Température (°C)": f"{midday_forecast1['main']['temp']:.1f}",
                "Humidité (%)": f"{midday_forecast1['main']['humidity']}",
                "Vent (m/s)": f"{midday_forecast1['wind']['speed']:.1f}"
            })
            forecast_data2.append({
                "Jour": day,
                "Météo": f"{meteo_emoji(desc2)} {desc2}",
                "Température (°C)": f"{midday_forecast2['main']['temp']:.1f}",
                "Humidité (%)": f"{midday_forecast2['main']['humidity']}",
                "Vent (m/s)": f"{midday_forecast2['wind']['speed']:.1f}"
            })

        df_forecast1 = pd.DataFrame(forecast_data1)
        df_forecast2 = pd.DataFrame(forecast_data2)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"#### {ville1}")
            st.dataframe(df_forecast1, use_container_width=True, hide_index=True)
        with col2:
            st.markdown(f"#### {ville2}")
            st.dataframe(df_forecast2, use_container_width=True, hide_index=True)

        st.markdown(
                "<div style='color: gray; font-size: 11px; margin-top: -10px;'>"
                "Source : <a href='https://openweathermap.org/' style='color: gray;' target='_blank'>OpenWeatherMap API</a>"
                "</div>",
                unsafe_allow_html=True
            )

elif st.session_state.page == "Niveau de vie":
    st.header("Niveau de vie")
    # 1. Comparaison du niveau de vie
    niveau_df = pd.DataFrame({
        "Ville": [ville1, ville2],
        "Médiane du niveau de vie (€)": [df_ville2["MED21"],df_ville2["MED21"]],
        "Taux de pauvreté (%)": [df_ville1["TP6021"], df_ville2["TP6021"]],
         "Ménages fiscaux 2021": [df_ville1["NBMENFISC21"], df_ville2["NBMENFISC21"]],
        "Part ménages imposés (%)": [df_ville1["PIMP21"], df_ville2["PIMP21"]],

    })

    # Diagramme à barres groupées
    fig1 = px.bar(niveau_df.melt(id_vars="Ville"), x="variable", y="value", color="Ville", barmode="group",
                     labels={"variable": "Indicateur", "value": "Valeur"},
                     title="Comparaison du niveau de vie des villes").update_layout(plotly_theme["layout"])
    st.plotly_chart(fig1, use_container_width=True)

# Affiche source INSEE sauf dans l'onglet Climat
if st.session_state.page != "Climat":
    st.markdown(
        "<div style='color: gray; font-size: 11px; margin-top: -10px;'>"
        "Source : <a href='https://www.insee.fr/fr/statistiques/2521169#consulter' style='color: gray;' target='_blank'>INSEE</a>"
        "</div>",
        unsafe_allow_html=True
    )
