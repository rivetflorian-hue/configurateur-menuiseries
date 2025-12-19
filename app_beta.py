import streamlit as st
import math
import uuid
import json
import copy
import pandas as pd
import os
import base64
import datetime


LOGO_B64 = "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"


st.set_page_config(
    layout="wide", 
    page_title="Calculateur Menuiserie & Habillage", 
    initial_sidebar_state="collapsed"
)


# --- PDF GENERATION WITH REPORTLAB & SVGLIB (ROBUST) ---
def generate_pdf_report(data_dict, svg_string=None):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.graphics import renderPDF
        from svglib.svglib import svg2rlg
        import io
        import os
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # 1. LOGO (Haut Gauche)
        # Gestion sécurisée: Si échec, on affiche un texte rouge
        try:
             # Try decoding as-is, then with padding fix if needed
             try:
                 logo_data = base64.b64decode(LOGO_B64, validate=True)
             except:
                 b64 = LOGO_B64
                 b64 += "=" * ((4 - len(b64) % 4) % 4)
                 logo_data = base64.b64decode(b64)
             
             logo_io = io.BytesIO(logo_data)
             
             from reportlab.lib.utils import ImageReader
             img = ImageReader(logo_io)
             iw, ih = img.getSize()
             aspect = ih / float(iw)
             draw_w = 150
             draw_h = draw_w * aspect
             c.drawImage(img, 40, height - 40 - draw_h, width=draw_w, height=draw_h, mask='auto', preserveAspectRatio=True)
             
        except Exception as e:
            c.setFont("Helvetica-Oblique", 10)
            c.setFillColor("red")
            c.drawString(40, height - 60, f"[Erreur Logo: {str(e)}]")
            c.setFillColor("black")

        # 2. TITRE & INFOS
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, height - 100, f"Fiche Technique : {data_dict.get('ref_id', 'F1')}")
        
        c.setFont("Helvetica", 10)
        c.drawString(40, height - 120, f"Projet: {data_dict.get('project', {}).get('name', 'P')}")
        c.drawString(40, height - 135, f"Date: {datetime.datetime.now().strftime('%d/%m/%Y')}")

        # 3. CONTENU TEXTE (Simplifié pour robustesse)
        y_cursor = height - 160
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y_cursor, "1. Caractéristiques Principales")
        y_cursor -= 20
        c.setFont("Helvetica", 10)
        
        # Info Block
        infos = [
            f"Dimensions: {data_dict.get('width_dorm', 0)} x {data_dict.get('height_dorm', 0)} mm",
            f"Type: {data_dict.get('mat_type', 'PVC')} - {data_dict.get('pose_type', '-')}",
            f"Couleur: Int {data_dict.get('col_in','-')} / Ext {data_dict.get('col_ex','-')}",
            f"Dormant: {data_dict.get('frame_thig', 70)} mm",
            f"Ailettes: {data_dict.get('fin_val', 0)} mm"
        ]
        
        for line in infos:
            c.drawString(50, y_cursor, f"• {line}")
            y_cursor -= 15
            
        y_cursor -= 20
        
        # 4. SCHÉMA (SVG)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y_cursor, "2. Plan Technique")
        y_cursor -= 20
        
        if svg_string:
            try:
                # Convert string to BytesIO for svglib
                svg_file = io.BytesIO(svg_string.encode('utf-8'))
                drawing = svg2rlg(svg_file)
                
                # Scale logic
                d_width = drawing.width
                d_height = drawing.height
                scale = min(500 / d_width, 300 / d_height)
                drawing.scale(scale, scale)
                
                renderPDF.draw(drawing, c, 40, y_cursor - (d_height * scale))
                y_cursor -= (d_height * scale + 40)
            except Exception as e:
                c.setFillColor("red")
                c.drawString(40, y_cursor, f"[Erreur Schéma SVG: {str(e)}]")
                c.setFillColor("black")
                y_cursor -= 40
        else:
            c.drawString(40, y_cursor, "[Aucun schéma disponible]")
            y_cursor -= 40

        # Disclaimer
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColor("gray")
        c.drawCentredString(width/2, 30, "Document généré automatiquement - Miroiterie Yerroise")
        
        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer
    except Exception as e:
        # GLOBAL CRASH CATCHER -> Return text error in a buffer to download as txt? 
        # Or better: return None and let UI handle it?
        # User requested: "Si une image échoue... le PDF doit quand même se générer".
        # This global catch matches unforeseen errors.
        print(f"CRITICAL PDF ERROR: {e}") 
        return None

