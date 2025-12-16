import streamlit as st
import math
import uuid
import json
import copy
import pandas as pd
import os

# ==============================================================================
# --- MODULE GESTION DE PROJET (Intégré) ---
# ==============================================================================

def init_project_state():
    """Initialise l'état du projet s'il n'existe pas."""
    if 'project' not in st.session_state:
        st.session_state['project'] = {
            "name": "Nouveau Projet",
            "configs": [] # List of dicts: {id, ref, data}
        }
        # Create initial default config if empty
        if not st.session_state['project']['configs']:
            default_data = serialize_config() # Captures current (default) state
            add_config_to_project(default_data, "F1")

def serialize_config():
    """Capture l'état actuel de la configuration (Session State) dans un dictionnaire."""
    # Liste des clés à sauvegarder (tout ce qui définit la fenêtre)
    keys_to_save = [
        'ref_id', 'qte_val', 'mat_type', 'frame_thig', 
        'proj_type', 'pose_type', 'fin_val', 'same_bot', 'fin_bot',
        'is_appui_rap', 'width_appui', 'col_in', 'col_ex',
        'width_dorm', 'height_dorm', 'h_allege',
        'vr_enable', 'vr_h', 'vr_g', 'struct_mode', 'zone_tree'
    ]
    
    data = {}
    for k in keys_to_save:
        if k in st.session_state:
            # IMPORTANT: DEEP COPY to avoid reference sharing
            data[k] = copy.deepcopy(st.session_state[k])
            
    # Also capture ALL dynamic keys from the recursive UI
    # FIXED V73: Capture ALL keys except system keys. Previously only 'root*' was captured.
    system_keys = ['project', 'active_config_id', 'mgr_sel_id', 'uploader_json', 'FormSubmitter']
    
    for k in st.session_state:
        if k in system_keys or k.startswith('FormSubmit'):
            continue
            
        # EXCLUDE BUTTONS
        if isinstance(k, str):
             if k.endswith('_btn') or k.startswith('btn_'):
                 continue
            
        # Avoid duplicating static keys already added
        if k not in data:
            try:
                data[k] = copy.deepcopy(st.session_state[k])
            except:
                data[k] = st.session_state[k]
    
    return data

def deserialize_config(data):
    """Restaure une configuration depuis un dictionnaire vers le Session State."""
    # 1. Clear current state (or specific keys) to avoid ghosts
    # We don't use st.session_state.clear() because we want to keep 'project' and UI state
    # But for safety, we should clear dynamic keys
    # FIXED V73: Preserve 'mgr_sel_id' and 'active_config_id' to prevent loss of context
    # Also preserve 'uploader_json' to avoid re-triggering reload
    keys_keep = ['project', 'mgr_sel_id', 'active_config_id', 'uploader_json']
    keys_to_del = [k for k in st.session_state if k not in keys_keep]
    for k in keys_to_del:
        del st.session_state[k]
        
    # 2. Load new data
    for k, v in data.items():
        # Filter out buttons if they snuck in (Backwards compatibility)
        if isinstance(k, str) and (k.endswith('_btn') or k.startswith('btn_')):
            continue
            
        # FIXED V73: DEEP COPY on load to ensure UI edits don't mutate stored config in real-time.
        # This decouples the "Working Draft" (Session State) from the "Saved File" (Project Dict).
        try:
            st.session_state[k] = copy.deepcopy(v)
        except Exception:
            # Fallback for non-copyable objects (rare in checking, but safe)
            st.session_state[k] = v
        
def add_config_to_project(data, ref_name):
    """Ajoute une configuration au projet."""
    new_id = str(uuid.uuid4())
    st.session_state['project']['configs'].append({
        "id": new_id,
        "ref": ref_name,
        "data": copy.deepcopy(data) # Ensure stored data is independent
    })
    return new_id

def update_current_config_in_project(config_id, data, ref_name):
    """Met à jour une configuration existante dans le projet."""
    for cfg in st.session_state['project']['configs']:
        if cfg['id'] == config_id:
            cfg['data'] = copy.deepcopy(data) # Ensure stored data is independent
            cfg['ref'] = ref_name
            return True
    return False

def delete_config_from_project(config_id):
    """Supprime une configuration."""
    st.session_state['project']['configs'] = [
        c for c in st.session_state['project']['configs'] if c['id'] != config_id
    ]

def render_project_sidebar():
    """Affiche l'interface de gestion de projet dans la sidebar (Refonte V73)."""
    st.sidebar.markdown("### 📁 Projet")
    
    # 1. Nom du Projet
    proj_name = st.sidebar.text_input("Nom du Chantier", st.session_state['project']['name'])
    if proj_name != st.session_state['project']['name']:
        st.session_state['project']['name'] = proj_name
        
    configs = st.session_state['project']['configs']
    
    # Initialize active_id and active_ref safe default
    active_id = None
    active_ref = "Nouveau"
    
    # Selection State Logic
    if not configs:
        st.sidebar.warning("Aucune configuration.")
        options = {}
    else:
        # --- GESTION ÉTAT ACTIF (ACTIVE CONFIG ID) ---
        if 'active_config_id' not in st.session_state:
            # Try to find if current data matches a saved config? Difficile.
            # Assume None / Unsaved Mode initially or match first if identical?
            # Let's start with None (Mode "Sans Titre")
            st.session_state['active_config_id'] = None

        # Determine Active Ref Name
        active_id = st.session_state['active_config_id']
        active_ref = "Non enregistré"
        active_color = "red"
        
        if active_id:
            # Find ref
            found = next((c for c in configs if c['id'] == active_id), None)
            if found:
                active_ref = found['ref']
                active_color = "green"
            else:
                # ID deleted OR Mismatch?
                # DEBUG MODE: Do NOT reset automatically to see what happened
                # st.session_state['active_config_id'] = None 
                active_ref = f"ORPHELIN ({active_id})"
                active_color = "orange"

        st.sidebar.markdown(f"**Fichier Actif :** :{active_color}[{active_ref}]")
        # st.sidebar.caption(f"Debug: ActiveID={active_id}, Found={active_id and any(c['id'] == active_id for c in configs)}")

        # Create Options Map
        options = {c['id']: f"{c['ref']} (ID: {c['id'][:4]})" for c in configs}
        
        # Ensure ID is valid (optional but safe)
        if 'mgr_sel_id' not in st.session_state or st.session_state['mgr_sel_id'] not in options:
             st.session_state['mgr_sel_id'] = configs[0]['id']
    c_save, c_new = st.sidebar.columns(2)
    
    # SAUVEGARDER (Target: ACTIVE ID ONLY)
    # Check if active_id physically exists in the current list
    id_exists = False
    if active_id and configs:
        id_exists = any(c['id'] == active_id for c in configs)
    
    lbl_save = f"💾 Mettre à jour '{active_ref}'" if id_exists else "💾 Enreg. Nouveau"
    
    # Visual Warning if Selection != Active
    sel_id = st.session_state.get('mgr_sel_id')
    if active_id and sel_id and active_id != sel_id:
        st.sidebar.warning(f"⚠️ **Attention** : Vous éditez **{active_ref}**, mais **{options.get(sel_id, 'Inconnu')}** est sélectionné dans la liste.")
        st.sidebar.caption("Cliquez sur 'Ouvrir' pour changer de fichier.")
    
    if c_save.button(lbl_save, help=f"Enregistrer modifications sur '{active_ref}'", use_container_width=True):
        current_data = serialize_config()
        current_ref = st.session_state.get('ref_id', 'Sans Ref')
        
        if id_exists:
            # UPDATE EXISTING
            if update_current_config_in_project(active_id, current_data, current_ref):
                 st.toast(f"✅ Fichier '{current_ref}' mis à jour !")
            else:
                 st.error("Erreur critique: ID introuvable malgré vérification.")
        else:
            # CREATE NEW (Because ID doesn't exist or is None)
            cnt = len(configs) + 1
            if current_ref == 'Sans Ref': current_ref = f"Fenêtre {cnt}"
            new_id = add_config_to_project(current_data, current_ref)
            st.session_state['active_config_id'] = new_id
            st.toast(f"🆕 Nouveau fichier '{current_ref}' créé !")
            st.rerun() # Refresh to show green status
        
    # NOUVELLE CONFIGURATION
    if c_new.button("➕ Nouveau", help="Vider l'écran pour une nouvelle fenêtre", use_container_width=True):
        # We want to clear screen but NOT necessarily save immediately?
        # Or just "Clone current as new"? 
        # User expectation: "New" = Blank Canvas usually.
        # But here valid config is required.
        # Let's create a NEW entry based on Default/Current and make it active.
        current_data = serialize_config() # Copy current settings as base
        cnt = len(configs) + 1
        new_id = add_config_to_project(current_data, f"Fenêtre {cnt}")
        st.session_state['active_config_id'] = new_id
        st.toast(f"Nouvelle fenêtre {cnt} créée !")
        st.rerun()

    st.sidebar.markdown("---")
    
    # 3. LISTE & CHARGEMENT
    if configs:
        st.sidebar.caption("Ouvrir une autre configuration :")
        
        # BIND DIRECTLY TO mgr_sel_id for LIST selection
        sel_id = st.sidebar.selectbox(
            "Liste", 
            options.keys(), 
            format_func=lambda x: options[x], 
            key='mgr_sel_id', # SYNCED with list state
            label_visibility="collapsed"
        )
        
        c_load, c_del = st.sidebar.columns([2, 1])
        
        # CHARGER : SWITCH ACTIVE ID
        if c_load.button("📂 Ouvrir", use_container_width=True):
            target = next((c for c in configs if c['id'] == sel_id), None)
            if target:
                deserialize_config(target['data'])
                # SET ACTIVE ID
                st.session_state['active_config_id'] = target['id']
                # SYNC SELECTION (Redundant & Causes API Error)
                # st.session_state['mgr_sel_id'] = target['id'] 
                st.toast(f"Ouverture de '{target['ref']}'...")
                st.rerun()
                
        if c_del.button("🗑", help="Supprimer", use_container_width=True):
            delete_config_from_project(sel_id)
            # If we deleted the active one, reset active
            if st.session_state.get('active_config_id') == sel_id:
                st.session_state['active_config_id'] = None
            st.rerun()
            
    # 4. EXPORT / IMPORT (Discret en bas)
    with st.sidebar.expander("Import / Export JSON"):
        proj_data = json.dumps(st.session_state['project'], indent=2)
        
        # Dynamic Filename based on Project Name
        raw_name = st.session_state['project'].get('name', 'Projet_Fenetre')
        safe_name = "".join([c if c.isalnum() else "_" for c in raw_name])
        dl_name = f"{safe_name}.json"
        
        st.download_button("Export (JSON)", proj_data, file_name=dl_name, mime="application/json")
        
        # Manual Import Trigger (Safer)
        uploaded = st.file_uploader("Import JSON", type=['json'], key='uploader_json')
        if uploaded:
            if st.button("📥 Charger le Projet", help="Ecrase le projet actuel avec le fichier"):
                 try:
                    data = json.load(uploaded)
                    if 'configs' in data:
                        st.session_state['project'] = data
                        # Reset active ID to avoid conflicts
                        st.session_state['active_config_id'] = None
                        st.toast("Projet importé avec succès !")
                        st.rerun()
                 except Exception as e:
                    st.error(f"Erreur lors de l'import : {e}")

