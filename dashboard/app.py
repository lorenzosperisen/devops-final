import os
import streamlit as st
import httpx
import pandas as pd
import time

# Récupération des configurations globales depuis l'environnement
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
API_KEY = os.getenv("API_KEY", "")

st.set_page_config(
    page_title="DevOps Monitoring Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 DevOps Monitoring Dashboard")
st.caption("Système de supervision des ressources et de disponibilité en temps réel")

# --- ONGLETS PRINCIPAUX ---
tab_metrics, tab_servers = st.tabs(["📈 Métriques Système", "🖥️ Gestion des Serveurs"])

# ---------------------------------------------------------
# ONGLET 1 : MÉTRIQUES EN DIRECT
# ---------------------------------------------------------
with tab_metrics:
    st.subheader("Indicateurs de Performance en Temps Réel")
    
    # Bouton pour rafraîchir manuellement (Streamlit rejoue tout le script)
    if st.button("🔄 Actualiser les métriques"):
        st.rerun()

    # Initialisation de l'historique dans le state pour le graphique de 60 secondes
    if "metrics_history" not in st.session_state:
        st.session_state.metrics_history = pd.DataFrame(columns=["Temps", "CPU", "Mémoire", "Disque"])

    # Récupération des métriques depuis le backend API
    try:
        with httpx.Client() as client:
            response = client.get(f"{API_BASE_URL}/metrics", timeout=2.0)
            
        if response.status_code == 200:
            data = response.json()
            cpu = data.get("cpu_percent", 0.0)
            mem = data.get("memory_percent", 0.0)
            disk = data.get("disk_percent", 0.0)
            
            # 1. Affichage des blocs KPIs
            col1, col2, col3 = st.columns(3)
            col1.metric(label="Utilisation CPU", value=f"{cpu} %")
            col2.metric(label="Mémoire Vive", value=f"{mem} %")
            col3.metric(label="Espace Disque", value=f"{disk} %")
            
            # 2. Mise à jour de l'historique de données (fenêtre glissante)
            current_time = time.strftime("%H:%M:%S")
            new_row = pd.DataFrame([{"Temps": current_time, "CPU": cpu, "Mémoire": mem, "Disque": disk}])
            
            st.session_state.metrics_history = pd.concat([st.session_state.metrics_history, new_row], ignore_index=True)
            
            # Garder uniquement les 60 derniers points (fenêtre de 60 secondes si rafraîchi par sec)
            if len(st.session_state.metrics_history) > 60:
                st.session_state.metrics_history = st.session_state.metrics_history.tail(60)
                
            # 3. Graphique linéaire
            st.subheader("Évolution de la charge")
            chart_data = st.session_state.metrics_history.set_index("Temps")
            st.line_chart(chart_data)
            
        else:
            st.error(f"Impossible de récupérer les métriques. Code erreur : {response.status_code}")
    except Exception as e:
        st.error(f"Connexion au backend impossible ({API_BASE_URL}). Assurez-vous que l'API est lancée.")

# ---------------------------------------------------------
# ONGLET 2 : GESTION DES SERVEURS
# ---------------------------------------------------------
with tab_servers:
    st.subheader("Parc de serveurs sous supervision")
    
    # 1. Formulaire d'ajout d'un serveur
    with st.form("register_server_form", clear_on_submit=True):
        st.write("**Ajouter un nouveau serveur à la liste**")
        col_id, col_name = st.columns(2)
        server_id = col_id.text_input("ID unique (ex: srv-prod-01)")
        server_name = col_name.text_input("Nom du serveur (ex: Serveur Principal)")
        
        col_host, col_port = st.columns(2)
        server_host = col_host.text_input("Hôte / IP (ex: localhost, 10.0.0.5)")
        server_port = col_port.number_input("Port", min_value=1, max_value=65535, value=80)
        
        submit_btn = st.form_submit_button("💾 Enregistrer le serveur")
        
        if submit_btn:
            if not server_id or not server_name or not server_host:
                st.warning("Veuillez remplir tous les champs du formulaire.")
            else:
                payload = {"id": server_id, "name": server_name, "host": server_host, "port": int(server_port)}
                headers = {"X-API-Key": API_KEY}
                
                try:
                    with httpx.Client() as client:
                        res = client.post(f"{API_BASE_URL}/servers", json=payload, headers=headers, timeout=3.0)
                    if res.status_code == 201:
                        st.success(f"Le serveur '{server_name}' a été enregistré avec succès !")
                        st.rerun()
                    else:
                        st.error(f"Échec de l'ajout ({res.status_code}) : {res.json().get('detail')}")
                except Exception as e:
                    st.error(f"Erreur de communication : {str(e)}")

    st.write("---")
    
    # 2. Tableau d'affichage des serveurs enregistrés
    st.write("**Statut de la flotte**")
    try:
        with httpx.Client() as client:
            res_list = client.get(f"{API_BASE_URL}/servers", timeout=2.0)
            
        if res_list.status_code == 200:
            servers_data = res_list.json()
            
            if not servers_data:
                st.info("Aucun serveur n'est actuellement enregistré.")
            else:
                df = pd.DataFrame(servers_data)
                
                # Fonction pour colorer le tableau selon le statut (Exigence du barème)
                def color_status(val):
                    if val == "UP":
                        return "background-color: #d4edda; color: #155724; font-weight: bold;"
                    elif val == "DEGRADED":
                        return "background-color: #fff3cd; color: #856404; font-weight: bold;"
                    elif val == "DOWN":
                        return "background-color: #f8d7da; color: #721c24; font-weight: bold;"
                    return ""

                styled_df = df.style.map(color_status, subset=["status"])
                st.dataframe(styled_df, use_container_width=True)
                
                # 3. Actions rapides (Diagnostic manuel et suppression)
                st.write("**Actions rapides sur les serveurs**")
                for srv in servers_data:
                    col_info, col_check, col_del = st.columns([4, 1, 1])
                    col_info.write(f"🖥️ **{srv['name']}** ({srv['id']}) — `{srv['host']}:{srv['port']}` [**{srv['status']}**]")
                    
                    # Déclencher un check manuel
                    if col_check.button("🔍 Diagnostiquer", key=f"check_{srv['id']}"):
                        with httpx.Client() as client:
                            client.post(f"{API_BASE_URL}/servers/{srv['id']}/check")
                        st.rerun()
                        
                    # Supprimer le serveur
                    if col_del.button("🗑️ Supprimer", key=f"del_{srv['id']}"):
                        headers = {"X-API-Key": API_KEY}
                        with httpx.Client() as client:
                            client.delete(f"{API_BASE_URL}/servers/{srv['id']}", headers=headers)
                        st.success(f"Serveur {srv['id']} supprimé.")
                        st.rerun()
        else:
            st.error("Impossible de récupérer la liste des serveurs.")
    except Exception as e:
        st.error(f"Erreur de chargement des serveurs : {str(e)}")