# --- CSS MOBILE & PRINT FIX ---
st.markdown("""
<style>
    /* Force sidebar behavior on mobile */
    @media (max-width: 768px) {
        /* Only force full width when OPEN */
        section[data-testid="stSidebar"][aria-expanded="true"] {
            min-width: 100vw !important;
            width: 100vw !important;
            height: 100vh !important;
            z-index: 99999 !important;
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
        }
        
        /* Force hide when CLOSED (if standard behavior fails) */
        section[data-testid="stSidebar"][aria-expanded="false"] {
            margin-left: -110vw !important;
            width: 0 !important;
        }

        /* Fix overlapping content if needed */
        .main .block-container {
            max-width: 100% !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
    }
    /* General print fix */
    @media print {
        [data-testid="stSidebar"] { display: none; }
        .stApp { margin: 0; padding: 0; }
        header { display: none; }
    }
    
    /* Move Sidebar Button down on Mobile to avoid header overlap */
    @media (max-width: 768px) {
        /* OPEN BUTTON (When sidebar is closed) */
        [data-testid="collapsedControl"] {
            top: 80px !important;
            left: 10px !important;
            z-index: 1000000 !important;
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        
        /* CLOSE BUTTON (When sidebar is open) - Target the SVG/Button container inside sidebar */
        section[data-testid="stSidebar"] button {
             top: 80px !important; /* Force it down */
        }
        
        /* Alternatively, push the entire Sidebar Header down */
        section[data-testid="stSidebar"] > div > div:first-child {
             margin-top: 60px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION CHEMINS (GLOBAL) ---
# Correction pour déploiement Cloud : Chemin relatif "assets"
# --- CONFIGURATION CHEMINS (GLOBAL) ---
# Correction pour déploiement Cloud : Chemin relatif "assets"
current_dir = os.path.dirname(os.path.abspath(__file__))
ARTIFACT_DIR = os.path.join(current_dir, "assets")

# ==============================================================================


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
    
    # Ensure mode_module exists immediately
    if 'mode_module' not in st.session_state:
        st.session_state['mode_module'] = 'Menuiserie'
        
    # DELETED: Default F1 creation. 
    # User wants empty list on startup.
    # if not st.session_state['project']['configs']:
    #     default_data = serialize_config()
    #     add_config_to_project(default_data, "F1")

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
             # FLUSH BUTTON KEYS: catch anything with 'btn'
             if 'btn' in k:
                 continue
             # Keep old check just in case
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
        # MORE ROBUST FILTERING on load
        if isinstance(k, str) and ('btn' in k):
            continue
            
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

def render_top_navigation():
    """Affiche la navigation supérieure (Projet, Mode, Liste)."""
    
    # 1. Ligne Supérieure : Nom Projet & Imports
    c_proj, c_imp = st.columns([3, 1])
    
    with c_proj:
        # Style 'Title' for Project Name
        proj_name = st.text_input("Nom du Chantier", st.session_state['project']['name'], key="proj_name_top")
        if proj_name != st.session_state['project']['name']:
            st.session_state['project']['name'] = proj_name
            
    with c_imp:
        with st.popover("⚙️ Options"):
            st.markdown("### Import / Export")
            proj_data = json.dumps(st.session_state['project'], indent=2)
            raw_name = st.session_state['project'].get('name', 'Projet_Fenetre')
            safe_name = "".join([c if c.isalnum() else "_" for c in raw_name])
            dl_name = f"{safe_name}.json"
            
            st.download_button("Export (JSON)", proj_data, file_name=dl_name, mime="application/json")
            
            uploaded = st.file_uploader("Import JSON", type=['json'], key='uploader_json')
            if uploaded and st.button("📥 Charger le Projet"):
                 try:
                    data = json.load(uploaded)
                    if 'configs' in data:
                        st.session_state['project'] = data
                        st.session_state['active_config_id'] = None
                        st.toast("Projet importé avec succès !")
                        st.rerun()
                 except Exception as e:
                    st.error(f"Erreur : {e}")

    st.markdown("---")
    
    # 2. Ligne Navigation : Mode & Liste Configs
    c_mode, c_list = st.columns([1, 2])
    
    with c_mode:
        # MODE SWITCH
        nav_options = ["Menuiserie", "Habillage"]
        current_mode = st.session_state.get('mode_module', 'Menuiserie')
        
        # Ensure valid
        if current_mode not in nav_options: current_mode = "Menuiserie"
        
        user_mode = st.radio("Module", nav_options, index=nav_options.index(current_mode), horizontal=True, label_visibility="collapsed", key="nav_mode_top")
        
        if user_mode != current_mode:
            st.session_state['mode_module'] = user_mode
            st.rerun()
            
    with c_list:
        configs = st.session_state['project']['configs']
        
        # Filter configs by mode? User says "Si menuiserie cochée... liste menuiserie".
        # We need 'config_type' in data. 
        # Existing configs might not have it. Default to 'Menuiserie'.
        # We'll filter the dropdown.
        
        # V74 FIX: Unified List (User Request)
        # Show ALL configs regardless of type, chronologically.
        filtered_configs = configs 
        
        if not filtered_configs:
            options = {}
        else:
            # Show Type in label for clarity? e.g. "F1 (Menuiserie)" or just "F1"
            # User example: "F1, H1, H2, F2"
            options = {c['id']: f"{c['ref']}" for c in filtered_configs}
            
        # Selectbox for OPENING
        # We use a placeholder "Sélectionner..." to allow re-selecting same item?
        # Or just standard selectbox.
        
        if options:
            # V74 FIX: Handle pending selection (conflict avoidance)
            if 'pending_new_id' in st.session_state:
                target_id = st.session_state.pop('pending_new_id')
                if target_id in options:
                    st.session_state['mgr_sel_id'] = target_id
            
            if 'mgr_sel_id' not in st.session_state or st.session_state['mgr_sel_id'] not in options:
                st.session_state['mgr_sel_id'] = list(options.keys())[0]
                
            if 'mgr_sel_id' not in st.session_state or st.session_state['mgr_sel_id'] not in options:
                st.session_state['mgr_sel_id'] = list(options.keys())[0]
                
            c_l_sel, c_l_btn = st.columns([2, 1])
            sel_id = c_l_sel.selectbox(
                "Configurations Enregistrées", 
                options.keys(), 
                format_func=lambda x: options[x], 
                key='mgr_sel_id', 
                label_visibility="collapsed"
            )
            
            with c_l_btn:
                 # STATE MACHINE FOR CONFIRMATION
                 # Keys: 'confirm_action': 'open' | 'delete' | None
                 #       'confirm_target_id': id
                 
                 # Helper to clear state
                 def clear_confirm():
                     st.session_state.pop('confirm_action', None)
                     st.session_state.pop('confirm_target_id', None)
                     
                 # Check if we are in confirmation mode for THIS selected item (or generic)
                 current_action = st.session_state.get('confirm_action')
                 target_id = st.session_state.get('confirm_target_id')
                 
                 if current_action and target_id == sel_id:
                     # SHOW CONFIRMATION UI REPLACING BUTTONS
                     ref_name = options.get(target_id, "???")
                     if current_action == 'open':
                         # FIXED: Proper newline for Streamlit MD/Info
                         msg = f"⚠️ **Ouvrir '{ref_name}' ?**\n\n(Toutes modifications non sauvegardées seront perdues)"
                     else:
                         msg = f"🗑️ **Supprimer '{ref_name}' ?**\n\n(Cette action est irréversible)"
                         
                     st.info(msg) # Use Info or Warning to make it distinct
                     cc_yes, cc_no = st.columns(2)
                     if cc_yes.button("✅ OUI", use_container_width=True, key="btn_yes"):
                         target = next((c for c in configs if c['id'] == target_id), None)
                         if current_action == 'open' and target:
                             deserialize_config(target['data'])
                             st.session_state['active_config_id'] = target['id']
                             st.session_state['ref_id'] = target['ref']
                             st.session_state['mode_module'] = target['data'].get('mode_module', 'Menuiserie')
                             st.toast(f"Ouverture de '{target['ref']}'...")
                             clear_confirm()
                             st.rerun()
                         elif current_action == 'delete':
                             delete_config_from_project(target_id)
                             st.toast(f"Suppression de '{ref_name}' effectuée.")
                             # If deleted, select another one? Handled by next render.
                             clear_confirm()
                             st.rerun()
                             
                     if cc_no.button("❌ NON", use_container_width=True, key="btn_no"):
                         clear_confirm()
                         st.rerun()
                         
                 else:
                     # STANDARD BUTTONS
                     cb_open, cb_del = st.columns(2)
                     if cb_open.button("📂 Ouvrir", use_container_width=True, help="Ouvrir (Perd les modifs non sauvegardées)"):
                        st.session_state['confirm_action'] = 'open'
                        st.session_state['confirm_target_id'] = sel_id
                        st.rerun()
                        
                     if cb_del.button("🗑️ Suppr.", use_container_width=True, help="Supprimer définitivement"):
                        st.session_state['confirm_action'] = 'delete'
                        st.session_state['confirm_target_id'] = sel_id
                        st.rerun()
                        
    # 3. Active Status Bar 
                 
    # 3. Active Status Bar
    active_id = st.session_state.get('active_config_id')
    active_ref = st.session_state.get('ref_id', 'Nouveau')
    
    if active_id:
        st.caption(f"✏️ **Édition en cours :** {active_ref} (Enregistré)")
    else:
        st.caption(f"✨ **Nouveau fichier :** {active_ref} (Non enregistré)")


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
        # Retrieve Traverse Thickness (Default 0 if new/legacy, but UI forces default)
        # Safely default to 0 if missing, to match old logic, but UI sets it to dormant.
        # Check UI initialization to be sure, or here.
        trav_th = int(node.get('traverse_thickness', 0))
        
        # Check substrings because radio value contains extra text
        if "Horizontale" in node['split_type']:
            # Split value is height of the top/left child
            h1 = node['split_value']
            # h2 is remaining height MINUS traverse thickness
            # Ensure we don't go negative
            h2 = max(0, current_h - h1 - trav_th)
            
            flat_zones.extend(flatten_tree(node['children'][0], current_x, current_y, current_w, h1))
            # Offset second child by h1 + thickness
            flat_zones.extend(flatten_tree(node['children'][1], current_x, current_y + h1 + trav_th, current_w, h2))
        else: # Verticale
            # Split value is width of the top/left child
            w1 = node['split_value']
            w2 = max(0, current_w - w1 - trav_th)
            
            flat_zones.extend(flatten_tree(node['children'][0], current_x, current_y, w1, current_h))
            # Offset second child by w1 + thickness
            flat_zones.extend(flatten_tree(node['children'][1], current_x + w1 + trav_th, current_y, w2, current_h))
    return flat_zones

# --- HELPER: AUTO-INCREMENT REFERENCE (GLOBAL) ---
def get_next_project_ref():
    """
    Parcourt toutes les configurations du projet pour trouver le prochain numéro de repère disponible.
    S'harmonise entre Menuiserie et Habillage.
    Format par defaut: "Repère N"
    """
    import re
    max_num = 0
    pattern = re.compile(r'(\d+)$')
    
    # 1. Check existing configs in project
    if 'project' in st.session_state and 'configs' in st.session_state['project']:
        for cfg in st.session_state['project']['configs']:
            ref = cfg.get('ref', '')
            match = pattern.search(ref)
            if match:
                try:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
                except:
                    pass
                    
    # 2. Check current active input (to avoid collision if user is typing)
    # Actually, we want to suggest the NEXT available.
    
    return f"Repère {max_num + 1}"

def get_next_ref(current_ref):
    """
    Incrémente la partie numérique d'une référence spécifique (Locale).
    Utilisé si on veut incrémenter par rapport à ce qu'on vient de saisir.
    MAIS le client veut une harmonisation globale.
    """
    return get_next_project_ref() # OVERRIDE TO USE GLOBAL LOGIC

# --- HELPER: GENERATION DU SVG (PARTIE 3 - CUSTOM PROFILES) ---
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
        if p['traverses'] >= 1:
            # V73 FIX: Allow user to edit Thickness of Petit Bois
            p['epaisseur_traverse'] = st.number_input("Épaisseur Traverse (mm)", 10, 100, 20, step=5, key=f"{key_prefix}_eptrav")
            
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

            # TRAVERSE THICKNESS (New V22)
            # Default to Dormant Thickness if not set
            def_th = st.session_state.get('frame_thig', 70)
            if 'traverse_thickness' not in node:
                node['traverse_thickness'] = def_th
                
            node['traverse_thickness'] = st.number_input(
                "Épaisseur Traverse (mm)", 
                min_value=0, max_value=200, value=int(node['traverse_thickness']), step=5,
                key=f"{prefix}_trav_th"
            )
    
            # Recursively render children INSIDE this expander box
            if "Verticale" in node['split_type']:
                render_node_ui(node['children'][0], node['split_value'], h_ref, level + 1, counter)
                render_node_ui(node['children'][1], w_ref - node['split_value'], h_ref, level + 1, counter)
            else: # horizontal
                render_node_ui(node['children'][0], w_ref, node['split_value'], level + 1, counter)
                render_node_ui(node['children'][1], w_ref, h_ref - node['split_value'], level + 1, counter)
def reset_config(rerun=True):
    # FIXED V73: Do NOT clear everything (keeps Project, Session, Selection)
    # Only clear config-related keys
    # V74: Preserve 'mode_module' to stay in current context
    # V75: REMOVE 'active_config_id'. Reset = New.
    keys_keep = ['project', 'mgr_sel_id', 'uploader_json', 'mode_module']
    
    # SAFE ITERATION: list(keys)
    keys_to_del = [k for k in list(st.session_state.keys()) if k not in keys_keep]
    for k in keys_to_del:
        del st.session_state[k]
    
    current_mode = st.session_state.get('mode_module', 'Menuiserie')
    
    # Default Values based on Mode
    # GLOBAL HARMONIZATION: Always use next available Repère
    st.session_state['ref_id'] = get_next_project_ref()
    
    st.session_state['qte_val'] = 1
    
    # Menuiserie Defaults (Only set if in Menuiserie or General Reset? 
    # Setting them is harmless as they are keys used only by Menuiserie widgets usually,
    # except ref/qte which are shared).
    
    # Matériau & Pose
    st.session_state['mat_type'] = "PVC"
    st.session_state['frame_thig'] = 70
    st.session_state['proj_type'] = "Rénovation"
    st.session_state['pose_type'] = "Pose en rénovation (R)" # Default for Reno
    
    # Ailettes / Seuil
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
    
    # HABILLAGE DEFAULTS (Explicit Reset to fix persistence)
    # Default is Index 0 of PROFILES_DB -> "m1"
    st.session_state['hab_model_selector'] = "m1"
    st.session_state['hab_length_input'] = 3000
    
    # Explicitly reset dimensions for default model (m1) to force UI update
    # even if widget key 'hab_m1_A' remains the same.
    st.session_state['hab_m1_A'] = 100
    
    # Clear any previous 'hab_m1_A' etc ??
    # Deletion loop above handles that.
    
    # Allow external control of rerun
    if rerun:
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
            ep_trav = params.get('epaisseur_traverse', 20) # V73 FIX: Used input value
            
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
            
            # --- COTE HAUTEUR TRAVERSE (V74 FIX) ---
            # Dessiner une cote visible pour la hauteur de traverse
            # Position: Droite ou Gauche de la vitre
            # On la met dans le vitrage (discret mais lisible)
            
            # Calcul Hauteur (Axe)
            ltx = lx + lw - 30 
            if pos_trav == "Sur mesure (du bas)":
               # Cote depuis le bas
               draw_dimension_line(svg, ltx, y_center, ltx, ly+lh, h_custom, "", -10, "V", font_size=16, z_index=z_eff+10)
            else:
               # Cote centrée (relative au haut ?) ou juste marquer "H/2"
               # On affiche la cote réelle depuis le bas pour info
               h_reel_bas = (ly+lh) - y_center
               draw_dimension_line(svg, ltx, y_center, ltx, ly+lh, h_reel_bas, "", -10, "V", font_size=16, z_index=z_eff+10)

            
        else:
            remp_glob = params.get('remplissage_global', 'Vitrage')
            # DEBUG removed
            col_g = "#F0F0F0" if remp_glob == "Panneau" else config_global['color_glass']
            # z_eff = 50
            draw_rect(svg, lx, ly, lw, lh, col_g, "black", 1, z_eff+1)
            
            if nb_trav > 1:
                ep_trav = params.get('epaisseur_traverse', 20) # V73 FIX for multiple traverses
                # Simple distribution
                # If N traverses, N+1 spaces? 
                # Calculation: Total H. Space = (TotalH - N*Ep)/ (N+1).
                # Current code: section_h = lh / (nb_trav + 1). This assumes center-lines.
                # Let's keep simple distribution but use ep_trav for the rect height.
                
                section_h = lh / (nb_trav + 1)
                for k in range(1, nb_trav + 1):
                    ty = ly + (section_h * k) - (ep_trav/2)
                    draw_rect(svg, lx, ty, lw, ep_trav, c_frame, "black", 1, z_eff+2)

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
        # V74 FIX: Center handle EXACTLY on the Sash Profile (Not Frame)
        # Frame (Dormant) = 24mm (adj). 
        # Total visible (Dormant + Sash) = 55mm (vis_ouvrant).
        # Sash Profile Width = 55 - 24 = 31mm.
        # Center of Sash = 24 + (31/2) = 39.5mm.
        
        handle_offset_edge = 39.5 
        
        if sens == 'TG': x_h_vis = x + w - handle_offset_edge
        else: x_h_vis = x + handle_offset_edge
            
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
        
        # VISUAL FIX: Reduce central thickness (Battement)
        # Standard vis_ouvrant is 55. If sides are 55, center is 110 (Too thick).
        # We cheat by using a smaller visual for the central stiles.
        vis_middle = 35 # 35+35 = 70mm central block (vs 110mm)
        
        # Left Sash
        draw_rect(svg, x+adj, y+adj, w_vtl-adj, h-2*adj, c_frame, "black", 1, z_base) 
        # Right Sash
        draw_rect(svg, x+w_vtl, y+adj, w_vtl-adj, h-2*adj, c_frame, "black", 1, z_base) 
        
        # Intérieurs
        # LEFT SASH: Left=55 (Normal), Right=35 (Thinner)
        # Width of glass = SashWidth - LeftProfile - RightProfile
        # SashWidth = w_vtl - adj (approx, due to rect logic above).
        # Wait, draw_leaf_interior draws RELATIVE to the provided box.
        # But here we provide explicit coordinates.
        
        # Canvas for Left Interior:
        # X start: x + vis_ouvrant
        # Width: (w_vtl) - vis_ouvrant (left) - vis_middle (right)
        # Note: w_vtl is the half-width.
        
        # Visual correction:
        draw_leaf_interior(x+vis_ouvrant, y+vis_ouvrant, w_vtl - vis_ouvrant - vis_middle, h-2*vis_ouvrant)
        
        # RIGHT SASH: Left=35 (Thinner), Right=55 (Normal)
        draw_leaf_interior(x+w_vtl+vis_middle, y+vis_ouvrant, w_vtl - vis_middle - vis_ouvrant, h-2*vis_ouvrant)
        
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
            # V74 FIX: Centered on vis_middle (35mm)
            # x + w_vtl is the split. Right sash starts there.
            # Its left stile is vis_middle (35). Center is 17.5.
            x_h_vis = (x + w_vtl) + 17.5 
        else:
            # Principal Gauche -> Poignée à Droite du vantail gauche (Central)
            # V74 FIX: Centered on vis_middle (35mm)
            # x + w_vtl is the split. Left sash ends there.
            # Its right stile is vis_middle (35). Center is 17.5 from edge.
            x_h_vis = (x + w_vtl) - 17.5
            
        if hp_val > 0:
            draw_handle_icon(svg, x_h_vis, y_h_vis, z_index=z_base+8)
            
            # HANDLE ON SECONDARY SASH (VS) - Symmetric
            if is_princ_right:
                # VS is Left Sash. Handle on Right side of VS (Central).
                # Same X logic as "Principal Gauche" handle.
                x_h_vs = (x + w_vtl) - 17.5
                draw_handle_icon(svg, x_h_vs, y_h_vis, z_index=z_base+8)
            else:
                # VS is Right Sash. Handle on Left side of VS (Central).
                x_h_vs = (x + w_vtl) + 17.5
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
        # Top Rail center:
        # y start of frame. y frame interior = y+24.
        # Sash top rail = 31mm. Center = 24 + 15.5 = 39.5.
        
        h_soufflet_x = x + w/2
        h_soufflet_y = y + 39.5
        
        # User wants Horizontal, Tail to the Right.
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
        # Offset from Left Edge = 39.5mm (Dormant 24 + Half Sash 15.5)
        x_h_c_left = x + 39.5
        draw_handle_icon(svg, x_h_c_left, y_handle_c, z_index=z_base+12)
        
        # Handle Right Sash (on its Right Stile - Jamb Side)
        # Offset from Right Edge = 39.5mm
        x_h_c_right = (x + w) - 39.5
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
        "defaults": {"A": 100},
        "segments": ["A"]
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
        # STANDARD MODELS LOGIC (M1..M10)
        # Re-initialize points to ensure correct start for shapes like U or L
        points = [] 
        
        # Load params
        defaults = PROFILES_DB[type_p]["defaults"]
        P = lambda k: inputs.get(k, defaults.get(k, 0))
        
        if type_p == "m1": # Plat (A)
             A = P("A")
             points = [(0,0), (A, 0)]

        elif type_p == "m2": # Cornière Simple (A, B) - L Shape
             # Vertical A (Down), Horizontal B (Right)
             A = P("A"); B = P("B")
             points = [(0,0), (0, A), (B, A)]

        elif type_p == "m3": # Cornière Complexe (A, B, A1) - Ridge/Roof
             A = P("A"); B = P("B"); A1 = P("A1")
             # Peak at (0,0). A is Left leg, B is Right leg. 
             # A1 is internal angle.
             # Angle from vertical = A1/2
             rad = math.radians(A1/2.0)
             # Left Point (negative X, positive Y as down)
             p_left = (-A * math.sin(rad), A * math.cos(rad))
             # Right Point
             p_right = (B * math.sin(rad), B * math.cos(rad))
             points = [p_left, (0,0), p_right]

        elif type_p == "m4": # Profil en U (A, B, C) - Bucket
             # Flange A (Up), Web B (Right), Flange C (Up)
             A = P("A"); B = P("B"); C = P("C")
             # Start Top-Left
             points = [(0, -A), (0,0), (B, 0), (B, -C)]

        elif type_p == "m5": # Profil en Z (A, B, C) - Step
             # A(Right), B(Down), C(Right)
             A = P("A"); B = P("B"); C = P("C")
             points = [(0,0), (A, 0), (A, B), (A+C, B)]
             
        elif type_p == "m6": # Z Complexe / Omega (A,B,C,D, A1,A2,A3)
             # Use Turtle for complex shapes
             # Start (0,0). Right.
             curr_x, curr_y = 0, 0
             curr_ang = 0 # Right
             points = [(0,0)]
             
             # Segment A (Right)
             A = P("A")
             curr_x += A
             points.append((curr_x, curr_y))
             
             # Turn A1 (Relative). A1 internal?
             # If Z-like: A(Right), B(Slope Down).
             # Angle A1.
             # Turn = 180 - A1?
             # Let's assume standard Turtle:
             # A -> Turn -> B -> Turn -> C -> Turn -> D
             B=P("B"); C=P("C"); D=P("D")
             A1=P("A1"); A2=P("A2"); A3=P("A3")
             
             # Helper Turtle
             def moved(l, ang_deg):
                 fl_x = points[-1][0] + l * math.cos(math.radians(ang_deg))
                 fl_y = points[-1][1] + l * math.sin(math.radians(ang_deg))
                 points.append((fl_x, fl_y))
                 return ang_deg

             # A done. Current Dir 0.
             # Turn 1: 
             # If A1=100. Turn 80 deg. (Down-Right)
             curr_ang += (180 - A1)
             curr_ang = moved(B, curr_ang)
             
             # Turn 2:
             curr_ang += (180 - A2)
             curr_ang = moved(C, curr_ang)
             
             # Turn 3: 
             curr_ang += (180 - A3)
             curr_ang = moved(D, curr_ang)

        elif type_p == "m7": # Cornière 3 Plis (A, B, C, A1)
             # A(Hem), B(Leg), C(Leg)?
             # Or A(Leg), B(Leg), C(Hem)?
             # Let's assume: A (Small return), Angle A1, B (Leg 1), 90, C (Leg 2).
             # Standard "3 Pli": Return -> Leg -> Leg.
             A=P("A"); B=P("B"); C=P("C"); A1=P("A1")
             points = [(0,0)]
             # A (Return In/Up?)
             # Let's do B and C as Main L.
             # B (Vertical), C (Horizontal).
             # A is Return on B.
             # Start A.
             # Point 0.
             # Draw A. Turn A1. Draw B. Turn 90. Draw C.
             # Direction?
             # Start Up-Right.
             curr_ang = -90 # Up
             curr_x, curr_y = 0, 0
             
             # A (Return)
             # Maybe starts horizontal in?
             # Let's assume A is the small text.
             # Draw: A -> Turn -> B -> Turn -> C.
             # A (Right). Turn. B (Down). Turn. C (Right).
             # If A1=90.
             points = [(0,0), (A,0)] # A Right
             # Turn A1 (Internal).
             curr_ang = 0 + (180-A1)
             vx = math.cos(math.radians(curr_ang)); vy = math.sin(math.radians(curr_ang))
             p2 = (points[-1][0]+vx*B, points[-1][1]+vy*B)
             points.append(p2)
             # Turn 90 (Standard Cornière)
             # Assuming B to C is 90.
             curr_ang += 90 
             vx = math.cos(math.radians(curr_ang)); vy = math.sin(math.radians(curr_ang))
             p3 = (points[-1][0]+vx*C, points[-1][1]+vy*C)
             points.append(p3)

        elif type_p == "m8": # Couverine (A, B, C, A1, A2)
             # A(Drop), B(Top), C(Drop).
             # A (Up), B (Right), C (Down) -> Inverted U shape.
             A=P("A"); B=P("B"); C=P("C"); A1=P("A1"); A2=P("A2")
             # Start Bottom-Left.
             points = [(0, A)] # Start at A down
             # Draw Up A.
             points.append((0,0))
             # Turn A1. Draw B.
             # Curr Dir Up (-90).
             # A1 internal. Turn = 180-A1.
             # If A1=90 -> Right.
             curr_ang = -90 + (180-A1)
             vx=math.cos(math.radians(curr_ang)); vy=math.sin(math.radians(curr_ang))
             p2 = (points[-1][0]+vx*B, points[-1][1]+vy*B)
             points.append(p2)
             # Turn A2. Draw C.
             curr_ang += (180-A2)
             vx=math.cos(math.radians(curr_ang)); vy=math.sin(math.radians(curr_ang))
             p3 = (points[-1][0]+vx*C, points[-1][1]+vy*C)
             points.append(p3)

        elif type_p == "m9": # Bavette (A, B, C, A1, A2)
            # A(Flat), B(Slope), C(Drop)? 
            # Or A(Up), B(Slope), C(Vertical)?
            # Bavette: A horizontal. B Slope Down. C Vertical Down.
            A=P("A"); B=P("B"); C=P("C"); A1=P("A1"); A2=P("A2")
            points = [(0,0), (A,0)] # A Right
            # Turn A1 (Obtuse usually, >90)
            # 0 -> Turn. 180-A1? (Down)
            # If A1=135. Turn=45 (Down Right).
            curr_ang = 0 + (180-A1)
            vx=math.cos(math.radians(curr_ang)); vy=math.sin(math.radians(curr_ang))
            p2 = (points[-1][0]+vx*B, points[-1][1]+vy*B)
            points.append(p2)
            # Turn A2. C Vertical?
            # A2 usually 90 or similar.
            curr_ang += (180-A2)
            vx=math.cos(math.radians(curr_ang)); vy=math.sin(math.radians(curr_ang))
            p3 = (points[-1][0]+vx*C, points[-1][1]+vy*C)
            points.append(p3)

        elif type_p == "m10": # Z Rejet (A, B, C, D, E, A1)
            # A, B, C, D, E
            # A(Flat), B(Up/Down?), C(Rejet), D(Vertical), E(Return)
            # Standard: A Right. B Vertical Up. C Slope Out. D Vertical Up. E Return.
            # OR A Right. B Vertical Down. C Slope. D Vert. E Return.
            # Let's look at schema logic from before.
            # A, B, C, D...
            # Arbitrary implementation based on typical "Z Rejet":
            # A(Fixing), B(Offset), C(Rejet), D(Face), E(Return).
            inputs_keys = inputs.keys()
            # Generic chain if possible? No, need angles.
            # Let's do simple orthogonal chain A-B-C-D-E if angles not explicit?
            # A1 is angle.
            points = [(0,0)]
            # Draw A Right
            A=P("A"); points.append((A,0))
            # B Down
            B=P("B"); points.append((A,B))
            # C Slope (Rejet). Angle A1.
            # If A1=135. Down -> Out.
            C=P("C"); A1=P("A1")
            curr_ang = 90 + (180-A1)
            vx=math.cos(math.radians(curr_ang)); vy=math.sin(math.radians(curr_ang))
            p2 = (points[-1][0]+vx*C, points[-1][1]+vy*C)
            points.append(p2)
            # D Down
            D=P("D")
            p3 = (points[-1][0], points[-1][1]+D)
            points.append(p3)
            # E Left (Return)
            E=P("E")
            p4 = (points[-1][0]-E, points[-1][1])
            points.append(p4)
            
        else:
            # Fallback
            points = [(0,0), (100,0), (100,100)]

    # Normalize coordinates to fit in View
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    w_shape = max_x - min_x
    h_shape = max_y - min_y
    
    # Scale to fill portion of SVG (Zoom In)
    target_size = 350 
    
    # SCALING FIX: Increase minimum divisor to 250 to allow "growth" perception 
    # for small items (100->250mm). Items > 250mm will be fitted to target_size.
    ref_dim = max(w_shape, h_shape, 250) 
    scale = target_size / ref_dim
        
    # 1. Calculate Scaled Points relative to (0,0) first
    # min_x, min_y are the top-left of the shape in logical coords
    scaled_points = []
    for p in points:
        nx = (p[0] - min_x) * scale
        ny = (p[1] - min_y) * scale
        scaled_points.append((nx, ny))
        
    # 2. Create Back Face (Depth)
    # Increase Depth Vector to look "long enough" even when zoomed
    # Maybe proportional? No, fixed but larger looks better for "Profile Visual"
    depth_x, depth_y = 200, -100 # Increased from 150,-80
    back_points = []
    for p in scaled_points:
        back_points.append((p[0] + depth_x, p[1] + depth_y))
        
    # 3. AUTO-CENTERING
    # Collect all visual points
    all_x = [p[0] for p in scaled_points] + [p[0] for p in back_points]
    all_y = [p[1] for p in scaled_points] + [p[1] for p in back_points]
    
    min_gx, max_gx = min(all_x), max(all_x)
    min_gy, max_gy = min(all_y), max(all_y)
    
    w_draw = max_gx - min_gx
    h_draw = max_gy - min_gy
    
    # Center in 700x500
    offset_x = (700 - w_draw) / 2 - min_gx
    offset_y = (500 - h_draw) / 2 - min_gy
    
    # Apply Offset
    scaled_points = [(p[0] + offset_x, p[1] + offset_y) for p in scaled_points]
    back_points = [(p[0] + offset_x, p[1] + offset_y) for p in back_points]
    
    # DRAW SVG
    svg_els = []
    style_line = f'stroke="black" stroke-width="2" fill="none"'
    path_back = "M " + " L ".join([f"{p[0]},{p[1]}" for p in back_points])
    svg_els.append(f'<path d="{path_back}" stroke="#999" stroke-width="1" fill="none" stroke-dasharray="4,4" />')
    
    for p1, p2 in zip(scaled_points, back_points):
        svg_els.append(f'<line x1="{p1[0]}" y1="{p1[1]}" x2="{p2[0]}" y2="{p2[1]}" stroke="#555" stroke-width="1" />')
    
    if len(scaled_points) > 0:
        p_front = scaled_points[0]
        p_back = back_points[0]
        t = 0.8
        lbl_x = p_front[0] + (p_back[0] - p_front[0]) * t
        lbl_y = p_front[1] + (p_back[1] - p_front[1]) * t - 40 
        svg_els.append(f'<text x="{lbl_x}" y="{lbl_y}" font-family="Arial" font-size="14" fill="#335c85" font-weight="bold" text-anchor="middle">L={length}</text>')
        
    path_front = "M " + " L ".join([f"{p[0]},{p[1]}" for p in scaled_points])
    svg_els.append(f'<path d="{path_front}" {style_line} stroke="#000" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />')

    # Dimensions Labels
    # Calculate Centroid for Outward Orientation
    if scaled_points:
        cx = sum([p[0] for p in scaled_points]) / len(scaled_points)
        cy = sum([p[1] for p in scaled_points]) / len(scaled_points)
    else:
        cx, cy = 0, 0

    for i in range(len(scaled_points)-1):
        p1 = scaled_points[i]; p2 = scaled_points[i+1]
        mx = (p1[0]+p2[0])/2; my = (p1[1]+p2[1])/2
        dx = p2[0]-p1[0]; dy = p2[1]-p1[1]
        l = math.sqrt(dx*dx+dy*dy)
        if l==0: l=1
        
        # Initial Normal (Rotated -90 deg)
        nx = dy/l; ny = -dx/l
        
        # Check Orientation against Centroid (Outward Check)
        vec_out_x = mx - cx
        vec_out_y = my - cy
        dot = nx * vec_out_x + ny * vec_out_y
        
        # If pointing Inward (Dot < 0), Flip
        if dot < 0:
            nx = -nx; ny = -ny
            
        # Offset "Close" (User request: very close)
        offset = 4 # Reduced from 10
        
        lx = mx + nx*offset; ly = my + ny*offset
        
        # Smart Anchoring based on Direction
        anchor="middle"; baseline="middle"
        if abs(nx) > abs(ny): # Horizontal-ish force
            if nx > 0: anchor="start"; lx += 3 # Right
            else: anchor="end"; lx -= 3 # Left
        else: # Vertical-ish force
            if ny > 0: baseline="hanging"; ly += 3 # Down
            else: baseline="baseline"; ly -= 3 # Up
        
        try:
             # Handle labels for m11 (Sur Mesure)
             if type_p == "m11":
                 seg_char = chr(65 + i) # A, B, C...
                 txt = seg_char 
             else:
                 txt = PROFILES_DB[type_p]["params"][i]
                 
             svg_els.append(f'<text x="{lx}" y="{ly}" font-family="Arial" font-size="14" fill="red" font-weight="bold" text-anchor="{anchor}" dominant-baseline="{baseline}">{txt}</text>')
        except: pass

    # Face Labels
    max_len = -1; best_idx = 0
    if len(scaled_points) > 1:
        for i in range(len(scaled_points)-1):
            p1=scaled_points[i]; p2=scaled_points[i+1]
            l = math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
            if l > max_len: max_len=l; best_idx=i
        
        p1=scaled_points[best_idx]; p2=scaled_points[best_idx+1]
        mx=(p1[0]+p2[0])/2; my=(p1[1]+p2[1])/2
        dx=p2[0]-p1[0]; dy=p2[1]-p1[1]
        l=math.sqrt(dx*dx+dy*dy)
        if l==0: l=1
        nx=dy/l; ny=-dx/l
        
        f1_dist=130; f1_x=mx+nx*f1_dist; f1_y=my+ny*f1_dist # Face 2 (Top) - Further (90->130)
        f2_dist=90; f2_x=mx-nx*f2_dist; f2_y=my-ny*f2_dist # Face 1 (Bottom) - Further (60->90)
        style='font-family="Arial" font-size="12" fill="#666" font-style="italic" text-anchor="middle" dominant-baseline="middle"'
        svg_els.append(f'<text x="{f1_x}" y="{f1_y}" {style}>FACE 2</text>')
        svg_els.append(f'<text x="{f2_x}" y="{f2_y}" {style}>FACE 1</text>')

    final_svg = f'<svg viewBox="0 0 {w_svg} {h_svg}" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg" style="background-color: white; width: 100%; height: auto;">'
    final_svg += "".join(svg_els)
    final_svg += '</svg>'
    return final_svg

def get_html_download_link(content_html, filename, label):
    import base64
    b64 = base64.b64encode(content_html.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" download="{filename}" target="_blank" style="text-decoration:none; color:black; background-color:#f0f2f6; padding:8px 16px; border-radius:4px; border:1px solid #ccc;">📄 {label}</a>'

def render_habillage_main_ui(cfg):
    import datetime
    prof = cfg['prof']
    st.header(f"🧱 {prof['name']}") 
    
    dev = calc_developpe(cfg['key'], cfg['inputs'])
    
    c1, c2 = st.columns([2, 3])
    
    # Data Preparation
    exclude_keys = ['ref', 'qte', 'length', 'finition', 'epaisseur', 'couleur', 'modele']
    # Use HTML break for better readability in export
    dim_items = [f"<b>{k}</b> = {v}" for k,v in cfg['inputs'].items() if k not in exclude_keys]
    dim_str_export = "<br>".join(dim_items)
    dim_str_display = ", ".join([f"{k}={v}" for k,v in cfg['inputs'].items() if k not in exclude_keys])
    
    surface = (dev * cfg['length'] * cfg['qte']) / 1000000
    L_mm = cfg['length']
    qty = cfg['qte']
    
    with c1:
        st.subheader("Schéma de Principe")
        image_path = os.path.join(ARTIFACT_DIR, prof['image_key'])
        if os.path.exists(image_path):
            st.image(image_path, use_container_width=True)
        else:
            st.warning(f"Image non trouvée: {prof['image_key']}")
            st.caption(f"Chemin cherché: {image_path}") # Debug helper

        st.markdown("---")
        st.subheader("Informations Clés")
        
        st.metric("Développé Unitaire", f"{int(dev)} mm")
        st.markdown(f"**Quantité :** {qty}")
        st.markdown(f"**Dimensions :** {dim_str_display}")
        st.markdown(f"**Longueur :** {L_mm} mm")
        st.markdown(f"**Matière :** {cfg['finition']}")
        st.markdown(f"**Couleur :** {cfg['couleur']}")

    with c2:
        st.subheader("Visualisation 3D")
        svg = generate_profile_svg(cfg['key'], cfg['inputs'], cfg['length'], cfg['couleur'])
        st.markdown(f'''
        <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; background-color: white; text-align: center;">
            {svg}
        </div>
        ''', unsafe_allow_html=True)
        st.caption("Vue filaire 3D indicative.")
        
        st.download_button("🖼️ Télécharger SVG", svg, f"profil_{cfg['ref']}.svg", "image/svg+xml")

    st.markdown("---")
    st.subheader("Récapitulatif (Habillage)")
    
    col_table, col_export = st.columns([3, 1])
    
    df_hab = pd.DataFrame({
        "Libellé": ["Référence", "Modèle", "Quantité", "Dimensions", "Longueur", "Développé", "Surface Totale", "Matière", "Épaisseur", "Couleur"],
        "Valeur": [
            cfg['ref'], prof['name'], cfg['qte'], dim_str_display, f"{cfg['length']} mm", f"{dev} mm", 
            f"{surface:.2f} m²", cfg['finition'], cfg['epaisseur'], cfg['couleur']
        ]
    })

    with col_table:
        st.table(df_hab)
        
    with col_export:
        st.write("")
        st.write("")
        
        hab_data = {
            "ref": cfg['ref'], "modele": prof['name'], "qte": cfg['qte'],
            "dims": cfg['inputs'], "longueur": cfg['length'], "developpe": dev,
            "finition": cfg['finition'], "epaisseur": cfg['epaisseur'], "couleur": cfg['couleur']
        }
        json_hab = json.dumps(hab_data, indent=2, ensure_ascii=False)
        st.download_button("💾 Export JSON", json_hab, f"habillage_{cfg['ref']}.json", "application/json", use_container_width=True)

        import base64
        img_b64 = ""
        if os.path.exists(image_path):
             with open(image_path, "rb") as f:
                 img_b64 = base64.b64encode(f.read()).decode()
        
        html_report = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Fiche Technique - {prof['name']}</title>
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
            <style>
                body {{ font-family: 'Roboto', sans-serif; color: #333; line-height: 1.6; margin: 0; padding: 20px; background: #fff; }}
                .page-container {{ max-width: 210mm; margin: 0 auto; background: white; padding: 40px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
                .header {{ border-bottom: 3px solid #2c3e50; padding-bottom: 20px; margin-bottom: 40px; display: flex; justify-content: space-between; align-items: center; }}
                .header h1 {{ margin: 0; font-size: 24px; color: #2c3e50; text-transform: uppercase; letter-spacing: 1px; }}
                .header .ref {{ font-size: 14px; color: #7f8c8d; }}
                .main-grid {{ display: grid; grid-template-columns: 40% 55%; gap: 5%; margin-bottom: 40px; }}
                h2 {{ font-size: 18px; color: #34495e; border-left: 5px solid #3498db; padding-left: 10px; margin-bottom: 20px; clear: both; }}
                .schema-box {{ text-align: center; margin-bottom: 30px; border: 1px solid #eee; padding: 10px; border-radius: 4px; }}
                .info-box {{ background: #f8f9fa; padding: 20px; border-radius: 6px; font-size: 15px; }}
                .info-row {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; border-bottom: 1px solid #eee; padding-bottom: 4px; }}
                .info-row:last-child {{ border: 0; }}
                .label {{ font-weight: bold; color: #555; white-space: nowrap; margin-right: 15px; min-width: 100px; }}
                .dims-val {{ font-size: 16px; color: #2c3e50; text-align: left; }}
                .dims-row {{ justify-content: flex-start; gap: 20px; }}
                .visual-box {{ border: 1px solid #ddd; border-radius: 8px; padding: 10px; text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 400px; }}
                .visual-box svg {{ width: 100%; height: auto; max-height: 500px; display: block; margin: auto; }}
                table {{ width: 100%; border-collapse: collapse; font-size: 14px; margin-top: 20px; }}
                th {{ background: #2c3e50; color: white; padding: 12px; text-align: left; font-weight: 500; }}
                td {{ border-bottom: 1px solid #ddd; padding: 10px; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .footer {{ margin-top: 60px; text-align: center; font-size: 12px; color: #aaa; border-top: 1px solid #eee; padding-top: 20px; }}
                @media print {{ body {{ padding: 0; background: white; }} .page-container {{ box-shadow: none; padding: 0; max-width: none; }} @page {{ margin: 15mm; size: A4 portrait; }} }}
            </style>
        </head>
        <body>
            <div class="page-container">
                <div class="header">
                    <div>
                        <h1>Fiche Technique</h1>
                        <div style="font-size: 18px; margin-top: 5px; color: #3498db;">{prof['name']}</div>
                    </div>
                    <div class="ref" style="text-align: right;">
                        <div>RÉFÉRENCE CHANTIER</div>
                        <strong style="font-size: 18px; color: #000;">{cfg['ref']}</strong>
                        <div>{datetime.datetime.now().strftime('%d/%m/%Y')}</div>
                    </div>
                </div>
                
                <div class="main-grid">
                    <div>
                        <h2>Schéma de Principe</h2>
                        <div class="schema-box">
                             <img src="data:image/jpeg;base64,{img_b64}" style="max-width: 100%; max-height: 200px;">
                        </div>
                        <h2>Caractéristiques</h2>
                        <div class="info-box">
                            <div class="info-row"><span class="label">Quantité</span> <span>{qty}</span></div>
                            <div class="info-row"><span class="label">Longueur</span> <span>{L_mm} mm</span></div>
                            <div class="info-row"><span class="label">Développé</span> <span>{int(dev)} mm</span></div>
                            <div class="info-row"><span class="label">Matière</span> <span>{cfg['finition']}</span></div>
                            <div class="info-row"><span class="label">Couleur</span> <span>{cfg['couleur']}</span></div>
                            <div class="info-row"><span class="label">Épaisseur</span> <span>{cfg['epaisseur']}</span></div>
                            <div class="info-row dims-row" style="margin-top: 15px; border-top: 1px solid #ddd; padding-top: 10px;">
                                <span class="label">Dimensions</span> 
                                <span class="dims-val">{dim_str_export}</span>
                            </div>
                        </div>
                    </div>
                    <div>
                        <h2>Visualisation 3D</h2>
                        <div class="visual-box">
                            {svg}
                            <div style="margin-top: 15px; font-size: 12px; color: #999;">Vue filaire indicative</div>
                        </div>
                    </div>
                </div>
                
                <h2>Détails de Commande</h2>
                <table>
                    <thead><tr><th style="width: 40%;">Libellé</th><th>Valeur</th></tr></thead>
                    <tbody>
                        {''.join([f'<tr><td>{r[0]}</td><td>{r[1]}</td></tr>' for r in df_hab.values])}
                    </tbody>
                </table>
                <div class="footer">Document généré automatiquement via le Calculateur Menuiserie & Habillage.<br>Merci de vérifier les cotes avant validation définitive.</div>
            </div>
            <script>
                // Auto-print removed, purely manual now as per request to remove 'frame'.
            </script>
        </body>
        </html>
        """
        st.download_button("📄 Imprimer (PDF)", html_report, f"fiche_{cfg['ref']}.html", "text/html", use_container_width=True)

def render_habillage_form():
    """Renders the Sidebar inputs for Habillage and returns the config dict."""
    config = {}
    
    # 0. Identification
    with st.expander("1. Repère et quantité", expanded=False):
        c_ref, c_qte = st.columns([3, 1])
        # CHANGEMENT: Default Ref Repère 1
        
        # HANDLE PENDING REF UPDATE (Fix StreamlitAPIException)
        if 'pending_ref_id' in st.session_state:
            st.session_state['ref_id'] = st.session_state.pop('pending_ref_id')
            
        if 'pending_ref_id' in st.session_state:
            st.session_state['ref_id'] = st.session_state.pop('pending_ref_id')
            
        base_ref = st.session_state.get('ref_id', get_next_project_ref())
        # If user switched from Menuiserie to Habillage, logic handles it?
        # The session state 'ref_id' is shared. 
        # If current is "F1" (default Menuiserie) and we switch to Habillage, 
        # we might want to propose "H1" if it looks like a default.
        # NOW UNIFIED: Repère 1 for everyone.
        
        ref_chantier = c_ref.text_input("Référence", value=base_ref, key="ref_id")
        qte_piece = c_qte.number_input("Qté", 1, 100, 1, key="qte_val")
        config["ref"] = ref_chantier
        config["qte"] = qte_piece

    # 1. Model Selection
    profile_keys = list(PROFILES_DB.keys())
    model_labels = {k: PROFILES_DB[k]["name"] for k in profile_keys}
    
    with st.expander("2. Modèle & Dimensions", expanded=False):
        # CHANGEMENT: Index 0 (Modèle 1 Plat / Chant)
        # Added explicit key to ensure reset clears it
        selected_key = st.selectbox("Modèle", profile_keys, format_func=lambda x: model_labels[x], index=0, key="hab_model_selector")
        
        if selected_key == "m11":
            # CUSTOM BUILDER
            st.info("Mode Sur Mesure")
            
            # Init state
            if 'custom_segments' not in st.session_state:
                st.session_state['custom_segments'] = [{'type': 'start', 'val_L': 100}]
            
            segs = st.session_state['custom_segments']
            
            # Segment 1 (Start)
            st.markdown(f"**Segment A (Départ)**")
            segs[0]['val_L'] = st.number_input(f"Longueur A (mm)", 0, 1000, segs[0]['val_L'], key="cust_start_L")
            
            # Subsequent Segments
            letter_idx = 1 # B
            
            for i, seg in enumerate(segs[1:], 1):
                char_L = chr(65 + letter_idx)      # B, C...
                char_H = chr(65 + letter_idx + 1)  # C, D...
                
                st.markdown(f"**Pli {i}**")
                
                # Angle Type
                atype = st.selectbox(f"Angle Pli {i}", ["90", "45", "135", "Custom"], key=f"atype_{i}", index=["90","45","135","Custom"].index(seg.get('angle_type', '90')))
                seg['angle_type'] = atype
                
                if atype == "Custom":
                    c1, c2 = st.columns(2)
                    seg['val_L'] = c1.number_input(f"L. {char_L} (mm)", 0, 1000, seg.get('val_L', 50), key=f"valL_{i}")
                    seg['val_H'] = c2.number_input(f"H. {char_H} (mm)", 0, 1000, seg.get('val_H', 20), key=f"valH_{i}")
                    letter_idx += 2 
                else:
                    seg['val_L'] = st.number_input(f"Long. {char_L} (mm)", 0, 1000, seg.get('val_L', 50), key=f"valL_{i}")
                    letter_idx += 1
                
                st.markdown("---")
            
            # Buttons
            c_add, c_del = st.columns(2)
            if c_add.button("➕ Pli", key="btn_add_fold"):
                segs.append({'type': 'fold', 'angle_type': '90', 'val_L': 50})
                st.rerun()
            
            if len(segs) > 1 and c_del.button("➖ Pli", key="btn_del_fold"):
                segs.pop()
                st.rerun()
                
            # Maps for return
            config["A"] = segs[0]['val_L']
            # We don't map all dynamic keys to flat config dict easily, 
            # but main render reads session_state for m11 anyway.
            
        else:
            # STANDARD
            prof = PROFILES_DB[selected_key]
            params = prof["params"]
            defaults = prof["defaults"]
            
            cols_input = st.columns(2)
            for i, p in enumerate(params):
                is_angle = p.startswith("A") and len(p) > 1 and p[1].isdigit() 
                step = 5 if is_angle else 5
                
                with cols_input[i % 2]:
                    label = f"Angle {p}" if is_angle else f"Cote {p}"
                    val = st.number_input(label, value=int(defaults.get(p, 0)), step=int(step), key=f"hab_{selected_key}_{p}")
                    config[p] = val
                    
        length = st.number_input("Longueur (mm)", value=3000, step=100, key="hab_length_input")
        config["length"] = length # Ensure key matches usage

    # 3. Finition
    with st.expander("3. Finition", expanded=False):
        # Type Finition choices
        type_fin_choices = ["Prélaqué 1 face", "Prélaqué 2 faces", "Laquage 1 face", "Laquage 2 faces", "Brut", "Galva"]
        type_finition = st.selectbox("Type", type_fin_choices, index=0, key="hab_type_fin")
        
        epaisseurs = ["10/10ème (1,0 mm)", "15/10ème (1,5 mm)", "20/10ème (2,0 mm)", "30/10ème (3,0 mm)"]
        # Default: 15/10ème (Index 1). Key renamed to avoid conflict with old '75/100' value.
        epaisseur = st.selectbox("Épaisseur", epaisseurs, index=1, key="hab_ep_v2")
        
        colors_list = ["Blanc 9016", "Gris 7016", "Noir 9005", "Chêne Doré", "RAL Spécifique"]
        
        couleur = "Standard"
        
        # Logic for Color Sections
        if "Brut" in type_finition or "Galva" in type_finition:
             st.info(f"Aspect : {type_finition}")
             couleur = f"Sans ({type_finition})"
             
        elif "Laquage 1 face" == type_finition:
             # Choice of face
             face_choice = st.selectbox("Face à laquer", ["Face 1 (Extérieur)", "Face 2 (Intérieur)"], index=0)
             # Color selection
             couleur_st = st.selectbox("Couleur", colors_list, index=0, key="col_laq1")
             if couleur_st == "RAL Spécifique":
                 ral = st.text_input("Code RAL", "RAL ")
                 couleur = f"{ral} ({face_choice})"
             else:
                 couleur = f"{couleur_st} ({face_choice})"
                 
        elif "Laquage 2 faces" == type_finition:
             st.markdown("**Face 1 (Ext)**")
             c1_st = st.selectbox("Couleur F1", colors_list, index=0, key="col_laq2_f1")
             c1_val = c1_st
             if c1_st == "RAL Spécifique": c1_val = st.text_input("RAL F1", "RAL ")
             
             st.markdown("**Face 2 (Int)**")
             c2_st = st.selectbox("Couleur F2", colors_list, index=0, key="col_laq2_f2")
             c2_val = c2_st
             if c2_st == "RAL Spécifique": c2_val = st.text_input("RAL F2", "RAL ")

             couleur = f"F1: {c1_val} / F2: {c2_val}"
             
        elif "Prélaqué 1 face" == type_finition:
             # Face 1 defaults
             couleur_st = st.selectbox("Couleur (Face 1)", colors_list, index=0, key="col_prelaq1")
             config["couleur"] = couleur_st # Backwards compat
             if couleur_st == "RAL Spécifique":
                 couleur = st.text_input("Code RAL", "RAL ")
             else:
                 couleur = couleur_st
                 
        elif "Prélaqué 2 faces" == type_finition:
             # Usually standard colors both sides or diff?
             st.markdown("**Face 1 & 2**")
             couleur_st = st.selectbox("Couleur", colors_list, index=0, key="col_prelaq2")
             couleur = f"{couleur_st} (2 faces)"

        config["finition"] = type_finition
        config["epaisseur"] = epaisseur
        config["couleur"] = couleur

    # Finition END
    
    # --- MOVED ACTION BUTTONS HERE (Bottom of Form, Outside Expander) ---
    # FIXED: REMOVED ROGUE MARKDOWN
    # st.markdown("##    # --- ACTIONS ---")
    st.markdown("### 💾 Actions")
    
    # 0. Show Edition Status
    active_id = st.session_state.get('active_config_id')
    if active_id:
        # Check if active is Habillage?
        # Yes, because we loaded it.
        st.caption(f"✏️ Édition en cours : {st.session_state.get('ref_id', '???')}")
        
    c_btn0, c_btn1, c_btn2 = st.columns(3)
    
    # ACTION: UPDATE (Only if active file)
    if active_id:
         if c_btn0.button("💾 Mettre à jour", use_container_width=True, help="Écraser la configuration active"):
             data = serialize_config()
             data['mode_module'] = 'Habillage' # Ensure consistency
             current_ref = st.session_state.get('ref_id', 'Repère 1')
             
             # Helper function in project_utils.py ? Or implemented here.
             # Need to find 'update_current_config_in_project' in namespace.
             # It is imported.
             update_current_config_in_project(active_id, data, current_ref)
             st.toast(f"✅ {current_ref} mis à jour !")
             st.rerun()
    
    if c_btn1.button("Ajouter & Dupliquer", use_container_width=True, key="hab_btn_add"):
        data = serialize_config()
        data['mode_module'] = 'Habillage'
        new_ref = st.session_state.get('ref_id', 'H1')
        new_id = add_config_to_project(data, new_ref)
        # Fix: Use pending_new_id to avoid "notify after instantiate" error
        st.session_state['pending_new_id'] = new_id
        # AUTO-INCREMENT REF
        st.session_state['pending_ref_id'] = get_next_ref(new_ref)
        st.toast(f"✅ {new_ref} ajouté !")
        st.rerun()

    if c_btn2.button("Ajouter & Nouveau", use_container_width=True, key="hab_btn_new"):
        data = serialize_config()
        data['mode_module'] = 'Habillage'
        new_ref = st.session_state.get('ref_id', 'Repère 1')
        new_id = add_config_to_project(data, new_ref)
        st.session_state['pending_new_id'] = new_id
        st.toast(f"✅ {new_ref} enregistré !")
        
        st.toast(f"✅ {new_ref} enregistré !")
        
        # Reset but DO NOT RERUN yet
        reset_config(rerun=False)
        
        # AUTO-INCREMENT REF (Now this code is reachable)
        st.session_state['pending_ref_id'] = get_next_project_ref()
        st.rerun()


    return {
        "key": selected_key,
        "prof": PROFILES_DB[selected_key],
        "inputs": config, # Flattened config into inputs for compatibility
        # Add discrete keys if needed by main ui
        "ref": ref_chantier,
        "qte": qte_piece,
        "length": length,
        "finition": type_finition, 
        "epaisseur": epaisseur, 
        "couleur": couleur
    }





def render_menuiserie_form():
    global rep, qte, mat, ep_dormant, type_projet, type_pose, ail_val, ail_bas, col_int, col_ext
    global l_dos_dormant, h_dos_dormant, h_allege, vr_opt, h_vr, vr_grille, h_menuiserie
    global is_appui_rap, largeur_appui, txt_partie_basse, zones_config, cfg_global

    # --- SECTION 1 : IDENTIFICATION ---
    with st.expander("1. Repère et quantité", expanded=False):
        c1, c2 = st.columns([3, 1])
        
        # HANDLE PENDING REF UPDATE (Fix StreamlitAPIException)
        if 'pending_ref_id' in st.session_state:
            st.session_state['ref_id'] = st.session_state.pop('pending_ref_id')
            
        rep = c1.text_input("Repère", st.session_state.get('ref_id', get_next_project_ref()), key="ref_id")
        qte = c2.number_input("Qté", 1, 100, 1, key="qte_val")

    # --- SECTION 2 : MATERIAU ---
    with st.expander("2. Matériau & Ailettes", expanded=False):
        mat = st.radio("Matériau", ["PVC", "ALU"], horizontal=True, key="mat_type")

        if mat == "PVC":
            # liste_ailettes_std removed (unlocked)
            liste_couleurs = ["Blanc (9016)", "Plaxé Chêne", "Plaxé Gris 7016", "Beige"]
        else: 
            # liste_ailettes_std removed (unlocked)
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
        c_ail1, c_ail2 = st.columns(2)
        # Unlocked Ailettes (Default 60mm, Manual Input)
        ail_val = c_ail1.number_input(f"Ailettes H/G/D (mm)", min_value=0, value=60, step=5, key="fin_val")
        bas_identique = c_ail2.checkbox("Seuil idem ?", False, key="same_bot")
        # Default Bas to 0 if separate (Standard threshold)
        ail_bas = ail_val if bas_identique else c_ail2.number_input(f"Seuil / Bas (mm)", min_value=0, value=0, step=5, key="fin_bot")

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
        cc1, cc2 = st.columns(2)
        col_int = cc1.selectbox("Couleur Int", liste_couleurs, key="col_in")
        col_ext = cc2.selectbox("Couleur Ext", liste_couleurs, key="col_ex")

    # --- SECTION 3 : DIMENSIONS ---
    with st.expander("3. Dimensions & VR", expanded=False):
        # New Dimensions Type Dropdown
        dim_type = st.selectbox("Type de Côtes", ["Côtes fabrication", "Côtes passage", "Côtes tableau"], key="dim_type")
        c3, c4 = st.columns(2)
        
        # Libellé dynamique pour la Hauteur
        lbl_hauteur = "Hauteur Rejingo" if is_appui_rap else "H. Dos Dormant"
        
        l_dos_dormant = c3.number_input("L. Dos Dormant", 300, 5000, 1200, 10, key="width_dorm")
        h_dos_dormant = c4.number_input(lbl_hauteur, 300, 5000, 1400, 10, help="Hauteur totale incluant le coffre", key="height_dorm")
        
        # Hauteur d'Allège
        h_allege = st.number_input("Hauteur Allège", 0, 2500, 900, step=10, key="h_allege")

        vr_opt = st.toggle("Volet Roulant", False, key="vr_enable")
        h_vr = 0
        vr_grille = False
        if vr_opt:
            h_vr = st.number_input("Hauteur Coffre", 0, 500, 185, 10, key="vr_h")
            vr_grille = st.checkbox("Grille d'aération ?", key="vr_g")
            h_menuiserie = h_dos_dormant - h_vr
            st.markdown(f"""<div style='background:#e8f4f8; padding:5px; border-radius:4px; font-weight:bold; color:#2c3e50; text-align:center;'>🧮 H. Menuiserie : {int(h_menuiserie)} mm</div>""", unsafe_allow_html=True)
        else:
            h_menuiserie = h_dos_dormant

    # --- SECTION 4 : STRUCTURE & FINITIONS ---
    with st.expander("4. Structure & Finitions", expanded=False):
        # mode_structure = st.radio("Mode Structure", ["Simple (1 Zone)", "Divisée (2 Zones)"], horizontal=True, key="struct_mode", index=0)
        st.caption("Arbre de configuration (Diviser/Fusionner)")

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
     # --- ACTIONS ---
    st.markdown("### 💾 Actions")
    
    active_id = st.session_state.get('active_config_id')
    if active_id:
        st.caption(f"✏️ Édition en cours : {st.session_state.get('ref_id', '???')}")
        
    c_btn0, c_btn1, c_btn2 = st.columns(3)
    
    # ACTION: UPDATE (Menuiserie)
    if active_id:
        if c_btn0.button("💾 Mettre à jour", use_container_width=True, help="Écraser la configuration active"):
             data = serialize_config()
             data['mode_module'] = 'Menuiserie'
             current_ref = st.session_state.get('ref_id', 'Repère 1')
             update_current_config_in_project(active_id, data, current_ref)
             st.toast(f"✅ {current_ref} mis à jour !")
             st.rerun()

    # 1. Ajouter et Dupliquer (Save as New, Keep Editing)
    if c_btn1.button("Ajouter & Dupliquer", use_container_width=True, help="Enregistrer une copie"):
        data = serialize_config()
        # Ensure mode_module is saved
        data['mode_module'] = 'Menuiserie'
        new_ref = st.session_state.get('ref_id', 'Repère 1')
        
        new_id = add_config_to_project(data, new_ref)
        st.session_state['pending_new_id'] = new_id # Fix error
        # AUTO-INCREMENT REF
        st.session_state['pending_ref_id'] = get_next_ref(new_ref)
        st.toast(f"✅ {new_ref} ajouté à la liste !")
        st.rerun()
        
    # 2. Ajouter et Nouveau (Save as New, Reset)
    if c_btn2.button("Ajouter & Nouveau", use_container_width=True):
        data = serialize_config()
        data['mode_module'] = 'Menuiserie'
        new_ref = st.session_state.get('ref_id', 'Repère 1')
        
        new_id = add_config_to_project(data, new_ref)
        st.session_state['pending_new_id'] = new_id
        st.toast(f"✅ {new_ref} enregistré !")
        
        # RESET (No Rerun)
        reset_config(rerun=False) 
        # AUTO-INCREMENT REF
        st.session_state['pending_ref_id'] = get_next_project_ref()
        st.rerun()
    




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
# Base directory for artifacts
# (Déplacé en haut de fichier pour portée globale)

# Define Profile Models based on User Images (1-5)

# Define Profile Models based on User Images (1-5)




# --- MAIN LAYOUT V3 (Responsive Columns) ---

# 1. Logo & Branding
# 1. Logo & Branding
# 1. Logo & Branding
# Direct placement for maximum left alignment and size control
# Remove columns to avoid gutters
if 'LOGO_B64' in globals():
    try:
         # Robust Logic for Main UI Logo
         try:
             decoded = base64.b64decode(LOGO_B64, validate=True)
         except:
             b64 = LOGO_B64
             b64 += "=" * ((4 - len(b64) % 4) % 4)
             decoded = base64.b64decode(b64)
         
         st.image(decoded, width=350)
    except Exception as e:
         st.error(f"Error loading logo: {e}")
else:
     st.warning("Logo variable not found.")


# Spacer between logo and Project Name
st.write("")

# 2. Top Navigation & Project Management
render_top_navigation()

# 2. Main Content Columns (Desktop: Config Left / Preview Right)
# Mobile: Stacked automatically due to Streamlit columns behavior
c_config, c_preview = st.columns([1, 1.3])

hab_config = None
current_mode = st.session_state.get('mode_module', 'Menuiserie')

# --- COLUMN LEFT: CONFIGURATION ---
with c_config:
    # BOUTON RESET (RESTAURÉ)
    if st.button("❌ Réinitialiser", use_container_width=True, help="Remettre à zéro le formulaire"):
        reset_config()
        
    if current_mode == 'Menuiserie':
        st.markdown("### 🛠 Options Menuiserie")
        render_menuiserie_form()
    else:
        st.markdown("### 🧱 Options Habillage")
        hab_config = render_habillage_form()

# --- COLUMN RIGHT: VISUALISATION ---
with c_preview:
    st.markdown("### 👁️ Visualisation")
    
    if current_mode == 'Menuiserie':
        # 1. PLAN TECHNIQUE
        try:
            svg_output = generate_svg_v73()
            # Use container width for SVG
            st.markdown(f"<div>{svg_output}</div>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Erreur SVG: {e}")
            import traceback
            st.code(traceback.format_exc())

        # 2. RÉCAPITULATIF SOUS LE DESSIN
        st.markdown("---")
        
        # PREPARE ZONES DATA
        config_display = flatten_tree(st.session_state.get('zone_tree'), 0,0,0,0)
        sorted_zones = sorted(config_display, key=lambda z: z['id'])

        # Nested columns for Recap
        c_recap_l, c_recap_r = st.columns([1, 1])

        with c_recap_l:
            st.subheader("Info. Générales")
            
            s = st.session_state
            
            if s.get('is_appui_rap', False):
                pb_txt = f"Appui Rapp. ({s.get('width_appui', 0)}mm)"
            else:
                pb_txt = "Bavette 100x100"
                
            vr_txt = "Oui" if s.get('vr_enable', False) else "Non"
            h_ail = s.get('fin_val', 0)
            b_ail = s.get('fin_bot', 0) if not s.get('same_bot', False) else h_ail
            ailes_txt = f"H/G/D:{h_ail} B:{b_ail}"

            # --- UI INFO GÉNÉRALES (Refactored V23) ---
            st.markdown("#### 📝 Synthèse")
            
            # Helper for metrics
            def kpi(label, value):
                st.markdown(f"**{label}** : {value}")

            ci1, ci2 = st.columns(2)
            with ci1:
                kpi("Repère", s.get('ref_id', 'F1'))
                kpi("Quantité", s.get('qte_val', 1))
                kpi("Dimensions", f"{s.get('width_dorm', 0)} x {s.get('height_dorm', 0)}")
                kpi("Type Côtes", s.get('dim_type', 'Tableau'))
                kpi("Matériau", s.get('mat_type', 'PVC'))
                
            with ci2:
                kpi("Pose", s.get('pose_type', '-')[:20]+"..")
                # Ailettes formatting
                h_ail = s.get('fin_val', 0)
                b_ail = s.get('fin_bot', 0) if not s.get('same_bot', False) else h_ail
                kpi("Ailettes", f"H/G/D: {h_ail}mm | Bas: {b_ail}mm")
                kpi("Dormant", f"{s.get('frame_thig', 70)} mm")
                kpi("Couleurs", f"Int: {s.get('col_in','-')} / Ext: {s.get('col_ex','-')}") # Fix <br>
            
            # --- EXPORT HTML FULL (V23) ---
            # Construction manuelle pour garantir la fidélité
            
            # 1. Info Table HTML
            info_rows = f"""
                <tr><td><strong>Repère</strong></td><td>{s.get('ref_id', 'F1')}</td><td><strong>Quantité</strong></td><td>{s.get('qte_val', 1)}</td></tr>
                <tr><td><strong>Dimensions</strong></td><td>{s.get('width_dorm', 0)} x {s.get('height_dorm', 0)} mm</td><td><strong>Type de Côtes</strong></td><td>{s.get('dim_type', '-')}</td></tr>
                <tr><td><strong>Matériau</strong></td><td>{s.get('mat_type', 'PVC')}</td><td><strong>Dormant</strong></td><td>{s.get('frame_thig', 70)} mm</td></tr>
                <tr><td><strong>Pose</strong></td><td colspan="3">{s.get('pose_type', '-')}</td></tr>
                <tr><td><strong>Ailettes</strong></td><td>H/G/D: {h_ail}mm / Bas: {b_ail}mm</td><td><strong>Bas</strong></td><td>{pb_txt}</td></tr>
                <tr><td><strong>Couleurs</strong></td><td colspan="3">Int: {s.get('col_in','-')} / Ext: {s.get('col_ex','-')}</td></tr>
                <tr><td><strong>Volet Roulant</strong></td><td colspan="3">{vr_txt}</td></tr>
            """
            
            # 2. Zones Details
            zones_html_rows = ""
            for z in sorted_zones:
                d_list = []
                remp = z['params'].get('remplissage_global', 'Vitrage')
                d_list.append(f"<b>Remp:</b> {remp}")
                if remp == "Vitrage":
                    d_list.append(f"V: Ext {z['params'].get('vitrage_ext','4')} / Int {z['params'].get('vitrage_int','4')}")
                
                # Check Traverse Thickness (if split) -> Not easy to list here as this loop is leaf zones?
                # Actually flat_zones contains LEAFs. Splits are structural.
                # If we want traverse info, we need to inspect the TREE or just mention global defaults.
                
                if z['params'].get('grille_aera'): d_list.append(f"Grille: {z['params'].get('pos_grille')}")
                if 'sens' in z['params']: d_list.append(f"Sens: {z['params']['sens']}")
                
                # Try to extract traverse thickness from parent? Too complex for now.
                
                details_str = " | ".join(d_list)
                zones_html_rows += f"<tr><td style='width:30%'><strong>{z['label']}</strong> ({z['type']})</td><td>{details_str}</td></tr>"

            menuiserie_html = f"""
            <!DOCTYPE html><html><head><meta charset="utf-8">
            <title>Fiche_{s.get('ref_id', 'F1')}</title>
            <style>
                body {{ font-family: 'Helvetica', sans-serif; padding: 40px; color:#333; }}
                h1 {{ color:#2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }}
                h2 {{ color:#0066cc; margin-top: 30px; font-size: 18px; border-bottom: 1px solid #eee; }}
                table {{ width: 100%; border-collapse: collapse; margin-top:10px; font-size: 14px; }}
                td, th {{ border: 1px solid #ddd; padding: 8px; vertical-align: top; }} 
                th {{ background: #f9f9f9; text-align:left; }}
                .highlight {{ background-color: #f0f7ff; font-weight: bold; }}
                .drawing {{ text-align:center; margin: 30px 0; border: 1px solid #eee; padding: 20px; }}
                @media print {{ body {{ padding: 0; }} .no-print {{ display: none; }} }}
            </style></head><body>
            
            <h1>Fiche Technique - {s.get('ref_id', 'F1')}</h1>
            <p style="font-size:16px;"><strong>Projet:</strong> {s.get('project', {}).get('name', 'P')} | <strong>Date:</strong> {datetime.datetime.now().strftime('%d/%m/%Y')}</p>
            
            <h2>1. Informations Générales</h2>
            <table>{info_rows}</table>
            
            <h2>2. Plan Technique</h2>
            <div class="drawing">{svg_output}</div>
            
            <h2>3. Détails des Zones</h2>
            <table>
                <tr class="highlight"><th>Zone</th><th>Caractéristiques</th></tr>
                {zones_html_rows}
            </table>
            
            <p style="margin-top:50px; font-size:12px; color:#999; text-align:center;">
                Document généré par l'application Miroiterie Yerroise.
            </p>
            <script>
                // Auto print prompt
                // window.onload = function() {{ window.print(); }}
            </script>
            </body></html>"""
            



# Use the function
        pdf_buffer = generate_pdf_report(s, svg_output)

        if pdf_buffer:
            st.download_button(
                label="📄 Télécharger PDF (Officiel)",
                data=pdf_buffer,
                file_name=f"Fiche_{s.get('ref_id', 'F1')}.pdf",
                mime="application/pdf"
            )
        else:
            st.error("❌ Erreur CRITIQUE : Impossible de générer le fichier PDF.")
            st.warning("Veuillez contacter le support.")


        with c_recap_r:
            st.subheader("Détail Zones")
            for z in sorted_zones:
                with st.expander(f"{z['label']} : {z['type']}", expanded=True):
                    remp_global = z['params'].get('remplissage_global', 'Vitrage')
                    st.write(f"**Remp:** {remp_global}")
                    if remp_global == "Vitrage":
                        st.caption(f"Ex:{z['params'].get('vitrage_ext')} / In:{z['params'].get('vitrage_int')}")
                    if z['params'].get('grille_aera'):
                        st.caption(f"Grille: {z['params'].get('pos_grille')}")

    else:
        # HABILLAGE PREVIEW
        if hab_config:
            render_habillage_main_ui(hab_config)
        else:
            st.info("Configuration Habillage non initialisée.")


# END OF CODE V73.5 (VALIDATED)