def generate_html_report(project_name, config_ref, svg_content, data_dict):
    """Génère un rapport HTML complet prêt à l'impression."""
    
    # Format Table HTML
    table_rows = ""
    for k, v in data_dict.items():
        table_rows += f"<tr><td style='font-weight:bold; width:40%; padding:5px; border-bottom:1px solid #ddd;'>{k}</td><td style='padding:5px; border-bottom:1px solid #ddd;'>{v}</td></tr>"

    # FIXED: Use standard string (not f-string) and .format() to avoid conflicts with CSS braces
    # We double the braces for CSS/JS {{ }} so .format() ignores them.
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Fiche Technique - {config_ref}</title>
        <style>
            body {{ font-family: sans-serif; margin: 40px; color: #333; }}
            h1 {{ color: #2c3e50; text-align: center; }}
            h2 {{ color: #3498db; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 30px; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .drawing {{ text-align: center; margin: 20px 0; border: 1px solid #eee; padding: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            .footer {{ margin-top: 50px; font-size: 12px; color: #777; text-align: center; border-top: 1px solid #eee; padding-top: 10px; }}
            
            @media print {{
                body {{ margin: 0; }}
                .no-print {{ display: none; }}
                .container {{ max-width: 100%; }}
                .page-break {{ page-break-before: always; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Fiche Technique Menuiserie</h1>
            <p style="text-align:center;"><strong>Projet :</strong> {project_name} | <strong>Réf :</strong> {config_ref}</p>
            
            <div class="drawing">
                {svg_content}
            </div>
            
            <h2>Caractéristiques Techniques</h2>
            <table>
                {table_rows}
            </table>
            
            <div class="footer">
                Généré par FenêtrePro V73 - {project_name}
            </div>
        </div>
        <script>
            // Auto print if desired, or let user click
            // window.print();
        </script>
    </body>
    </html>
    """
    return html_template.format(project_name=project_name, config_ref=config_ref, svg_content=svg_content, table_rows=table_rows)

# ==============================================================================

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="FenêtrePro V73 - Sidebar Large", layout="wide")

# --- CSS PERSONNALISÉ (AVEC SIDEBAR ÉLARGIE) ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    h1, h2, h3, h4 { color: #2c3e50; }
    .stApp { max-width: 100%; }
    
    /* FORCE LA LARGEUR DE LA SIDEBAR */
    section[data-testid="stSidebar"] {
        width: 35% !important; /* Environ 1/3 de l'écran */
        min-width: 450px !important; /* Largeur minimum confortable */
    }
    
    div.row-widget.stRadio > div { flex-direction: row; }
    .metric-box {
        background-color: #e8f4f8;
        border-left: 5px solid #3498db;
        padding: 10px;
        margin: 10px 0;
        border-radius: 4px;
        font-weight: bold;
        color: #2c3e50;
    }
    .streamlit-expanderHeader {
        font-weight: bold;
        color: #2c3e50;
    }
    .centered-header {
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. FONCTIONS D'AIDE POUR L'ARBRE (TOP LEVEL) ---

# INIT PROJECT STATE (V73)
init_project_state()

def init_node(node_id, node_type="leaf", split_type=None, split_value=None, children=None, zone_params=None):
    """Initialise un noeud pour l'arbre de configuration."""
    if zone_params is None:
        zone_params = {
            'type': "Fixe",
            'params': {
                'traverses': 0,
                'remplissage_global': "Vitrage",
                'vitrage_ext': "4mm",
                'vitrage_int': "4mm",
                'pos_grille': "Aucune"
            }
        }
    return {
        'id': node_id,
        'type': node_type, # 'leaf' or 'split'
        'split_type': split_type, # 'horizontal' or 'vertical'
        'split_value': split_value, # percentage or absolute value
        'children': children if children is not None else [],
        'zone_params': zone_params # Only for leaf nodes
    }

def flatten_tree(node, current_x, current_y, current_w, current_h):
    """Convertit l'arbre de noeuds en une liste de zones plates avec leurs coordonnées."""
    flat_zones = []
    if node['type'] == 'leaf':
        # Ensure 'params' key exists in zone_params
        if 'params' not in node['zone_params']:
            node['zone_params']['params'] = {}
            
        z = {
            'id': node['id'],
            'type': node['zone_params']['type'],
            'params': node['zone_params']['params'],
            'x': current_x,
            'y': current_y,
            'w': current_w,
            'h': current_h
        }
        # V73 FIX: Propagate Zone Label for Schema
        if 'label' in node:
            z['label'] = node['label']
            
        flat_zones.append(z)
    elif node['type'] == 'split':
        # Check substrings because radio value contains extra text
        if "Horizontale" in node['split_type']:
            # Split value is height of the top/left child
            h1 = node['split_value']
            h2 = current_h - h1
            flat_zones.extend(flatten_tree(node['children'][0], current_x, current_y, current_w, h1))
            flat_zones.extend(flatten_tree(node['children'][1], current_x, current_y + h1, current_w, h2))
        else: # Verticale
            # Split value is width of the top/left child
            w1 = node['split_value']
            w2 = current_w - w1
            flat_zones.extend(flatten_tree(node['children'][0], current_x, current_y, w1, current_h))
            flat_zones.extend(flatten_tree(node['children'][1], current_x + w1, current_y, w2, current_h))
    return flat_zones

# --- HELPERS UI ---
TYPES_OUVRANTS = ["Fixe", "1 Vantail", "2 Vantaux", "Coulissant", "Soufflet"]
VITRAGES_INT = ["4mm", "33.2 (Sécurité)", "44.2 (Effraction)", "44.2 Silence"]
VITRAGES_EXT = ["4mm", "6mm", "SP10 (Anti-effraction)", "Granité"]

def config_zone_ui(label, key_prefix, current_node_type="Fixe"):
    # REMOVED EXPANDER to avoid nesting issues
    st.markdown(f"#### {label}")
    
    t, p = "Fixe", {}
    
    # 1. Type d'ouvrant
    col_type, col_princ = st.columns([2, 2])
    
    # Calc index from current_node_type
    try:
        idx_t = TYPES_OUVRANTS.index(current_node_type)
    except ValueError:
        idx_t = 0
        
    t = col_type.selectbox("Type", TYPES_OUVRANTS, index=idx_t, key=f"{key_prefix}_t")
        
    if "Vantail" in t and "2" not in t and "Coulissant" not in t:
        p['sens'] = col_princ.selectbox("Sens", ["TG", "TD"], key=f"{key_prefix}_s")
            
    if "2 Vantaux" in t:
        p['principal'] = col_princ.radio("Principal", ["G", "D"], horizontal=True, index=1, key=f"{key_prefix}_p")
    elif "Coulissant" in t:
        c_opt1, c_opt2 = st.columns(2)
        p['principal'] = c_opt1.radio("Sens (Principal)", ["G", "D"], index=1, horizontal=True, key=f"{key_prefix}_sens")
        # V73: Explicit Grille Position options for Sliding
        p['pos_grille'] = c_opt2.selectbox("Grille Aération", ["Aucune", "Vtl Gauche", "Vtl Droit"], key=f"{key_prefix}_grille")
        
    if "Oscillo" in t or "Vantail" in t or "Vantaux" in t or "Soufflet" in t:
            p['ob'] = st.checkbox("OB", False, key=f"{key_prefix}_o")
            
    # CONFIGURATION HAUTEUR POIGNÉE (HP)
    if t != "Fixe" and t != "Soufflet":
        current_allege = st.session_state.get('h_allege', 900)
        # Standard 1400 from floor (User Request)
        def_hp = max(0, 1400 - current_allege)
        if def_hp == 0: def_hp = 500 # Fallback reasonnable si allège très haute 
        
        p['h_poignee'] = st.number_input("Hauteur Poignée (mm)", 0, 2500, def_hp, step=10, key=f"{key_prefix}_hp")
    elif t == "Soufflet":
        st.info("Poignée : Centrée en traverse haute (Fixe)")
    
    with st.expander(f"⚙️ Finitions {label}"):
        p['traverses'] = st.number_input("Traverses Horiz.", 0, 5, 0, key=f"{key_prefix}_trav")
        if p['traverses'] == 1:
            p['pos_traverse'] = st.radio("Position", ["Centrée", "Sur mesure (du bas)"], horizontal=True, key=f"{key_prefix}_pos_t")
            if p['pos_traverse'] == "Sur mesure (du bas)":
                p['h_traverse_custom'] = st.number_input("Cote axe depuis bas (mm)", 100, 2000, 800, 10, key=f"{key_prefix}_h_t")
            cr1, cr2 = st.columns(2)
            p['remp_haut'] = cr1.radio("Remplissage HAUT", ["Vitrage", "Panneau"], key=f"{key_prefix}_rh")
            p['remp_bas'] = cr2.radio("Remplissage BAS", ["Panneau", "Vitrage"], key=f"{key_prefix}_rb")
        else:
            p['remplissage_global'] = st.radio("Remplissage Global", ["Vitrage", "Panneau"], horizontal=True, key=f"{key_prefix}_rg")
        
        st.markdown("🔍 **Composition Vitrage**")
        cv1, cv2 = st.columns(2)
        p['vitrage_ext'] = cv1.selectbox("Face Ext.", VITRAGES_EXT, key=f"{key_prefix}_ve")
        p['vitrage_int'] = cv2.selectbox("Face Int.", VITRAGES_INT, key=f"{key_prefix}_vi")

        st.markdown("💨 **Ventilation**")
        opts_grille = ["Aucune", "Vtl Principal"]
        if "2 Vantaux" in t: opts_grille.append("Vtl Secondaire")
        # For Coulissant, options are handled above in the main section
        if "Coulissant" not in t:
            p['pos_grille'] = st.selectbox("Position Grille", opts_grille, key=f"{key_prefix}_pg")
        
    return t, p

def render_node_ui(node, w_ref, h_ref, level=0, counter=None):
    """Rend l'interface utilisateur pour un noeud de l'arbre de configuration."""
    if counter is None: counter = {'zone': 1} # Mutable counter
    
    prefix = f"{node['id']}_lvl{level}"
    
    # Simplified Logic: Only show Title for LEAF zones (Actual Glazing)
    # Split Containers just show controls
    
    if node['type'] == 'leaf':
        zone_label = f"Zone {counter['zone']}"
        node['label'] = zone_label # Store for SVG
        counter['zone'] += 1
        
        # Use Expander for cleaner UI
        with st.expander(f"🔹 {zone_label} ({int(w_ref)}x{int(h_ref)})", expanded=True):
            # Pass current type to ensure UI sync
            current_t = node['zone_params'].get('type', 'Fixe')
            t, p = config_zone_ui(f"Config.", prefix, current_node_type=current_t)
            node['zone_params']['type'] = t
            node['zone_params']['params'] = p

            st.markdown("---")
            col_split, col_misc = st.columns([1, 2])
            if col_split.button(f"✂️ Diviser cette Zone", key=f"{prefix}_split_btn", help="Couper cette zone en deux"):
                node['type'] = 'split'
                node['split_type'] = 'vertical' 
                node['split_value'] = w_ref / 2 
                node['children'] = [
                    init_node(f"{node['id']}_child_0"),
                    init_node(f"{node['id']}_child_1")
                ]
                st.rerun()

    elif node['type'] == 'split':
        # Split Container UI - NESTED inside Expander
        with st.expander(f"➗ Division ({int(w_ref)}x{int(h_ref)})", expanded=True):
            col_type, col_value, col_unsplit = st.columns([1, 1, 1])
            
            # Robust check for initial 'vertical' or selected 'Verticale (|)'
            current_split = node.get('split_type', 'vertical')
            is_vert = 'Verticale' in current_split or current_split == 'vertical'
            
            node['split_type'] = col_type.radio(
                f"Sens",
                ["Verticale (|)", "Horizontale (-)"],
                index=0 if is_vert else 1,
                horizontal=True,
                key=f"{prefix}_split_type",
                label_visibility="collapsed"
            )
            
            if "Verticale" in node['split_type']:
                max_val = int(w_ref)
                label = "Largeur Zone Gauche"
            else: # horizontal
                max_val = int(h_ref)
                label = "Hauteur Zone Haute"
    
            # FIXED: Clamp value to avoid StreamlitValueAboveMaxError
            safe_current_val = int(node['split_value']) if node['split_value'] else int(max_val/2)
            min_allow = 10
            max_allow = max(max_val - 10, min_allow + 10)
            
            if safe_current_val < min_allow: safe_current_val = min_allow
            if safe_current_val > max_allow: safe_current_val = max_allow
            
            if safe_current_val != int(node['split_value']):
                 node['split_value'] = safe_current_val
    
            node['split_value'] = col_value.number_input(
                label,
                min_allow, max_allow, safe_current_val, step=10,
                key=f"{prefix}_split_value"
            )
            
            if col_unsplit.button(f"↩️ Annuler Division", key=f"{prefix}_unsplit_btn"):
                node['type'] = 'leaf'
                node['split_type'] = None
                node['split_value'] = None
                node['children'] = []
                node['zone_params'] = init_node('temp')['zone_params']
                st.rerun()
    
            # Recursively render children INSIDE this expander box
            if "Verticale" in node['split_type']:
                render_node_ui(node['children'][0], node['split_value'], h_ref, level + 1, counter)
                render_node_ui(node['children'][1], w_ref - node['split_value'], h_ref, level + 1, counter)
            else: # horizontal
                render_node_ui(node['children'][0], w_ref, node['split_value'], level + 1, counter)
                render_node_ui(node['children'][1], w_ref, h_ref - node['split_value'], level + 1, counter)
def reset_config():
    # FIXED V73: Do NOT clear everything (keeps Project, Session, Selection)
    # Only clear config-related keys
    keys_keep = ['project', 'active_config_id', 'mgr_sel_id', 'uploader_json']
    keys_to_del = [k for k in st.session_state if k not in keys_keep]
    for k in keys_to_del:
        del st.session_state[k]
    
    # Identification
    st.session_state['ref_id'] = "F1"
    st.session_state['qte_val'] = 1
    
    # Matériau & Pose
    st.session_state['mat_type'] = "PVC"
    st.session_state['frame_thig'] = 70
    st.session_state['proj_type'] = "Rénovation"
    st.session_state['pose_type'] = "Pose en rénovation (R)" # Default for Reno
    
    # Ailettes / Seuil
    # PVC defaults: indices match logic in UI (60 for side, 0 for bottom)
    # We let the widgets pick defaults based on index, but clearing SS works for 'index'.
    # However, forcing keys is safer.
    # Note: selectbox stores the VALUE string, not index.
    st.session_state['fin_val'] = 60 # Standard PVC 60
    st.session_state['same_bot'] = False
    st.session_state['fin_bot'] = 0
    
    # Partie Basse
    st.session_state['is_appui_rap'] = False
    st.session_state['width_appui'] = 100
    
    # Couleurs
    st.session_state['col_in'] = "Blanc (9016)"
    st.session_state['col_ex'] = "Blanc (9016)"
    
    # Dimensions
    st.session_state['width_dorm'] = 1200
    st.session_state['height_dorm'] = 1400
    st.session_state['h_allege'] = 900
    
    # Options
    st.session_state['vr_enable'] = False
    st.session_state['vr_h'] = 185
    st.session_state['vr_g'] = False
    
    # Structure (Arbre)
    st.session_state['struct_mode'] = "Simple (1 Zone)" 
    st.session_state['zone_tree'] = init_node('root') # Reset to single Fixe
    
    # FORCE RESET ROOT WIDGET (Fix persistence bug)
    st.session_state['root_lvl0_t'] = "Fixe"
    
    st.rerun()



def draw_rect(svg, x, y, w, h, fill, stroke="black", sw=1, z_index=1):
    svg.append((z_index, f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" />'))

def draw_text(svg, x, y, text, font_size=12, fill="black", weight="normal", anchor="middle", z_index=10, rotation=0):
    transform = f'transform="rotate({rotation}, {x}, {y})"' if rotation != 0 else ""
    svg.append((z_index, f'<text x="{x}" y="{y}" font-family="Arial" font-size="{font_size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}" dominant-baseline="middle" {transform}>{text}</text>'))

def draw_dimension_line(svg_content, x1, y1, x2, y2, value, text_prefix="", offset=50, orientation="H", font_size=24, z_index=8, leader_fixed_start=None):
    tick_size = 10
    display_text = f"{text_prefix}{int(value)}"
    
    if orientation == "H":
        y_line = y1 + offset 
        draw_rect(svg_content, x1, y_line, x2-x1, 2, "black", "black", 0, z_index)
        
        # Lignes de rappel
        start_y1 = leader_fixed_start if leader_fixed_start is not None else y1
        start_y2 = leader_fixed_start if leader_fixed_start is not None else y2
        
        svg_content.append((z_index, f'<line x1="{x1}" y1="{start_y1}" x2="{x1}" y2="{y_line + tick_size}" stroke="black" stroke-width="1" stroke-dasharray="4,4" />'))
        svg_content.append((z_index, f'<line x1="{x2}" y1="{start_y2}" x2="{x2}" y2="{y_line + tick_size}" stroke="black" stroke-width="1" stroke-dasharray="4,4" />'))
        draw_text(svg_content, (x1 + x2) / 2, y_line - 15, display_text, font_size=font_size, weight="bold", z_index=z_index)
    elif orientation == "V":
        x_line = x1 - offset
        draw_rect(svg_content, x_line, y1, 2, y2-y1, "black", "black", 0, z_index)
        
        start_x1 = leader_fixed_start if leader_fixed_start is not None else x1
        start_x2 = leader_fixed_start if leader_fixed_start is not None else x2

        svg_content.append((z_index, f'<line x1="{start_x1}" y1="{y1}" x2="{x_line - tick_size}" y2="{y1}" stroke="black" stroke-width="1" stroke-dasharray="4,4" />'))
        svg_content.append((z_index, f'<line x1="{start_x2}" y1="{y2}" x2="{x_line - tick_size}" y2="{y2}" stroke="black" stroke-width="1" stroke-dasharray="4,4" />'))
        
        txt_x = x_line - 15
        txt_y = (y1 + y2) / 2
        draw_text(svg_content, txt_x, txt_y, display_text, font_size=font_size, fill="black", weight="bold", anchor="middle", z_index=z_index, rotation=-90)

# --- FONCTION DESSIN CONTENU ZONE ---
def draw_handle_icon(svg, x, y, z_index=20, rotation=0):
    # Modern Handle Design (Scaled Up 2.0x for Visibility)
    # Rotation support for horizontally aligned handles (like Soufflet)
    transform = f'transform="rotate({rotation}, {x}, {y})"' if rotation != 0 else ""
    
    # 1. Base Plate (Rosace)
    # Size: w=20 h=60
    svg.append((z_index, f'<rect x="{x-10}" y="{y-30}" width="20" height="60" rx="4" fill="#e0e0e0" stroke="#999" stroke-width="0.5" {transform} />'))
    # 2. Lever - More distinct info
    # Length: 70px
    path_d = f"M{x-4},{y} L{x-4},{y+65} Q{x-4},{y+75} {x+6},{y+75} L{x+6},{y+75} L{x+6},{y+10} Z"
    svg.append((z_index+1, f'<path d="{path_d}" fill="#ccc" stroke="#666" stroke-width="1" {transform} />'))
    # 3. Pivot Point
    svg.append((z_index+2, f'<circle cx="{x}" cy="{y}" r="6" fill="#666" {transform} />'))

def draw_sash_content(svg, x, y, w, h, type_ouv, params, config_global, z_base=10):
    c_frame = config_global['color_frame']
    vis_ouvrant = 55 
    
    # Helper interne pour dessiner un "bloc vitré/panneau"
    def draw_leaf_interior(lx, ly, lw, lh, z_start=None):
        nb_trav = params.get('traverses', 0)
        z_eff = z_start if z_start is not None else z_base
        
        if nb_trav == 1:
            pos_trav = params.get('pos_traverse', 'Centrée')
            h_custom = params.get('h_traverse_custom', 800)
            ep_trav = 20
            
            if pos_trav == "Sur mesure (du bas)":
                y_center = (ly + lh) - h_custom
            else:
                y_center = ly + lh / 2
            
            y_trav_start = y_center - (ep_trav / 2)
            y_trav_end = y_center + (ep_trav / 2)
            
            # Bas
            h_rect_bas = (ly + lh) - y_trav_end
            if h_rect_bas > 0:
                col_b = "#F0F0F0" if params.get('remp_bas') == "Panneau" else config_global['color_glass']
                draw_rect(svg, lx, y_trav_end, lw, h_rect_bas, col_b, "black", 1, z_eff+1)
            # Haut
            h_rect_haut = y_trav_start - ly
            if h_rect_haut > 0:
                col_h = "#F0F0F0" if params.get('remp_haut') == "Panneau" else config_global['color_glass']
                draw_rect(svg, lx, ly, lw, h_rect_haut, col_h, "black", 1, z_eff+1)
            
            draw_rect(svg, lx, y_trav_start, lw, ep_trav, c_frame, "black", 1, z_eff+2)
            
        else:
            remp_glob = params.get('remplissage_global', 'Vitrage')
            # DEBUG removed
            col_g = "#F0F0F0" if remp_glob == "Panneau" else config_global['color_glass']
            # z_eff = 50
            draw_rect(svg, lx, ly, lw, lh, col_g, "black", 1, z_eff+1)
            
            if nb_trav > 1:
                section_h = lh / (nb_trav + 1)
                for k in range(1, nb_trav + 1):
                    ty = ly + (section_h * k) - 10 
                    draw_rect(svg, lx, ty, lw, 20, c_frame, "black", 1, z_eff+2)

    # --- TYPES OUVRANTS ---
    if type_ouv == "Fixe":
        vis_fixe = 42 # Épaississement du dormant visible pour le Fixe (~65mm total)
        # draw_rect(svg, x, y, w, h, c_frame, "black", 1, z_base) <- Removed to avoid double border
        draw_leaf_interior(x+vis_fixe, y+vis_fixe, w-2*vis_fixe, h-2*vis_fixe)
        draw_text(svg, x+w/2, y+h/2, "F", font_size=40, fill="#335c85", weight="bold", z_index=z_base+5)
        
    elif type_ouv in ["1 Vantail", "Oscillo-Battant"]:
        adj = 24 # Visuel dormant (Increased V73)
        draw_rect(svg, x+adj, y+adj, w-2*adj, h-2*adj, c_frame, "black", 1, z_base)
        draw_leaf_interior(x+vis_ouvrant, y+vis_ouvrant, w-2*vis_ouvrant, h-2*vis_ouvrant)
        
        # LABEL VP (Vantail Principal)
        draw_text(svg, x+w/2, y+h/2, "VP", font_size=40, fill="#335c85", weight="bold", z_index=z_base+7)
        
        sens = params.get('sens', 'TG')
        mid_y = y + h/2
        if sens == 'TD': p = f"{x+w},{y} {x},{mid_y} {x+w},{y+h}"
        else: p = f"{x},{y} {x+w},{mid_y} {x},{y+h}"
        svg.append((z_base+6, f'<polygon points="{p}" fill="none" stroke="black" stroke-width="1" />'))
        
        # DESSIN POIGNÉE
        hp_val = params.get('h_poignee', 0)
        # remove allege substraction, hp_val is already relative from bottom
        y_h_vis = max(y + 50, min(y + h - 50, y + h - hp_val))
        
        # Position X dependent on hinges (Sens)
        # Handle axis approx 28mm (Center of 55mm sash)
        vis_axis_offset = 28 
        
        if sens == 'TG': x_h_vis = x + w - vis_axis_offset
        else: x_h_vis = x + vis_axis_offset
            
        if hp_val > 0:
            draw_handle_icon(svg, x_h_vis, y_h_vis, z_index=z_base+8)
        
        if params.get('ob', False):
            p_ob = f"{x},{y+h} {x+w},{y+h} {x+w/2},{y}"
            svg.append((z_base+6, f'<polygon points="{p_ob}" fill="none" stroke="black" stroke-width="1" />'))
            draw_text(svg, x+w/2, y+h-30, "OB", font_size=20, fill="black", weight="bold", z_index=z_base+7)

    elif type_ouv == "2 Vantaux":
        w_vtl = w / 2
        # V73: Inset sash to show dormant frame "Liseret"
        adj = 24
        
        # Left Sash
        draw_rect(svg, x+adj, y+adj, w_vtl-adj, h-2*adj, c_frame, "black", 1, z_base) 
        # Right Sash
        draw_rect(svg, x+w_vtl, y+adj, w_vtl-adj, h-2*adj, c_frame, "black", 1, z_base) 
        
        # Intérieurs
        draw_leaf_interior(x+vis_ouvrant, y+vis_ouvrant, w_vtl-2*vis_ouvrant, h-2*vis_ouvrant)
        draw_leaf_interior(x+w_vtl+vis_ouvrant, y+vis_ouvrant, w_vtl-2*vis_ouvrant, h-2*vis_ouvrant)
        
        svg.append((z_base+6, f'<line x1="{x+w_vtl}" y1="{y}" x2="{x+w_vtl}" y2="{y+h}" stroke="black" stroke-width="1" />'))
        
        # Symboles
        p_g = f"{x},{y} {x+w_vtl},{y+h/2} {x},{y+h}"
        p_d = f"{x+w},{y} {x+w_vtl},{y+h/2} {x+w},{y+h}"
        svg.append((z_base+6, f'<polygon points="{p_g}" fill="none" stroke="black" stroke-width="1" />'))
        svg.append((z_base+6, f'<polygon points="{p_d}" fill="none" stroke="black" stroke-width="1" />'))
        
        is_princ_right = (params.get('principal', 'D') == 'D')
        
        # DESSIN POIGNÉE (Sur Vantail Principal)
        hp_val = params.get('h_poignee', 0)
        y_h_vis = max(y + 50, min(y + h - 50, y + h - hp_val))
        
        if is_princ_right:
            # Principal Droite -> Poignée à Gauche du vantail droit (Central)
            x_h_vis = (x + w_vtl) + 28
        else:
            # Principal Gauche -> Poignée à Droite du vantail gauche (Central)
            x_h_vis = (x + w_vtl) - 28
            
        if hp_val > 0:
            draw_handle_icon(svg, x_h_vis, y_h_vis, z_index=z_base+8)
            
            # HANDLE ON SECONDARY SASH (VS) - Symmetric
            # If VP is Right (handle on Left of VP), VS is Left (handle on Right of VS).
            # If VP is Left (handle on Right of VP), VS is Right (handle on Left of VS).
            
            # Simply put: 2 Vantaux always meet in the center.
            # Handle on Left Sash is on its Right Stile.
            # Handle on Right Sash is on its Left Stile.
            
            # Let's calculate VS position
            if is_princ_right:
                # VS is Left Sash. Handle on Right side of VS.
                x_h_vs = (x + w_vtl) - 28
                # Same Y
                draw_handle_icon(svg, x_h_vs, y_h_vis, z_index=z_base+8)
            else:
                # VS is Right Sash. Handle on Left side of VS.
                x_h_vs = (x + w_vtl) + 28
                draw_handle_icon(svg, x_h_vs, y_h_vis, z_index=z_base+8)

        # Labels VP / VS
        txt_g = "VS" if is_princ_right else "VP"
        txt_d = "VP" if is_princ_right else "VS"
        
        draw_text(svg, x+w_vtl/2, y+h/2, txt_g, font_size=30, fill="#335c85", weight="bold", z_index=z_base+7)
        draw_text(svg, x+w_vtl+w_vtl/2, y+h/2, txt_d, font_size=30, fill="#335c85", weight="bold", z_index=z_base+7)

        if params.get('ob', False):
            ox, oy, ow, oh = (x+w_vtl, y, w_vtl, h) if is_princ_right else (x, y, w_vtl, h)
            p_ob = f"{ox},{oy+oh} {ox+ow},{oy+oh} {ox+ow/2},{oy}"
            svg.append((z_base+6, f'<polygon points="{p_ob}" fill="none" stroke="black" stroke-width="1" />'))
            draw_text(svg, ox+ow/2, oy+oh-30, "OB", font_size=20, fill="black", weight="bold", z_index=z_base+8)

    elif type_ouv == "Soufflet":
        adj = 24
        draw_rect(svg, x+adj, y+adj, w-2*adj, h-2*adj, c_frame, "black", 1, z_base)
        draw_leaf_interior(x+vis_ouvrant, y+vis_ouvrant, w-2*vis_ouvrant, h-2*vis_ouvrant)
        draw_text(svg, x+w/2, y+h/2, "S", font_size=40, fill="#335c85", weight="bold", z_index=z_base+5)
        
        p_ob = f"{x},{y+h} {x+w},{y+h} {x+w/2},{y}"
        svg.append((z_base+6, f'<polygon points="{p_ob}" fill="none" stroke="black" stroke-width="1" />'))
        draw_text(svg, x+w/2, y+h-30, "OB", font_size=20, fill="black", weight="bold", z_index=z_base+7)
        
        # HANDLE FOR SOUFFLET: Top Center
        # Profile width ~70mm. Handle centered on top rail. Frame width 55mm?
        # Top sash rail is at y. Handle axis y + 28.
        h_soufflet_x = x + w/2
        h_soufflet_y = y + 28 # Top rail center
        # Scale handle down slightly? Or rotate?
        # Soufflet handles are often horizontal. Let's rotate -90 or 90.
        # For simplicity, vertical is fine, inverted?
        # User said "Traverse Haute". 
        # V73 Correctif: User wants Horizontal, Tail to the Right.
        # Default is Down. Rotate -90 makes it point Right? 
        # SVG Rotation: + clockwise. Down (0,1) -> -90 -> Right (1,0)? No wait.
        # (0,1) -> rot(-90) -> (1,0). Yes.
        draw_handle_icon(svg, h_soufflet_x, h_soufflet_y, z_index=z_base+8, rotation=-90)
         
    elif type_ouv == "Coulissant":
        # Dimensions standard
        w_vtl = w/2 + 25
        
        # Logique Principal / Secondaire (Principal = Devant)
        is_princ_right = (params.get('principal', 'D') == 'D')
        
        # Définition des Vantaux
        # Vantail Gauche (x, y)
        def draw_vtl_left(z_idx):
            adj = 24
            draw_rect(svg, x+adj, y+adj, w_vtl-adj, h-2*adj, c_frame, "black", 1, z_idx)
            draw_leaf_interior(x+vis_ouvrant, y+vis_ouvrant, w_vtl-2*vis_ouvrant, h-2*vis_ouvrant, z_start=z_idx)
            
        # Vantail Droit (x+w/2-25, y)
        def draw_vtl_right(z_idx):
            adj = 24
            draw_rect(svg, x+w/2-25, y+adj, w_vtl-adj, h-2*adj, c_frame, "black", 1, z_idx)
            draw_leaf_interior(x+w/2-25+vis_ouvrant, y+vis_ouvrant, w_vtl-2*vis_ouvrant, h-2*vis_ouvrant, z_start=z_idx)

        # Ordre de Dessin : VS (Derrière) puis VP (Devant)
        if is_princ_right:
            # Droite est Principal -> Devant.
            # Donc on dessine Gauche (VS) en premier (z_base), puis Droite (VP) au dessus (z_base+2)
            draw_vtl_left(z_base)
            draw_vtl_right(z_base+2)
        else:
            # Gauche est Principal -> Devant.
            # Dessin Droite (VS) en premier, puis Gauche (VP)
            draw_vtl_right(z_base)
            draw_vtl_left(z_base+2)
        
        # Textes & Flèches
        ay = y + h/2
        text_y = ay - 10 # Remonte un peu le texte
        arrow_y = ay + 40 # Descend les flèches
        
        txt_g = "VS" if is_princ_right else "VP"
        txt_d = "VP" if is_princ_right else "VS"
        
        # Z-Index Textes : au dessus des deux (z_base+10)
        draw_text(svg, x+w_vtl/2, text_y, txt_g, font_size=30, fill="#335c85", weight="bold", z_index=z_base+10)
        draw_text(svg, x+w/2-25+w_vtl/2, text_y, txt_d, font_size=30, fill="#335c85", weight="bold", z_index=z_base+10)

        # Flèches de refoulement (Indiquent l'ouverture)
        # Vantail Gauche s'ouvre vers la Droite (->)
        # Vantail Droit s'ouvre vers la Gauche (<-)
        # On les dessine en dessous du texte.
        
        # Flèche Gauche (->)
        x1_g = x + vis_ouvrant + 30
        x2_g = x + w_vtl - vis_ouvrant - 30
        
        # Line
        svg.append((z_base+10, f'<line x1="{x1_g}" y1="{arrow_y}" x2="{x2_g}" y2="{arrow_y}" stroke="#335c85" stroke-width="3" />'))
        
        # Manual Arrow Head (Right)
        # Tip at x2_g, arrow_y
        p_arrow_g = f"{x2_g},{arrow_y} {x2_g-30},{arrow_y-10} {x2_g-30},{arrow_y+10}"
        svg.append((z_base+10, f'<polygon points="{p_arrow_g}" fill="#335c85" />'))
        
        # Flèche Droite (<-)
        x1_d = x + w - vis_ouvrant - 30
        x2_d = x + w/2 - 25 + vis_ouvrant + 30
        
        # Line
        svg.append((z_base+10, f'<line x1="{x1_d}" y1="{arrow_y}" x2="{x2_d}" y2="{arrow_y}" stroke="#335c85" stroke-width="3" />'))
        
        # Manual Arrow Head (Left)
        # Tip at x2_d, arrow_y
        p_arrow_d = f"{x2_d},{arrow_y} {x2_d+30},{arrow_y-10} {x2_d+30},{arrow_y+10}"
        svg.append((z_base+10, f'<polygon points="{p_arrow_d}" fill="#335c85" />'))
        
        # HANDLES FOR COULISSANT
        # Centered vertically (roughly) or at HP.
        # Handle on Stile (Montant). 
        # Left Sash: Right Stile. Right Sash: Left Stile.
        
        y_handle_c = y + h/2
        if params.get('h_poignee', 0) > 0:
            # If custom HP provided, use it relative to Sash Bottom
             current_allege = st.session_state.get('h_allege', 900)
             # Basic calc: y + h - (hp - allege)
             # But let's stick to center for sliding if not specified, 
             # or use the same logic if hp is available.
             hp_val = params.get('h_poignee', 0)
             y_handle_c = max(y + 50, min(y + h - 50, y + h - hp_val))

        # Handle Left Sash (on its Left Stile - Jamb Side)
        # Sash starts at x. Frame visible ~55. Center 28.
        # User wants "extremity". Left sash -> Left side.
        x_h_c_left = x + 28
        draw_handle_icon(svg, x_h_c_left, y_handle_c, z_index=z_base+12)
        
        # Handle Right Sash (on its Right Stile - Jamb Side)
        # Sash ends at x+w.
        x_h_c_right = (x + w) - 28
        draw_handle_icon(svg, x_h_c_right, y_handle_c, z_index=z_base+12)

    # GRILLE D'AÉRATION - V73 FIX
    pos_grille = params.get('pos_grille', 'Aucune')
    if pos_grille != "Aucune":
        gx, gy = 0, 0
        
        # FIXED: Center logic
        if type_ouv == "Fixe":
             # Center X on the zone
             gx = x + (w - 250)/2
             # Top alignment (in frame 42mm -> center at 15)
             gy = y + 15
             
        elif type_ouv == "Coulissant":
             # V73: Respect Left/Right selection
             # w_vtl = w/2 + 25
             # If Left (VS or VP): center on left half
             # If Right (VS or VP): center on right half
             
             # Determine target leaf from selection
             target_is_right = False
             
             # Logic: "Vtl Principal" or "Vtl Secondaire" depends on 'principal' param
             is_princ_right = (params.get('principal', 'D') == 'D')
             
             if pos_grille == "Vtl Principal":
                 target_is_right = is_princ_right
             elif pos_grille == "Vtl Secondaire":
                 target_is_right = not is_princ_right
             elif pos_grille == "Vtl Gauche": # Explicit new option
                 target_is_right = False
             elif pos_grille == "Vtl Droit": # Explicit new option
                 target_is_right = True
            
             if target_is_right:
                 # Center on Right Sash
                 # Right sash starts at x + w/2 - 25
                 # Width approx w/2 + 25.
                 # Center = Start + (Width - 250)/2
                 sash_x = x + w/2 - 25
                 sash_w = w/2 + 25
                 gx = sash_x + (sash_w - 250)/2
             else:
                 # Center on Left Sash
                 # Sash starts at x
                 sash_w = w/2 + 25
                 gx = x + (sash_w - 250)/2

             gy = y + (vis_ouvrant - 12) / 2

        elif type_ouv == "2 Vantaux":
            is_princ_right = (params.get('principal', 'D') == 'D')
            if pos_grille == "Vtl Principal":
                if is_princ_right: gx = x + w/2 + (w/2 - 250)/2
                else: gx = x + (w/2 - 250)/2
            elif pos_grille == "Vtl Secondaire":
                if is_princ_right: gx = x + (w/2 - 250)/2
                else: gx = x + w/2 + (w/2 - 250)/2
            else: gx = x + (w/2 - 250)/2
            gy = y + (vis_ouvrant - 12) / 2
        
        else: # 1 Vantail, Soufflet...
            gx = x + (w - 250)/2
            gy = y + (vis_ouvrant - 12) / 2

        draw_rect(svg, gx, gy, 250, 12, "#eeeeee", "black", 1, z_base+8)
        for k in range(1, 10):
            lx = gx + (250/10)*k
            svg.append((z_base+8, f'<line x1="{lx}" y1="{gy}" x2="{lx}" y2="{gy+12}" stroke="black" stroke-width="0.5" />'))



# --- MODULE HABILLAGE (HELPERS & DEFINITIONS) ---

# Define Profile Models based on User Images (1-5)
PROFILES_DB = {
    # 1. Plat (Ex m9)
    "m1": {
        "name": "Modèle 1 (Plat / Chant)",
        "image_key": "uploaded_image_3_1765906701825.jpg",
        "params": ["A"], 
        "defaults": {"A": 100}
    },
    # 2. Cornière Simple (Ex m8)
    "m2": {
        "name": "Modèle 2 (Cornière Simple)",
        "image_key": "uploaded_image_2_1765906701825.jpg",
        "params": ["A", "B"], 
        "defaults": {"A": 50, "B": 50}
    },
    # 3. Cornière Complexe (Ex m1)
    "m3": {
        "name": "Modèle 3 (Cornière Complexe)",
        "image_key": "uploaded_image_0_1765905922661.jpg", 
        "params": ["A", "B", "A1"],
        "defaults": {"A": 50, "B": 50, "A1": 90}
    },
    # 4. Profil en U (Ex m10)
    "m4": {
        "name": "Modèle 4 (Profil en U)",
        "image_key": "uploaded_image_4_1765906701825.jpg",
        "params": ["A", "B", "C"], 
        "defaults": {"A": 40, "B": 150, "C": 40}
    },
    # 5. Profil en Z (Ex m7)
    "m5": {
        "name": "Modèle 5 (Profil en Z)",
        "image_key": "uploaded_image_1_1765906701825.jpg",
        "params": ["A", "B", "C"], 
        "defaults": {"A": 40, "B": 60, "C": 40}
    },
    # 6. Profil en Z Complexe (Ex m6) - SAME KEY, Updated logic kept
    "m6": {
        "name": "Modèle 6 (Profil en Z Complexe)",
        "image_key": "uploaded_image_0_1765906701825.jpg",
        "params": ["A", "B", "C", "D", "A1", "A2", "A3"],
        "defaults": {"A": 20, "B": 100, "C": 30, "D": 20, "A1": 100, "A2": 100, "A3": 90}
    },
    # 7. Cornière 3 Plis (Ex m3)
    "m7": {
        "name": "Modèle 7 (Cornière 3 Plis)",
        "image_key": "uploaded_image_2_1765905922661.jpg",
        "params": ["A", "B", "C", "A1"],
        "defaults": {"A": 20, "B": 20, "C": 50, "A1": 90}
    },
    # 8. Couverine (Ex m2)
    "m8": {
        "name": "Modèle 8 (Couverine 3 Plis)",
        "image_key": "uploaded_image_1_1765905922661.jpg",
        "params": ["A", "B", "C", "A1", "A2"],
        "defaults": {"A": 40, "B": 100, "C": 40, "A1": 135, "A2": 135}
    },
    # 9. Bavette (Ex m5)
    "m9": {
        "name": "Modèle 9 (Bavette)",
        "image_key": "uploaded_image_4_1765905922661.jpg",
        "params": ["A", "B", "C", "A1", "A2"],
        "defaults": {"A": 15, "B": 100, "C": 20, "A1": 95, "A2": 90}
    },
    # 10. Z Rejet (Ex m4)
    "m10": {
        "name": "Modèle 10 (Z / Rejet)",
        "image_key": "uploaded_image_3_1765905922661.jpg",
        "params": ["A", "B", "C", "D", "E", "A1"],
        "defaults": {"A": 20, "B": 50, "C": 20, "D": 50, "E": 20, "A1": 90} 
    },
    "m11": {
        "name": "Sur Mesure",
        "image_key": "custom_icon.png", # Placeholder
        "params": [], # Dynamic
        "defaults": {},
        "is_custom": True
    }
}

def calc_developpe(type_p, inputs):
    """Calculates developed length (raw material width)."""
    if type_p == "m11":
        segs = st.session_state.get('custom_segments', [])
        total = 0
        if not segs: return 100 # Default
        
        # Seg 0 is always Flat -> Length
        total += segs[0].get('val_L', 0)
        
        for s in segs[1:]:
             atype = s.get('angle_type', '90')
             if atype in ['90', '45', '135', '180']:
                 total += s.get('val_L', 0)
             else:
                 # Custom: L and H
                 l = s.get('val_L', 0)
                 h = s.get('val_H', 0)
                 total += math.sqrt(l*l + h*h)
        return total

    # Existing logic for fixed profiles (fallback)
    # Quick sum of all single-letter params
    keys = [k for k in inputs if len(k)==1 and k.isupper()]
    total = sum([inputs.get(k, 0) for k in keys])
    return total

def generate_profile_svg(type_p, inputs, length, color_name):
    w_svg, h_svg = 700, 500
    
    colors = {
        "Blanc 9016": "#FFFFFF",
        "Gris 7016": "#383E42",
        "Noir 9005": "#000000",
        "Chêne Doré": "#C6930A",
        "Autre": "#999999"
    }
    fill_col = colors.get(color_name, "#CCCCCC")
    
    points = [(0,0)] # Start at origin

    # CUSTOM MODEL LOGIC (M11)
    if type_p == "m11":
        segs = st.session_state.get('custom_segments', [])
        if not segs:
            # Default Start if no segments defined
            points.append((100, 0))
        else:
            # Turtle Graphics
            # Start Direction: Right (0 deg from +X axis)
            curr_angle_deg = 0 
            curr_x, curr_y = 0, 0
            
            # Seg 1: Flat (always horizontal right)
            l0 = segs[0].get('val_L', 100)
            curr_x += l0
            points.append((curr_x, curr_y))
            
            # Follow up segments
            for s in segs[1:]:
                atype = s.get('angle_type', '90')
                l = s.get('val_L', 50)
                
                if atype == '90':
                    # Turn 90 deg (relative to current direction). Default to Up.
                    # If current is Right (0), turn Up (-90).
                    # If current is Up (-90), turn Left (-180).
                    turn = -90 
                    curr_angle_deg += turn
                    rad = math.radians(curr_angle_deg)
                    curr_x += math.cos(rad) * l
                    curr_y += math.sin(rad) * l
                    
                elif atype == '45':
                    turn = -45
                    curr_angle_deg += turn
                    rad = math.radians(curr_angle_deg)
                    curr_x += math.cos(rad) * l
                    curr_y += math.sin(rad) * l

                elif atype == '135':
                    turn = -135
                    curr_angle_deg += turn
                    rad = math.radians(curr_angle_deg)
                    curr_x += math.cos(rad) * l
                    curr_y += math.sin(rad) * l
                
                elif atype == 'Custom':
                    h = s.get('val_H', 20)
                    
                    # Calculate the vector for (L, H) in the current segment's local coordinate system
                    # L is along the current direction, H is perpendicular (upwards, so -H in SVG Y)
                    
                    # Rotate (L, -H) by current_angle_deg
                    rad_curr = math.radians(curr_angle_deg)
                    
                    # New X = L * cos(angle) - (-H) * sin(angle)
                    # New Y = L * sin(angle) + (-H) * cos(angle)
                    dx = l * math.cos(rad_curr) - (-h) * math.sin(rad_curr)
                    dy = l * math.sin(rad_curr) + (-h) * math.cos(rad_curr)
                    
                    curr_x += dx
                    curr_y += dy
                    
                    # Update the current angle to the direction of the new segment
                    new_rad = math.atan2(dy, dx)
                    curr_angle_deg = math.degrees(new_rad)
                
                points.append((curr_x, curr_y))
                
    else:
        # Logic per model (UPDATED MAPPING m1..m10)
        
        # 1. Plat (Ex m9) -> m1
        if type_p == "m1":
            A = inputs.get("A", 100)
            points.append((A, 0)) # Horizontal

        # 2. Cornière Simple (Ex m8) -> m2
        elif type_p == "m2":
            A = inputs.get("A", 50)
            B = inputs.get("B", 50)
            points.append((0, -A)) # Up
            points.append((points[-1][0] + B, points[-1][1])) # Right

        # 3. Cornière Complexe (Ex m1) -> m3
        elif type_p == "m3": 
            # Seg 1: A (Up)
            A = inputs.get("A", 50)
            points.append((0, -A)) # P1
            
            A1 = inputs.get("A1", 90)
            B = inputs.get("B", 50)
            
            # Rotate vector logic (Up is 0, -1)
            # Angle from vertical (-Y) is A1.
            # If A1=90 -> Right. If A1=100 -> Down-Right.
            # Current direction is Up (angle -90 or 270 from +X axis).
            # We want to turn by (180 - A1) degrees relative to the previous segment.
            # If A1=90, turn 90. So -90 + 90 = 0 (Right).
            # If A1=100, turn 80. So -90 + 80 = -10 (Down-Right).
            current_angle_deg = -90 # Up
            turn_angle_deg = 180 - A1
            new_angle_deg = current_angle_deg + turn_angle_deg
            
            rad = math.radians(new_angle_deg)
            vx = math.cos(rad)
            vy = math.sin(rad)
            p2 = (points[-1][0] + vx * B, points[-1][1] + vy * B)
            points.append(p2)

        # 4. Profil en U (Ex m10) -> m4
        elif type_p == "m4": 
            A = inputs.get("A", 40)
            B = inputs.get("B", 150)
            C = inputs.get("C", 40)
            points.append((0, -A)) # Up
            points.append((points[-1][0] + B, points[-1][1])) # Right
            points.append((points[-1][0], points[-1][1] + C)) # Down

        # 5. Profil en Z (Ex m7) -> m5 (FIXED to be Step Z)
        elif type_p == "m5": 
            A = inputs.get("A", 40)
            B = inputs.get("B", 60)
            C = inputs.get("C", 40)
            # Z Step: Up, Right, Up
            points.append((0, -A)) # Up
            points.append((points[-1][0] + B, points[-1][1])) # Right
            points.append((points[-1][0], points[-1][1] - C)) # Up again (Y decreases)

        # 6. Profil en Z Complexe (Ex m6) -> m6 (FIXED ANGLES)
        elif type_p == "m6": 
            A = inputs.get("A", 20)
            B = inputs.get("B", 100)
            C = inputs.get("C", 30)
            D = inputs.get("D", 20)
            
            A1 = inputs.get("A1", 100) # Angle A-B
            A2 = inputs.get("A2", 100) # Angle B-C
            A3 = inputs.get("A3", 90)  # Angle C-D
            
            # P0->P1: Up A
            points.append((0, -A))
            
            # P1->P2: B (Sloped)
            # A1 is the internal angle between segment A (vertical up) and segment B.
            # Previous segment direction: Up (-90 deg from +X axis).
            # Turn angle = 180 - A1.
            # If A1=90, turn 90 deg. New angle = -90 + 90 = 0 (Right).
            # If A1=100, turn 80 deg. New angle = -90 + 80 = -10 (Down-Right).
            current_angle_deg = -90 # Up
            turn_angle_deg = 180 - A1
            angle_b_deg = current_angle_deg + turn_angle_deg
            
            rad_b = math.radians(angle_b_deg)
            vx_b = math.cos(rad_b)
            vy_b = math.sin(rad_b)
            points.append((points[-1][0] + vx_b * B, points[-1][1] + vy_b * B))
            
            # P2->P3: C (Sloped)
            # A2 is the internal angle between segment B and segment C.
            # Previous segment direction: angle_b_deg.
            # Turn angle = 180 - A2.
            angle_c_deg = angle_b_deg + (180 - A2)
            
            rad_c = math.radians(angle_c_deg)
            vx_c = math.cos(rad_c)
            vy_c = math.sin(rad_c)
            points.append((points[-1][0] + vx_c * C, points[-1][1] + vy_c * C))
            
            # P3->P4: D (Sloped)
            # A3 is the internal angle between segment C and segment D.
            # Previous segment direction: angle_c_deg.
            # Turn angle = 180 - A3.
            angle_d_deg = angle_c_deg + (180 - A3)
            
            rad_d = math.radians(angle_d_deg)
            vx_d = math.cos(rad_d)
            vy_d = math.sin(rad_d)
            points.append((points[-1][0] + vx_d * D, points[-1][1] + vy_d * D))
            
        # 7. Cornière 3 Plis (Ex m3) -> m7
        elif type_p == "m7": 
             # A - B - C generic
             keys = [k for k in inputs if len(k)==1 and k.isupper()]
             x, y = 0, 0
             points = [(x,y)]
             # Simple generic draw for now as m3 was generic
             for k in keys:
                 val = inputs[k]
                 x += val * 0.7
                 y -= val * 0.7
                 points.append((x,y))

        # 8. Couverine (Ex m2) -> m8
        elif type_p == "m8":
            A = inputs.get("A", 40)
            B = inputs.get("B", 100)
            C = inputs.get("C", 40)
            A1 = inputs.get("A1", 135)
            A2 = inputs.get("A2", 135)
            
            points.append((0, -A))
            
            # Current angle is -90 (Up)
            current_angle_deg = -90
            turn1_deg = 180 - A1
            angle1_deg = current_angle_deg + turn1_deg
            
            rad1 = math.radians(angle1_deg)
            vx1 = math.cos(rad1)
            vy1 = math.sin(rad1)
            p2 = (points[-1][0] + vx1 * B, points[-1][1] + vy1 * B)
            points.append(p2)
            
            # Turn A2
            turn2_deg = 180 - A2
            angle2_deg = angle1_deg + turn2_deg
            
            rad2 = math.radians(angle2_deg)
            vx2 = math.cos(rad2)
            vy2 = math.sin(rad2)
            p3 = (points[-1][0] + vx2 * C, points[-1][1] + vy2 * C)
            points.append(p3)

        # 9. Bavette (Ex m5) -> m9
        elif type_p == "m9":
             # Schema: A (Up), B (Slope), C (Down), D (Return Left)
             A = inputs.get("A", 15)
             B = inputs.get("B", 100)
             C = inputs.get("C", 20)
             D = inputs.get("D", 15)
             A1 = inputs.get("A1", 95) # Slope angle
             
             # P1: Up A
             points.append((0, -A))
             
             # P2: Slope B (Angle A1 from vertical? or Horizontal?)
             # Usually Bavette slope is ~10 deg.
             # A1=95 implies 5 deg slope down.
             # Standard Ref: Horizontal Right = 0 deg.
             # A1 is internal angle A-B? A is Vertical Up (-90).
             # If A1=95, Turn is 180-95=85. New angle -90+85 = -5. (Slop Down).
             current_angle = -90
             turn = 180 - A1
             angle_b = current_angle + turn
             rad_b = math.radians(angle_b)
             
             points.append((points[-1][0] + math.cos(rad_b)*B, points[-1][1] + math.sin(rad_b)*B))
             
             # P3: Down C
             # Relative to B? Or Vertical Down?
             # Usually vertical down.
             points.append((points[-1][0], points[-1][1] + C))
             
             # P4: Return D (Left or In)
             # Usually return is Horizontal Left or angled 'E'.
             # Let's assume Horizontal Left "Goutte d'eau".
             # Return angle A2? If not provided, assume 90 relative or just Horiz.
             # Schema shows angled return. But let's simplify to Horizontal Left for D.
             points.append((points[-1][0] - D, points[-1][1])) # Left

        # 10. Z Rejet (Ex m4) -> m10
        elif type_p == "m10":
            # Schema: A(Horiz), B(Vert), C(Slope), D(Vert), E(Return)
            A = inputs.get("A", 20)
            B = inputs.get("B", 50)
            C = inputs.get("C", 20)
            D = inputs.get("D", 50)
            E = inputs.get("E", 20)
            A1 = inputs.get("A1", 90) # Angle for C?
            
            # P1: Right A
            points.append((A, 0))
            
            # P2: Down B
            points.append((points[-1][0], points[-1][1] + B))
            
            # P3: Slope C (Rejet)
            # Angle A1. If B is Down (90 deg).
            # A1=135. Turn = 180 - 135 = 45.
            # New angle = 90 - 45 = 45 (Down Right).
            # Let's use A1 properly.
            # Previous dir: Down (90 deg).
            # Turn: -(180-A1) (Clockwise/Counter? Rejet goes Out/Right).
            # Turn Left (CCW) is positive. Rejet goes Right.
            # Let's just calculate absolute direction: Down-Right.
            # Assuming A1 is the internal angle between B (down) and C (slope)
            # If A1=90, C is horizontal right.
            # If A1=135, C is 45 deg down-right.
            current_angle_deg = 90 # Down
            turn_angle_deg = -(180 - A1) # Negative for clockwise turn (right)
            angle_c_deg = current_angle_deg + turn_angle_deg
            
            rad_c = math.radians(angle_c_deg)
            vx_c = math.cos(rad_c)
            vy_c = math.sin(rad_c)
            points.append((points[-1][0] + vx_c * C, points[-1][1] + vy_c * C))
            
            # P4: Down D
            points.append((points[-1][0], points[-1][1] + D))
            
            # P5: Return E (Left)
            points.append((points[-1][0] - E, points[-1][1])) # Left

        else:
            # Default Fallback
            points = [(0,0), (0, -100), (100, -100)]


    # Normalize coordinates to fit in View
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    w_shape = max_x - min_x
    h_shape = max_y - min_y
    
    # Scale to fill 30% of SVG
    target_size = 150
    scale = 1.0
    if w_shape > 0 or h_shape > 0:
        scale = target_size / max(w_shape, h_shape, 1)
        
    # Project 2D Profile (Front Face)
    ox, oy = 150, 250
    
    scaled_points = []
    for p in points:
        nx = ox + (p[0] - min_x) * scale
        ny = oy + (p[1] - min_y) * scale
        scaled_points.append((nx, ny))
        
    # Create Back Face (Depth)
    depth_x, depth_y = 250, -100
    back_points = []
    for p in scaled_points:
        back_points.append((p[0] + depth_x, p[1] + depth_y))
        
    # DRAW SVG
    svg_els = []
    style_line = f'stroke="black" stroke-width="2" fill="none"'
    
    # 1. Back lines (Wireframe) - dashed
    path_back = "M " + " L ".join([f"{p[0]},{p[1]}" for p in back_points])
    svg_els.append(f'<path d="{path_back}" stroke="#999" stroke-width="1" fill="none" stroke-dasharray="4,4" />')
    
    # 2. Connectors (Back to Front)
    for p1, p2 in zip(scaled_points, back_points):
        svg_els.append(f'<line x1="{p1[0]}" y1="{p1[1]}" x2="{p2[0]}" y2="{p2[1]}" stroke="#555" stroke-width="1" />')
    
    # ADDED LOGIC: LENGTH LABEL - MOVED TO BACK (Perspective)
    if len(scaled_points) > 0:
        # User wants it "au bout de l'image, pour donner de la profondeur"
        # We can place it at 80% along the connector from Front to Back
        # Let's use the first segment connector
        p_front = scaled_points[0]
        p_back = back_points[0]
        
        # 80% towards back
        t = 0.8
        lbl_x = p_front[0] + (p_back[0] - p_front[0]) * t
        lbl_y = p_front[1] + (p_back[1] - p_front[1]) * t
        
        # Slightly above
        lbl_y -= 15
        
        # Display Length
        svg_els.append(f'<text x="{lbl_x}" y="{lbl_y}" font-family="Arial" font-size="14" fill="#335c85" font-weight="bold" text-anchor="middle">L={length}</text>')
        
    # 3. Front Face (Profile) - Thick
    path_front = "M " + " L ".join([f"{p[0]},{p[1]}" for p in scaled_points])
    svg_els.append(f'<path d="{path_front}" {style_line} stroke="#000" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />')
    
    # Labels (Dimensions) - Left Normal Logic
    for i in range(len(scaled_points)-1):
        p1 = scaled_points[i]
        p2 = scaled_points[i+1]
        
        # Midpoint
        mx = (p1[0] + p2[0])/2
        my = (p1[1] + p2[1])/2
        
        # Direction Vector
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        
        # Normalize Dir
        len_seg = math.sqrt(dx*dx + dy*dy)
        if len_seg == 0: len_seg = 1
        dx, dy = dx/len_seg, dy/len_seg
        
        # Left Normal Vector (dy, -dx)
        nx = dy
        ny = -dx
        
        # Offset
        offset = 12
        lx = mx + nx * offset
        ly = my + ny * offset
        
        # Text Anchoring
        anchor = "middle"
        baseline = "middle"
        
        # Analyze Normal Direction
        # Pure Left
        if nx < -0.7: 
            anchor = "end"      
            baseline = "middle"
        # Pure Right
        elif nx > 0.7:
            anchor = "start"
            baseline = "middle"
        # Pure Up
        elif ny < -0.7:
            anchor = "middle"
            baseline = "baseline"
            ly += 5
        # Pure Down
        elif ny > 0.7:
            anchor = "middle"
            baseline = "hanging"
            ly -= 5
        else:
            # Diagonal
            if nx < 0: anchor = "end"
            else: anchor = "start"
            if ny < 0: baseline = "baseline"
            else: baseline = "hanging"

        # Special Override for M1 (Flat)
        if type_p == "m1":
             # Force Up
             lx = mx
             ly = my - 15  # Above
             anchor = "middle"
             baseline = "baseline"

        # M5 (Z) - Segment C (i=2)
        # Up Segment on Right Side -> Force Right Label
        if type_p == "m5" and i == 2:
             lx = mx + 15
             ly = my
             anchor = "start"
             baseline = "middle"
             
        # M9 (Bavette) - Segment C (i=2) -> Down Vertical. Left Normal is Right. Correct.
        # M10 (Z Rejet) - Segment C (i=2) -> Slope Down. 
        # Check collision with perspective?
        
        try:
             param_key = PROFILES_DB[type_p]["params"][i]
             svg_els.append(f'<text x="{lx}" y="{ly}" font-family="Arial" font-size="14" fill="red" font-weight="bold" text-anchor="{anchor}" dominant-baseline="{baseline}">{param_key}</text>')
        except: pass

    # ADDED LOGIC: FACE 1 / FACE 2 LABELS
    # Find longest segment to anchor face labels
    max_len = -1
    best_idx = 0
    
    if len(scaled_points) > 1:
        for i in range(len(scaled_points)-1):
            p1 = scaled_points[i]
            p2 = scaled_points[i+1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            l = math.sqrt(dx*dx + dy*dy)
            if l > max_len:
                max_len = l
                best_idx = i
                
        # Calculate Normal for longest segment
        p1 = scaled_points[best_idx]
        p2 = scaled_points[best_idx+1]
        mx = (p1[0] + p2[0])/2
        my = (p1[1] + p2[1])/2
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        norm_len = math.sqrt(dx*dx+dy*dy)
        if norm_len==0: norm_len=1
        
        # Left Normal (Outside / Face 1)
        nx = dy / norm_len
        ny = -dx / norm_len
        
        # Positions
        # Face 1: Outside (Left) - Increased distance for readability
        f1_dist = 70 
        f1_x = mx + nx * f1_dist
        f1_y = my + ny * f1_dist
        
        # Face 2: Inside (Right)
        f2_dist = 40
        f2_x = mx - nx * f2_dist
        f2_y = my - ny * f2_dist
        
        # Styling
        face_style = 'font-family="Arial" font-size="12" fill="#666" font-style="italic" text-anchor="middle" dominant-baseline="middle"'
        
        svg_els.append(f'<text x="{f1_x}" y="{f1_y}" {face_style}>FACE 1</text>')
        svg_els.append(f'<text x="{f2_x}" y="{f2_y}" {face_style}>FACE 2</text>')

    final_svg = f'<svg width="{w_svg}" height="{h_svg}" xmlns="http://www.w3.org/2000/svg" style="background-color: white;">'
    final_svg += "".join(svg_els)
    final_svg += '</svg>'
    
    return final_svg

def render_habillage_main_ui(inputs, selected_key):
    """Renders the Main Content Area for Habillage."""
    
    # 1. Header
    profile_name = PROFILES_DB[selected_key]["name"]
    st.markdown(f"### 🧱 {profile_name}")
    
    # 2. Main Columns
    c1, c2 = st.columns([1, 2])
    
    # Layout:
    # C1: Schema Image + Key Info (Dev, Qty, Dims)
    # C2: 3D Visualization
    # Bottom: Full Recap Table + Export
    
    # Calculate Data
    L_mm = inputs.get("length", 3000) # Changed from "longueur" to "length" based on sidebar output
    dev_prod = calc_developpe(selected_key, inputs)
    qty = inputs.get("qte", 1) # Changed from "qte" to "qty" for consistency with sidebar output
    
    # Format Dim String
    dim_parts = []
    params = PROFILES_DB[selected_key]["params"]
    for p in params:
        val = inputs.get(p, PROFILES_DB[selected_key]["defaults"].get(p))
        dim_parts.append(f"{p}={val}")
    dim_str = ", ".join(dim_parts)

    with c1:
        st.subheader("Schéma de Principe")
        img_key = PROFILES_DB[selected_key]["image_key"]
        
        # Display Image or Placeholder
        # Check if we have the file
        image_path = os.path.join(ARTIFACT_DIR, img_key)
        if os.path.exists(image_path):
             st.image(image_path, use_container_width=True)
        else:
             # Try absolute path from brain if needed (dev mode hack)
             # But usually running in scratch/v73_fix
             # Let's assume relative path works or try to find it
             # Fallback
             st.info(f"Image {img_key} non trouvée")

        st.markdown("---")
        st.markdown("#### Informations Clés")
        
        # Big metric
        st.metric("Développé Unitaire", f"{int(dev_prod)} mm")
        
        st.markdown(f"**Quantité :** {qty}")
        st.markdown(f"**Dimensions :** {dim_str}")
        st.markdown(f"**Longueur :** {L_mm} mm")
        st.markdown(f"**Matière :** {inputs.get('finition', 'Prélaqué 1 face')}") # Changed from "matiere" to "finition"
        st.markdown(f"**Couleur (Face 1) :** {inputs.get('couleur', 'Blanc 9016')}") # Explicit Face 1
             
    with c2:
        st.subheader("Visualisation 3D")
        color_sel = inputs.get("couleur", "Blanc 9016") # Changed from "color" to "couleur"
        svg_code = generate_profile_svg(selected_key, inputs, L_mm, color_sel)
        st.components.v1.html(svg_code, height=600, scrolling=True)
        st.caption("Vue filaire 3D indicative. Face 1 = Face Laquée.")

    # 3. Bottom Section: Full Recap & Actions
    st.markdown("---")
    st.subheader("Récapitulatif (Habillage)")
    
    col_table, col_export = st.columns([3, 1])
    
    with col_table:
        data = {
            "Libellé": ["Référence", "Modèle", "Quantité", "Dimensions", "Longueur", "Développé", "Surface Totale", "Matière", "Épaisseur", "Couleur (Face 1)"],
            "Valeur": [
                inputs.get("ref", "Bavette F1"), # Changed from "ref" to "ref"
                profile_name,
                str(qty),
                dim_str,
                f"{L_mm} mm",
                f"{int(dev_prod)} mm",
                f"{((dev_prod * L_mm * qty) / 1000000):.2f} m²",
                inputs.get("finition", "Prélaqué 1 face"), # Changed from "matiere" to "finition"
                inputs.get('epaisseur', "75/100"), # Changed from "epaisseur" to "epaisseur"
                inputs.get("couleur", "Blanc 9016") # Changed from "color" to "couleur"
            ]
        }
        df = pd.DataFrame(data)
        st.table(df)
        
    with col_export:
        st.write("")
        st.write("")
        
        # Prepare data for download button
        hab_data = {
            "ref": inputs.get("ref", "Bavette F1"),
            "modele": profile_name,
            "qte": qty,
            "dims": {p: inputs.get(p, PROFILES_DB[selected_key]["defaults"].get(p)) for p in PROFILES_DB[selected_key]["params"]},
            "longueur": L_mm,
            "developpe": dev_prod,
            "finition": inputs.get("finition", "Prélaqué 1 face"),
            "epaisseur": inputs.get('epaisseur', "75/100"),
            "couleur": inputs.get("couleur", "Blanc 9016")
        }
        json_hab = json.dumps(hab_data, indent=2, ensure_ascii=False)
        st.download_button("💾 Télécharger Fiche Habillage", json_hab, f"habillage_{inputs.get('ref', 'Bavette F1')}.json", "application/json", use_container_width=True)

def render_habillage_sidebar_ui():
    """Renders the Sidebar inputs for Habillage and returns the config dict."""
    config = {}
    
    st.sidebar.markdown("### 🛠 Options Habillage")
    
    # 0. Identification
    with st.sidebar.expander("1. Identification", expanded=False):
        c_ref, c_qte = st.columns([2, 1])
        ref_chantier = c_ref.text_input("Référence", "Bavette F1", key="hab_ref")
        qte_piece = c_qte.number_input("Qté", 1, 100, 1, key="hab_qte")
        config["ref"] = ref_chantier
        config["qte"] = qte_piece

    # 1. Model Selection
    profile_keys = list(PROFILES_DB.keys())
    model_labels = {k: PROFILES_DB[k]["name"] for k in profile_keys}
    
    with st.sidebar.expander("2. Modèle & Dimensions", expanded=False):
        selected_key = st.selectbox("Modèle", profile_keys, format_func=lambda x: model_labels[x])
        prof = PROFILES_DB[selected_key]

        # Dimensions
        inputs = {}
        cols_input = st.columns(2)
        for i, p in enumerate(prof["params"]):
            is_angle = p.startswith("A") and len(p) > 1 and p[1].isdigit() 
            step = 5 if is_angle else 5
            defaults = prof["defaults"]
            
            with cols_input[i % 2]:
                label = f"Angle {p}" if is_angle else f"Cote {p}"
                val = st.number_input(label, value=int(defaults.get(p, 0)), step=int(step), key=f"hab_{selected_key}_{p}")
                inputs[p] = val
        
        length = st.number_input("Longueur (mm)", value=3000, step=100)

    # 2. Finish
    with st.sidebar.expander("3. Finition", expanded=False):
        type_finition = st.selectbox("Type", ["Prélaqué 1 face", "Prélaqué 2 faces", "Brut", "Galva"], index=0)
        
        epaisseurs = ["75/100", "10/10", "15/10", "20/10", "30/10"]
        epaisseur = st.selectbox("Épaisseur", epaisseurs, index=0)
        
        colors_list = ["Blanc 9016", "Gris 7016", "Noir 9005", "Chêne Doré", "RAL Spécifique"]
        if "Brut" in type_finition or "Galva" in type_finition:
             couleur = f"Sans ({type_finition})"
             st.info(f"Aspect : {type_finition}")
        else:
             couleur_st = st.selectbox("Couleur", colors_list, index=0)
             if couleur_st == "RAL Spécifique":
                 couleur = st.text_input("Code RAL", "RAL ")
             else:
                 couleur = couleur_st

    return {
        "ref": ref_chantier,
        "qte": qte_piece,
        "key": selected_key,
        "prof": prof,
        "inputs": inputs,
        "length": length,
        "finition": type_finition,
        "epaisseur": epaisseur,
        "couleur": couleur
    }

def render_habillage_main_ui(cfg):
    """Renders the Main Content (Visuals, Recap) for Habillage using the config dict."""
    prof = cfg['prof']
    st.header(f"🧱 {prof['name']}") # Dynamic Header
    
    # Calculate Data Needed for both columns
    dev = calc_developpe(cfg['key'], cfg['inputs'])
    
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.subheader("Schéma de Principe")
        image_path = os.path.join(ARTIFACT_DIR, prof['image_key'])
        if os.path.exists(image_path):
            # Centered Image
            st.image(image_path, use_container_width=True)
        else:
            st.warning(f"Image introuvable: {prof['image_key']}")
            
        # --- RECAPITULATIF (BON DE COMMANDE) ---
        # Moving Recap here to fill space as requested
        st.markdown("---")
        st.markdown("<h3 class='centered-header'>Récapitulatif (Habillage)</h3>", unsafe_allow_html=True)
        
        dim_str = ", ".join([f"{k}={v}" for k,v in cfg['inputs'].items()])
        surface = (dev * cfg['length'] * cfg['qte']) / 1000000
        
        df_hab = pd.DataFrame({
            "Libellé": ["Référence", "Modèle", "Quantité", "Dimensions", "Longueur", "Développé", "Surface Totale", "Matière", "Épaisseur", "Couleur"],
            "Valeur": [
                cfg['ref'], prof['name'], cfg['qte'], dim_str, f"{cfg['length']} mm", f"{dev} mm", 
                f"{surface:.2f} m²", cfg['finition'], cfg['epaisseur'], cfg['couleur']
            ]
        })
        
        st.dataframe(df_hab, use_container_width=True, hide_index=True)
        
        # Export
        hab_data = {
            "ref": cfg['ref'], "modele": prof['name'], "qte": cfg['qte'],
            "dims": cfg['inputs'], "longueur": cfg['length'], "developpe": dev,
            "finition": cfg['finition'], "epaisseur": cfg['epaisseur'], "couleur": cfg['couleur']
        }
        json_hab = json.dumps(hab_data, indent=2, ensure_ascii=False)
        st.download_button("💾 Télécharger Fiche Habillage", json_hab, f"habillage_{cfg['ref']}.json", "application/json")
            
    with c2:
        st.subheader("Visualisation 3D")
        svg = generate_profile_svg(cfg['key'], cfg['inputs'], cfg['length'], cfg['couleur'])
        st.markdown(f'''
        <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; background-color: white; text-align: center;">
            {svg}
        </div>
        ''', unsafe_allow_html=True)
        st.caption("Vue filaire 3D indicative.")

        st.metric("Développé Unitaire", f"{dev} mm", delta_color="off")


# --- 2. INTERFACE SIDEBAR ---
# --- 2. INTERFACE SIDEBAR ---
# GESTION DE PROJET (V73)
render_project_sidebar()

st.sidebar.title("🛠️ Configuration")

# MENU NAVIGATION RETIRÉ (Retour aux expanders standards)

if st.sidebar.button("❌ Réinitialiser la configuration", key="btn_reset"):
    reset_config()

def render_menuiserie_sidebar_global():
    global rep, qte, mat, ep_dormant, type_projet, type_pose, ail_val, ail_bas, col_int, col_ext
    global l_dos_dormant, h_dos_dormant, h_allege, vr_opt, h_vr, vr_grille, h_menuiserie
    global is_appui_rap, largeur_appui, txt_partie_basse, zones_config, cfg_global

    # --- SECTION 1 : IDENTIFICATION ---
    with st.sidebar.expander("1. Identification", expanded=False):
        c1, c2 = st.columns(2)
        rep = c1.text_input("Repère", "F1", key="ref_id")
        qte = c2.number_input("Qté", 1, 100, 1, key="qte_val")

    # --- SECTION 2 : MATERIAU ---
    with st.sidebar.expander("2. Matériau & Ailettes", expanded=False):
        mat = st.radio("Matériau", ["PVC", "ALU"], horizontal=True, key="mat_type")

        if mat == "PVC":
            liste_ailettes_std = [0, 30, 40, 60]
            liste_couleurs = ["Blanc (9016)", "Plaxé Chêne", "Plaxé Gris 7016", "Beige"]
        else: 
            liste_ailettes_std = [0, 20, 35, 60, 65]
            liste_couleurs = ["Blanc (9016)", "Gris 7016 Texturé", "Noir 2100 Sablé", "Anodisé Argent"]

        ep_dormant = st.number_input("Épaisseur Dormant (mm)", 50, 200, 70, step=10, help="Largeur visible du profilé", key="frame_thig")

        st.write("---")
        # NOUVEAU : TYPE DE POSE
        # Remplacement Checkbox par Radio Horizontal (Style PVC/ALU)
        type_projet = st.radio("Type de Projet", ["Rénovation", "Neuf"], index=0, horizontal=True, key="proj_type")
        
        if type_projet == "Rénovation":
            liste_pose = ["Pose en rénovation (R)", "Pose en rénovation Dépose Totale (RT)"]
        else:
            liste_pose = ["Pose en applique avec doublage (A)", "Pose en applique avec embrasures (E)", 
                          "Pose en feuillure (F)", "Pose en tunnel nu intérieur (T)", "Pose en tunnel milieu de mur (TM)"]
        
        type_pose = st.selectbox("Type de Pose", liste_pose, key="pose_type")

        st.write("---")
        ail_val = st.selectbox(f"Ailettes H/G/D ({mat})", liste_ailettes_std, index=len(liste_ailettes_std)-1, key="fin_val")
        bas_identique = st.checkbox("Seuil (Bas) identique ?", False, key="same_bot")
        ail_bas = ail_val if bas_identique else st.selectbox(f"Seuil / Bas ({mat})", liste_ailettes_std, index=0, key="fin_bot")

        # CONFIG PARTIE BASSE (Seuil)
        st.write("---")
        st.markdown("**Partie Basse**")
        is_appui_rap = st.checkbox("Appui rapporté ?", False, key="is_appui_rap")
        largeur_appui = 0
        if is_appui_rap:
            largeur_appui = st.number_input("Largeur Appui (mm)", 0, 500, 100, step=10, key="width_appui")
            txt_partie_basse = f"Appui Rapporté (Largeur {largeur_appui}mm)"
        else:
            txt_partie_basse = "Bavette 100x100 mm"
            st.caption("Défaut : Bavette 100x100 mm")

        st.write("---")
        col_int = st.selectbox("Couleur Int", liste_couleurs, key="col_in")
        col_ext = st.selectbox("Couleur Ext", liste_couleurs, key="col_ex")

    # --- SECTION 3 : DIMENSIONS ---
    with st.sidebar.expander("3. Dimensions & VR", expanded=False):
        c3, c4 = st.columns(2)
        
        # Libellé dynamique pour la Hauteur
        lbl_hauteur = "Hauteur dessus rejingo" if is_appui_rap else "Hauteur Dos Dormant (mm)"
        
        l_dos_dormant = c3.number_input("Largeur Dos Dormant (mm)", 300, 5000, 1200, 10, key="width_dorm")
        h_dos_dormant = c4.number_input(lbl_hauteur, 300, 5000, 1400, 10, help="Hauteur totale incluant le coffre", key="height_dorm")
        
        # Hauteur d'Allège
        h_allege = st.number_input("Hauteur d'Allège (mm)", 0, 2500, 900, step=10, key="h_allege")

        vr_opt = st.toggle("Volet Roulant", False, key="vr_enable")
        h_vr = 0
        vr_grille = False
        if vr_opt:
            h_vr = st.number_input("Hauteur Coffre", 0, 500, 185, 10, key="vr_h")
            vr_grille = st.checkbox("Grille d'aération sur Coffre ?", key="vr_g")
            h_menuiserie = h_dos_dormant - h_vr
            st.markdown(f"""<div class="metric-box">🧮 H. Menuiserie : {int(h_menuiserie)} mm</div>""", unsafe_allow_html=True)
        else:
            h_menuiserie = h_dos_dormant

    # --- SECTION 4 : STRUCTURE & FINITIONS ---
    with st.sidebar.expander("4. Structure & Finitions", expanded=False):
        # mode_structure = st.radio("Mode Structure", ["Simple (1 Zone)", "Divisée (2 Zones)"], horizontal=True, key="struct_mode", index=0)
        st.caption("Configurez les zones ci-dessous (Cochez 'Diviser' pour séparer)")

        # Initialisation de l'arbre si absent
        if 'zone_tree' not in st.session_state:
            st.session_state['zone_tree'] = init_node('root')
            
        # Rendu UI Récursif
        render_node_ui(st.session_state['zone_tree'], l_dos_dormant, h_menuiserie)
             
        # Calcul des zones à plat pour le dessin
        zones_config = flatten_tree(st.session_state['zone_tree'], 0, 0, l_dos_dormant, h_menuiserie)
        
        color_map = {"Blanc": "#FFFFFF", "Gris": "#383E42", "Noir": "#1F1F1F", "Chêne": "#C19A6B"}
        hex_col = "#FFFFFF"
        for k, v in color_map.items():
            if k in col_int: 
                hex_col = v

        cfg_global = {
            'color_frame': hex_col,
            'color_glass': "#d6eaff"
        }

# --- NAVIGATION LOGIC (INSERTED AFTER DEFINITIONS) ---
st.sidebar.markdown("---")
# Use segmented control for cleaner look if available, else radio
nav_options = ["Menuiserie", "Habillage"]
nav_mode = st.sidebar.radio("Module", nav_options, horizontal=True, label_visibility="collapsed")

hab_config = None

if nav_mode == "Menuiserie":
    st.sidebar.title("🛠️ Configuration")
    render_menuiserie_sidebar_global()
else:
    st.sidebar.title("🧱 Configuration")
    hab_config = render_habillage_sidebar_ui()
    




# --- 3. GÉNÉRATEUR SVG FINAL ---
def generate_svg_v73():
    svg = []
    col_fin = "#D3D3D3"
    
    ht_haut = h_vr + ail_val if vr_opt else ail_val
    ht_bas = ail_bas
    
    bx = -ail_val
    by = -ht_haut
    bw = l_dos_dormant + 2*ail_val
    bh = h_menuiserie + ht_haut + ht_bas
    # V73 FIX: Visible Dormant Frame (Stroke black)
    draw_rect(svg, bx, by, bw, bh, col_fin, "black", 1, 0)
    
    if vr_opt:
        draw_rect(svg, 0, -h_vr, l_dos_dormant, h_vr, cfg_global['color_frame'], "black", 1, 1)
        draw_text(svg, l_dos_dormant/2, -h_vr/2, f"COFFRE {int(h_vr)}", font_size=16, fill="white" if "Blanc" not in col_int else "black", weight="bold", z_index=5)
        if vr_grille:
             gx = (l_dos_dormant - 250)/2
             gy = -h_vr/2 + 20
             draw_rect(svg, gx, gy, 250, 12, "#eeeeee", "black", 1, 6)
             for k in range(1, 10):
                lx = gx + (250/10)*k
                svg.append((6, f'<line x1="{lx}" y1="{gy}" x2="{lx}" y2="{gy+12}" stroke="black" stroke-width="0.5" />'))

    th_dorm = float(ep_dormant) / 3.0
    draw_rect(svg, 0, 0, l_dos_dormant, h_menuiserie, cfg_global['color_frame'], "black", 2, 2)
    
    # AJOUT V72 : SEPARATEUR DE ZONES (Assemblage marqué)
    if len(zones_config) == 2:
        z1 = zones_config[0]
        z2 = zones_config[1]
        # Division Horizontale (Verification sur X et W identiques)
        if abs(z1['x'] - z2['x']) < 1 and abs(z1['w'] - z2['w']) < 1:
            split_y = z2['y']
            svg.append((3, f'<line x1="0" y1="{split_y}" x2="{l_dos_dormant}" y2="{split_y}" stroke="black" stroke-width="2" />'))
        # Division Verticale (Verification sur Y et H identiques)
        elif abs(z1['y'] - z2['y']) < 1 and abs(z1['h'] - z2['h']) < 1:
            split_x = z2['x']
            svg.append((3, f'<line x1="{split_x}" y1="0" x2="{split_x}" y2="{h_menuiserie}" stroke="black" stroke-width="2" />'))

    for i, z in enumerate(zones_config):
        # FIX: Remove th_dorm padding to avoid double-thickness (130mm mullions)
        # zones touch each other; vis_fixe/vis_ouvrant handles the frame face.
        draw_sash_content(svg, z['x'], z['y'], z['w'], z['h'], z['type'], z['params'], cfg_global, z_base=4)
        
        # DRAW ZONE LABEL (V73 REFINED: Discreet, Top-Left)
        if 'label' in z:
            # Discreet style: matches labels like "F", "VP" (Size 30, Blue #335c85)
            # Position: Top-Left with padding
            font_size = 30
            
            # Only draw if zone is reasonably distinct (width > 50)
            if z['w'] > 50 and z['h'] > 50:
                tx = z['x'] + 15
                ty = z['y'] + 35
                
                # Standard text, no heavy stroke, aligned left
                svg.append((25, f'<text x="{tx}" y="{ty}" font-family="Arial, sans-serif" font-size="{font_size}" font-weight="bold" fill="#335c85" text-anchor="start" style="pointer-events: none;">{z["label"]}</text>'))

    try:
        # --- COTATION ---
        font_dim = 26
        
        # OFFSETS
        off_chain_h = 40   # Details Largeur (Bas)
        off_overall_h = 90 # Totale Largeur (Bas)
        
        off_chain_v = -40  # Details Hauteur (Gauche)
        off_overall_v = -90 # Totale Hauteur (Gauche)

        # 1. COTES CUMULEES (Détails des zones)
        # Horizontal (Largeur)
        xs = sorted(list(set([z['x'] for z in zones_config] + [z['x']+z['w'] for z in zones_config])))
        for k in range(len(xs)-1):
            val = xs[k+1] - xs[k]
            if val > 1: # Ignore micro-gaps
                draw_dimension_line(svg, xs[k], 0, xs[k+1], 0, val, "", h_menuiserie+off_chain_h, "H", font_dim-4, 9)
                
        # Vertical (Hauteur)
        ys = sorted(list(set([z['y'] for z in zones_config] + [z['y']+z['h'] for z in zones_config])))
        for k in range(len(ys)-1):
            val = ys[k+1] - ys[k]
            if val > 1:
                # On dessine à gauche (x=0 est le bord gauche du dormant)
                # draw_dimension_line attend x1, y1...
                # Pour Vertical: x_line est calculé par (x1 - offset) dans la fonction
                # Si on passe x1=0, offset=40 => ligne à -40.
                # Attention : ma fonction draw_dimension_line gère "V" en soustrayant l'offset.
                # Donc si je veux être à -40, je dois passer offset=40 (avec x1=0).
                draw_dimension_line(svg, 0, ys[k], 0, ys[k+1], val, "", -off_chain_v, "V", font_dim-4, 9)

        # 2. COTES TOTALES (Existantes, repoussées)
        # Cadre (Largeur)
        draw_dimension_line(svg, 0, 0, l_dos_dormant, 0, l_dos_dormant, "", h_menuiserie+off_overall_h, "H", font_dim, 9)
        
        # Hors Tout (Largeur)
        l_ht = l_dos_dormant + 2*ail_val
        draw_dimension_line(svg, -ail_val, 0, l_dos_dormant+ail_val, 0, l_ht, "", h_menuiserie+off_overall_h+50, "H", font_dim, 9)


        # Cadre (Hauteur)
        top_dormant_y = -h_vr if vr_opt else 0
        h_dos_calc = h_menuiserie + (h_vr if vr_opt else 0)
        # Offset positif pour "V" part vers la gauche.
        # Je veux être à -90. Donc offset 90.
        draw_dimension_line(svg, 0, top_dormant_y, 0, h_menuiserie, h_dos_calc, "", -off_overall_v, "V", font_dim, 9)

        # Hors Tout (Hauteur)
        ht_haut = h_vr + ail_val if vr_opt else ail_val
        ht_bas = ail_bas
        y_start_ht = -ht_haut
        y_end_ht = h_menuiserie + ht_bas
        h_visuel_total = abs(y_end_ht - y_start_ht)
        draw_dimension_line(svg, 0, y_start_ht, 0, y_end_ht, h_visuel_total, "", -off_overall_v+50, "V", font_dim, 9)

        # HP (si applicable) - Reste au milieu
        # On cherche la première zone qui a une HP définie
        hp_z = None
        for z in zones_config:
            if 'h_poignee' in z['params']:
                hp_z = z
                break
        
        if hp_z is not None:
             hp_val = hp_z['params']['h_poignee']
             # Reference : Bas de la zone concernée
             y_bottom_zone = hp_z['y'] + hp_z['h']
             
             # Position Poignée (Y dans SVG)
             y_hp = y_bottom_zone - hp_val
             
             
             # Position X : Milieu de la zone (Croisement des triangles / Jonction)
             # x_center_zone = hp_z['x'] + hp_z['w'] / 2 OLD
             
             # CALCUL POSITION REELLE POIGNEE (Copie logique draw_sash_content)
             vis_ouvrant = 55
             ox, oy, ow, oh = hp_z['x'], hp_z['y'], hp_z['w'], hp_z['h']
             type_ouv = hp_z['type']
             params = hp_z['params']
             
             # Default Center
             x_handle_pos = ox + ow / 2 
             
             if type_ouv == "1 Vantail":
                 sens = params.get('sens', 'TG')
                 if sens == 'TG': x_handle_pos = ox + ow - 28
                 else: x_handle_pos = ox + 28
             elif type_ouv == "2 Vantaux":
                 w_vtl = ow / 2
                 is_princ_right = (params.get('principal', 'D') == 'D')
                 if is_princ_right: x_handle_pos = (ox + w_vtl) + 28
                 else: x_handle_pos = (ox + w_vtl) - 28
             
             # Draw Cote - Aligned with Handle X but shifted slightly
             # Dynamic Offset to push AWAY from Center (Towards Frame)
             sash_center_x = ox + ow / 2
             if x_handle_pos < sash_center_x:
                 offset_line = -40 # Shift Left (Towards Left Frame)
             else:
                 offset_line = 40  # Shift Right (Towards Right Frame)
             
             draw_dimension_line(svg, x_handle_pos + offset_line, y_hp, x_handle_pos + offset_line, y_bottom_zone, hp_val, "HP : ", 0, "V", 20, 20, leader_fixed_start=x_handle_pos)  
        
        # ANCIEN CODE (Supprimé)
        # has_ouvrant = any(z['type'] != "Fixe" for z in zones_config)
        # if has_ouvrant:
        #    hp_val = 1050 ...

        # Cadre (Hauteur)
        top_dormant_y = -h_vr if vr_opt else 0
        h_dos_calc = h_menuiserie + (h_vr if vr_opt else 0)
        # Fix NameError: Use -off_overall_v (90)
        draw_dimension_line(svg, 0, top_dormant_y, 0, h_menuiserie, h_dos_calc, "", -off_overall_v, "V", font_dim, 9)

        # Hors Tout (Hauteur)
        ht_haut = h_vr + ail_val if vr_opt else ail_val
        ht_bas = ail_bas
        y_start_ht = -ht_haut
        y_end_ht = h_menuiserie + ht_bas
        h_visuel_total = abs(y_end_ht - y_start_ht)
        # Fix NameError: Use -off_overall_v + 50 (140)
        draw_dimension_line(svg, 0, y_start_ht, 0, y_end_ht, h_visuel_total, "", -off_overall_v + 50, "V", font_dim, 9)

        # DEFS & RETURN
        defs = ""
        svg_str = "".join([el[1] for el in sorted(svg, key=lambda x:x[0])])
        
        margin_left_dims = 260
        margin_bottom_dims = 220
        margin_tight = 20
        
        vb_x = -margin_left_dims
        vb_y = -ht_haut - margin_tight
        vb_w = (l_dos_dormant + ail_val + margin_tight) - vb_x
        bbox_bottom = max(h_menuiserie + ht_bas, h_menuiserie + margin_bottom_dims)
        vb_h = bbox_bottom - vb_y
        
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb_x} {vb_y} {vb_w} {vb_h}" style="background-color:white;">{defs}{svg_str}</svg>'
    except Exception as e:
        import traceback
        return f'<svg width="600" height="200" viewBox="0 0 600 200"><rect width="600" height="200" fill="#fee"/><text x="10" y="30" fill="red" font-family="monospace" font-size="12">Erreur: {str(e)}</text><text x="10" y="50" fill="red" font-family="monospace" font-size="10">{traceback.format_exc().split("line")[-1]}</text></svg>'


# ==============================================================================
# --- MODULE HABILLAGE (INTÉGRÉ) ---
# ==============================================================================

# Base directory for artifacts
ARTIFACT_DIR = "/Users/rivet/.gemini/antigravity/brain/cb97bc5a-e933-4edf-a526-bbdd7caa31a4"

# Define Profile Models based on User Images (1-5)



# --- RENDU FINAL (NOUVELLE MISE EN PAGE V72) ---

# --- TABS ---
# 1. Menuiserie (Existant)
# 2. Habillage (Nouveau)

# --- NAVIGATION SWITCH (V74) replaced Tabs ---
if nav_mode == "Menuiserie":
    # 1. TITRE ET DESSIN CENTRÉS
    st.markdown("<h2 class='centered-header'>Plan Technique</h2>", unsafe_allow_html=True)

    try:
        svg_output = generate_svg_v73()
        st.markdown(f"<div class='centered-svg'>{svg_output}</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erreur SVG: {e}")
        import traceback
        st.code(traceback.format_exc())

    # 2. RÉCAPITULATIF (SOUS LE DESSIN)
    st.markdown("---")
    st.markdown("<h3 class='centered-header'>Récapitulatif - Bon de Commande</h3>", unsafe_allow_html=True)

    c_recap_left, c_recap_right = st.columns([1, 1])

    with c_recap_left:
        st.subheader("Informations Générales")
        
        # Safe Access to Keys
        s = st.session_state
        
        # Partie Basse Logic reconstruction
        if s.get('is_appui_rap', False):
            pb_txt = f"Appui Rapporté (Largeur {s.get('width_appui', 0)}mm)"
        else:
            pb_txt = "Bavette 100x100 mm"
            
        # VR Logic
        vr_txt = "Oui" if s.get('vr_enable', False) else "Non"
        
        # Ailettes Logic (From fin_val / fin_bot)
        h_ail = s.get('fin_val', 0)
        b_ail = s.get('fin_bot', 0) if not s.get('same_bot', False) else h_ail
        # Assuming H/G/D are same 'fin_val'
        ailes_txt = f"H:{h_ail}/G:{h_ail}/D:{h_ail}/B:{b_ail}"

        # Nb Zones calculation
        # We can't access 'zones_config' easily here as it's local to Sidebar context.
        # But we can check 'zone_tree'
        try:
            nb_zones = len(flatten_tree(s.get('zone_tree'), 0,0,0,0))
        except: nb_zones = 1

        df_infos = pd.DataFrame({
            "value": [
                s.get('ref_id', 'F1'),
                s.get('qte_val', 1),
                f"{s.get('width_dorm', 0)} x {s.get('height_dorm', 0)} mm",
                f"{s.get('mat_type', 'PVC')} (Dormant {s.get('frame_thig', 70)}mm)",
                s.get('pose_type', '-'),
                pb_txt,
                f"Int: {s.get('col_in', '-')} / Ext: {s.get('col_ex', '-')}",
                f"{nb_zones} Zone(s)",
                vr_txt,
                ailes_txt
            ]
        }, index=[
            "Repère", "Quantité", "Dim. Dos Dormant", "Matériau", "Type de Pose", "Partie Basse", "Couleur", "Structure", "VR", "Ailettes"
        ])
        st.dataframe(df_infos, use_container_width=True)
        
        # BOUTON EXPORT JSON
        export_data = serialize_config()
        export_json = json.dumps(export_data, indent=2, ensure_ascii=False)
        st.download_button(
            label="💾 Télécharger Fiche (PDF/Print)",
            data=export_json, # Placeholder for PDF
            file_name=f"{st.session_state.get('ref_id', 'Configuration')}_config.json",
            mime="application/json",
            help="Pour le moment export JSON, bientôt PDF."
        )

    with c_recap_right:
        st.subheader("Détail des Zones")
        config_display = flatten_tree(st.session_state.get('zone_tree'), 0,0,0,0)
        
        sorted_zones = sorted(config_display, key=lambda z: z['id'])
        
        for z in sorted_zones:
            # Clean Title "Zone X : Type"
            # Remove "Zone " from z['label'] if explicit? No logic needed if label is clean.
            # Assuming z['label'] is "Zone 1"
            st.markdown(f"#### {z['label']} : {z['type']}")
            
            # Details: Remplissage, Vitrage, Grille
            details_list = []
            
            # Remplissage
            remp_global = z['params'].get('remplissage_global', 'Vitrage')
            details_list.append(f"Remplissage : {remp_global}")
            
            # Vitrage details if applicable
            if remp_global == "Vitrage":
                v_txt = f"Ext {z['params'].get('vitrage_ext', '4mm')} / Int {z['params'].get('vitrage_int', '4mm')}"
                details_list.append(f"Vitrage : {v_txt}")
            
            # Grille
            if z['params'].get('grille_aera', False):
                pos_g = z['params'].get('pos_grille', 'Vtl Principal')
                details_list.append(f"Grille Aération : Oui ({pos_g})")
                
            # Sens
            if 'sens' in z['params']:
                 details_list.append(f"Sens : {z['params']['sens']}")

            # Formatting as bullet points
            for d in details_list:
                st.markdown(f"- {d}")
                
            st.markdown("---")

else:
    if hab_config:
        render_habillage_main_ui(hab_config)

# END OF CODE V73.5 (VALIDATED)
