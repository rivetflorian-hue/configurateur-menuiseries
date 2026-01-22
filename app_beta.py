import streamlit as st
import math
import uuid
import json
import copy
import pandas as pd
import os
import base64
import datetime





# Dynamic Logo Loader
def load_logo():
    try:
        # Prefer cropped version if available
        p_cropped = os.path.join(os.path.dirname(__file__), "assets/logo_miroiterie_cropped.jpg")
        p_original = os.path.join(os.path.dirname(__file__), "assets/logo_miroiterie.jpg")
        
        p = p_cropped if os.path.exists(p_cropped) else p_original
        
        if os.path.exists(p):
            with open(p, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except:
        pass
    return ""

LOGO_B64 = load_logo()

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
        return buffer, None # Success
    except Exception as e:
        # GLOBAL CRASH CATCHER
        return None, f"{str(e)}" # Return error details

def render_html_menuiserie(s, svg_string, logo_b64):
    """HTML generation for Menuiserie printing (Full Width Bottom Plan)."""
    
    # Pre-calc Observations
    obs_men_html = ""
    if s.get('men_obs'):
        obs_men_html = f"""
            <div class="section-block">
                <h3>Observations</h3>
                <div class="panel">
                    <div class="panel-row" style="display:block; min-height:auto; padding:10px;"><span class="val" style="text-align:left; width:100%; white-space: pre-wrap;">{s.get('men_obs')}</span></div>
                </div>
            </div>
        """

    css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
        body { font-family: 'Roboto', sans-serif; -webkit-print-color-adjust: exact; padding: 0; margin: 0; background-color: #fff; color: #333; }
        
        .page-container { 
            max-width: 210mm; 
            margin: 0 auto; 
            padding: 20px;
        }

        /* HEADER */
        .header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; border-bottom: 3px solid #2c3e50; padding-bottom: 15px; }
        .header-left img { max-height: 70px; width: auto; }
        .header-left .subtitle { color: #3498db; font-size: 14px; margin-top: 5px; font-weight: 400; }
        
        .header-right { text-align: right; padding-right: 5px; }
        .header-right .label { font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 2px; }
        .header-right .ref { font-size: 24px; font-weight: bold; color: #000; margin-bottom: 2px; line-height: 1; }
        .header-right .date { font-size: 11px; color: #666; }

        /* STACKED LAYOUT (Sections) */
        .section-block { margin-bottom: 25px; break-inside: avoid; }
        
        /* HEADINGS */
        h3 { 
            font-size: 15px; color: #2c3e50; margin: 0 0 12px 0; 
            border-left: 5px solid #3498db; padding-left: 10px; 
            line-height: 1.2; text-transform: uppercase; letter-spacing: 0.5px;
        }
        
        /* PANELS */
        .panel { background: #fdfdfd; padding: 15px; border: 1px solid #eee; border-radius: 4px; font-size: 11px; }
        .panel-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px dotted #ccc; }
        .panel-row:last-child { border-bottom: none; }
        .panel-row .lbl { font-weight: bold; color: #444; width: 40%; }
        .panel-row .val { font-weight: normal; color: #000; text-align: right; width: 60%; }
        
        /* ZONES TABLE (Full Width) */
        table { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 5px; }
        th { background: #cfd8dc; color: #2c3e50; padding: 6px; text-align: left; text-transform: uppercase; font-size: 10px; }
        td { border-bottom: 1px solid #eee; padding: 8px 12px; color: #333; line-height: 1.4; }
        tr:nth-child(even) { background-color: #f9f9f9; }

        /* BOTTOM SECTION (PLAN) */
        .visual-box {
            border: none; margin-top: 20px;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            position: relative;
            width: 100%; height: 800px; /* Reduced to fit on Page 2 with Title */
            page-break-inside: avoid;
        }
        /* Allow SVG to take more space */
        .visual-box svg { height: 100%; width: auto; max-width: 98%; }
        
        .footer { 
            position: fixed; bottom: 10mm; left: 0; right: 0;
            font-size: 9px; color: #999; text-align: center; 
        }

        @media print {
            @page { size: A4; margin: 12mm; }
            body { padding: 0; background: white; -webkit-print-color-adjust: exact; }
            .page-container { margin: 0; padding: 0; box-shadow: none; max-width: none; width: 100%; }
            .no-print { display: none; }
            h3 { break-after: avoid; }
            /* Explicit Page Breaks with Safety Margin */
            .page-break { page-break-before: always; padding-top: 30px; }
        }
    </style>
    """
    
    # Logo
    logo_html = f"<h1>Fiche Technique</h1>"
    if logo_b64:
        logo_html = f'<img src="data:image/jpeg;base64,{logo_b64}" alt="Logo">'
        
    # Zones Processing
    w_d = s.get('width_dorm', 1000)
    h_d = s.get('height_dorm', 1000)
    flat = flatten_tree(s.get('zone_tree'), 0,0,w_d,h_d)
    real = [z for z in flat if z['type'] != 'split']
    sorted_zones = sorted(real, key=lambda z: (z['y'], z['x']))
    
    # Common Factorization Logic (For Print)
    # V75 FIX: Only factorize if multiple zones. If 1 zone, show details in Zone section.
    def get_vit(zparams):
         # V12 ROBUSTNESS: Reconstruct if missing
         res = zparams.get('vitrage_resume', '')
         if not res or res == "None":
             # Try to reconstruct from components
             if 'vitrage_ext_ep' in zparams:
                 # V11 Logic Reconstruction
                 try:
                     ep_e = str(zparams.get('vitrage_ext_ep','4')).replace(' mm', '')
                     ep_i = str(zparams.get('vitrage_int_ep','4')).replace(' mm', '')
                     # Handle "Vide Air" key variation (vide_air_ep vs vit_ep_air)
                     ep_a = str(zparams.get('vide_air_ep', zparams.get('vit_ep_air', '16'))).replace(' mm', '')
                     
                     c_e = zparams.get('vitrage_ext_couche','Aucune')
                     c_i = zparams.get('vitrage_int_couche','Aucune')
                     
                     sf_e = "FE" if "FE" in c_e else (" CS" if "Contrôle" in c_e else "")
                     sf_i = "FE" if "FE" in c_i else ""
                     
                     ty_e = zparams.get('vitrage_ext_type','Clair')
                     st_e = f" {ty_e}" if ty_e != "Clair" else ""
                     
                     ty_i = zparams.get('vitrage_int_type','Clair')
                     st_i = f" {ty_i}" if ty_i != "Clair" else ""
                     
                     gaz = zparams.get('vit_gaz','Argon').upper() # Default to Argon if missing
                     inter = str(zparams.get('intercalaire_type','Alu')).upper()
                     
                     res = f"Vit. {ep_e}{st_e}{sf_e} / {ep_a} / {ep_i}{st_i}{sf_i} - {inter} + GAZ {gaz}"
                 except:
                     res = "-"
             else:
                 res = "-"
         return str(res).replace('\n', ' ')

    def get_grille(zparams): return zparams.get('pos_grille', 'Aucune')

    common_specs = {}
    if sorted_zones and len(sorted_zones) > 1:
         first_type = sorted_zones[0]['type']
         if all(z['type'] == first_type for z in sorted_zones): common_specs['Type'] = first_type
         
         first_vit = get_vit(sorted_zones[0]['params'])
         if all(get_vit(z['params']) == first_vit for z in sorted_zones): common_specs['Vitrage'] = first_vit
         
         first_grille = get_grille(sorted_zones[0]['params'])
         if all(get_grille(z['params']) == first_grille for z in sorted_zones): 
             if first_grille != "Aucune": common_specs['Ventilation'] = first_grille
    
    z_rows = ""
    for z in sorted_zones:
        # Compact Line Building
        parts = [f"<strong>{z['label']}</strong> : {int(z['w'])} x {int(z['h'])} mm"]
        
        # Specifics
        if 'Type' not in common_specs: parts.append(f"Type: {z['type']}")
        
        v_curr = get_vit(z['params'])
        if 'Vitrage' not in common_specs: parts.append(f"Vitrage: {v_curr}")
        
        # Options
        opts = []
        if 'sens' in z['params']: opts.append(f"Sens {z['params']['sens']}")
        
        g_curr = get_grille(z['params'])
        if 'Ventilation' not in common_specs and g_curr != "Aucune": opts.append(f"VMC: {g_curr}")
        
        if z['params'].get('h_poignee', 0) > 0: opts.append(f"HP {z['params']['h_poignee']}mm")
        
        nb_h = z['params'].get('traverses', 0)
        nb_v = z['params'].get('traverses_v', 0)
        if nb_h > 0:
             ep_t = z['params'].get('epaisseur_traverse', 20)
             opts.append(f"Trav. {nb_h}H (Ep.{ep_t})")
             if nb_h == 1 and nb_v == 0:
                 opts.append(f"Remp. H:{z['params'].get('remp_haut','V')}/B:{z['params'].get('remp_bas','P')}")
        if nb_v > 0:
             opts.append(f"PB {nb_v}V")
        
        if opts: parts.append(f"Options: {', '.join(opts)}")
        
        full_line = " • ".join(parts)
        # More padding for comfort
        z_rows += f"<tr><td>{full_line}</td></tr>"

    # Pre-calc values
    ref_id = s.get('ref_id', 'F1')
    
    # Calc dimensions for Global Panel
    w_rec = w_d + (2 * s.get('fin_val', 0))
    h_bot_add = s.get('width_appui', 0) if s.get('is_appui_rap', False) else (s.get('fin_bot', 0) if not s.get('same_bot', False) else s.get('fin_val', 0))
    h_rec = h_d + s.get('fin_val', 0) + h_bot_add

    # Format Ailettes String
    if s.get('fin_val', 0) > 0:
        ail_str = f"{s.get('fin_val',0)}mm (H/G/D) / {s.get('fin_bot', 0) if not s.get('same_bot') else s.get('fin_val',0)}mm (Bas)"
    else:
        ail_str = "Sans"

    # Format Common Specs String
    common_str = ""
    for k,v in common_specs.items():
        common_str += f"<div class='panel-row'><span class='lbl'>{k} (Commun)</span> <span class='val'>{v}</span></div>"

    import datetime
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{css}</head>
    <body>
        <div class="page-container">
            <!-- HEADER -->
            <div class="header">
                <div class="header-left">
                    {logo_html}
                    <div class="subtitle">Menuiserie {s.get('mat_type', 'PVC')}</div>
                </div>
                <div class="header-right">
                    <div class="label">RÉFÉRENCE CHANTIER</div>
                    <div class="ref">{ref_id}</div>
                    <div class="date">{datetime.datetime.now().strftime('%d/%m/%Y')}</div>
                </div>
            </div>
            
            <!-- STACKED SECTIONS -->
            
            <!-- 1. INFORMATIONS GENERALES -->
            <div class="section-block">
                <h3>Informations Générales</h3>
                <div class="panel">
                    <div class="panel-row"><span class="lbl">Repère</span> <span class="val">{ref_id}</span></div>
                    <div class="panel-row"><span class="lbl">Quantité</span> <span class="val">{s.get('qte_val', 1)}</span></div>
                    <div class="panel-row"><span class="lbl">Projet</span> <span class="val">{s.get('proj_type', 'Rénovation')}</span></div>
                    <div class="panel-row"><span class="lbl">Pose</span> <span class="val">{s.get('pose_type')}</span></div>
                    <div class="panel-row"><span class="lbl">Dormant</span> <span class="val">{s.get('frame_thig')} mm</span></div>
                    <div class="panel-row"><span class="lbl">Ailettes</span> <span class="val">{ail_str}</span></div>
                    <div class="panel-row"><span class="lbl">Appui</span> <span class="val">{'OUI ('+str(s.get('width_appui'))+'mm)' if s.get('is_appui_rap') else 'NON'}</span></div>
                    <div class="panel-row"><span class="lbl">Couleur</span> <span class="val">{s.get('col_in')} (Int) / {s.get('col_ex')} (Ext)</span></div>
                    <div class="panel-row"><span class="lbl">Type Côtes</span> <span class="val">{s.get('dim_type', 'Tableau')}</span></div>
                    <div class="panel-row"><span class="lbl">Dos Dormant</span> <span class="val">{w_d} x {h_d} mm</span></div>
                    <div class="panel-row"><span class="lbl">Recouvrement</span> <span class="val">{w_rec} x {h_rec} mm</span></div>
                    <div class="panel-row"><span class="lbl">Allège</span> <span class="val">{s.get('h_allege', 0)} mm</span></div>
                    <div class="panel-row"><span class="lbl">Volet R.</span> <span class="val">{'OUI ('+str(int(s.get('vr_h',0)))+'mm)' if s.get('vr_enable') else 'NON'}</span></div>
                    {common_str}
                </div>
            </div>
            
            <!-- 2. DETAILS DES ZONES -->
            <div class="section-block">
                <h3>Détails des Zones</h3>
                <div class="panel">
                    <table>
                        <tbody>{z_rows}</tbody>
                    </table>
                </div>
            </div>
            
            <!-- 3. PLAN TECHNIQUE (New Page) -->
            <div class="page-break">
                <h3>Plan Technique</h3>
                <div class="visual-box">
                    {svg_string}
                    <div style="position:absolute; bottom:10px; font-size:10px; color:#aaa;">Vue extérieure - Cotes tableau en mm</div>
                </div>
            </div>
            
            <!-- OBSERVATIONS -->
            {obs_men_html}
            
            <div class="footer">
                Document généré automatiquement - Miroiterie Yerroise<br>
                Merci de vérifier les cotes avant validation définitive.
            </div>
        </div>
    </body>
    </html>
    """
    return html

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
    # V76 FIX: Apply Defered State Updates (To avoid Widget Instantiated Error)
    if 'pending_updates' in st.session_state:
        updates = st.session_state.pop('pending_updates')
        for k, v in updates.items():
            st.session_state[k] = v
            
    if 'project' not in st.session_state:
        st.session_state['project'] = {
            "name": "Nouveau Projet",
            "configs": [] # List of dicts: {id, ref, data}
        }
        
    # Fix for missing observations on fresh reload
    if 'men_obs' not in st.session_state:
        st.session_state['men_obs'] = ""
    
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
        'vr_enable', 'vr_h', 'vr_g', 'struct_mode', 'zone_tree',
        'men_w_tab_ex', 'men_h_tab_ex',
        'vr_add_winding',
        'men_obs'
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
    # V75 FIX: Remove 'mode_module' from keep list to ensure context switch works even if target is faulty
    keys_keep = ['project', 'mgr_sel_id', 'active_config_id', 'uploader_json', 'clean_config_snapshot']
    keys_to_del = [k for k in st.session_state if k not in keys_keep]
    for k in keys_to_del:
        del st.session_state[k]
        
    # 2. Load new data
    for k, v in data.items():
        # MORE ROBUST FILTERING on load (V10 FIX)
        # Scrub button keys that cause Streamlit ValueAssignmentNotAllowedError
        if isinstance(k, str):
            if k.endswith('_btn') or k.startswith('btn_'): continue
            if 'updup' in k or 'save_u' in k or 'del_u' in k or 'add_new' in k or 'upnew' in k: continue
            # Specific known offenders (Added vit_upnew)
            if k in ['vit_updup', 'vit_save_u', 'vit_del_u', 'vit_add_new', 'vit_upnew']: continue
            
        # FIXED V73: DEEP COPY on load to ensure UI edits don't mutate stored config in real-time.
        # This decouples the "Working Draft" (Session State) from the "Saved File" (Project Dict).
        try:
            st.session_state[k] = copy.deepcopy(v)
        except Exception:
            # Fallback for non-copyable objects (rare in checking, but safe)
            st.session_state[k] = v
            
    # 3. SET CLEAN SNAPSHOT (V75 - Config Management)
    # We take a snapshot of what we just loaded to be the "clean" state
    st.session_state['clean_config_snapshot'] = json.dumps(data, sort_keys=True, default=str)

def get_config_snapshot(current_data):
    """Returns a serialized string of the current config for comparison."""
    # Using sort_keys to ensure deterministic order
    return json.dumps(current_data, sort_keys=True, default=str)

def is_config_dirty(current_data):
    """Checks if the current data differs from the loaded snapshot."""
    if 'clean_config_snapshot' not in st.session_state:
        return True # Default to dirty if no snapshot
    
    current_snap = get_config_snapshot(current_data)
    return current_snap != st.session_state['clean_config_snapshot']

# ... (omitted unrelated functions) ...

def serialize_vitrage_config():
    """Capture toutes les variables Vitrage pour la sauvegarde."""
    # V10 FIX: Exclude ephemeral button keys from save
    data = {}
    for k, v in st.session_state.items():
        if k.startswith('vit_'):
            # Filter out known button keys (Added upnew)
            if 'btn' in k or 'updup' in k or 'save_u' in k or 'del_u' in k or 'add_new' in k or 'upnew' in k:
                continue
            data[k] = v
            
    # FORCE RECALC RESUME (Fix for "None" or stale data)
    # FORCE RECALC RESUME (Fix for "None" or stale data)
    s = st.session_state
    vt = s.get('vit_type_mode', 'Double Vitrage')
    if vt == "Double Vitrage":
        # Format V11: Vit. ep_ext / ep_air / ep_int - inter + GAZ gaz
        ep_e = s.get('vit_ep_ext','4').replace(' mm', '')
        ep_i = s.get('vit_ep_int','4').replace(' mm', '')
        ep_a = s.get('vit_ep_air','16').replace(' mm', '')
        
        c_e = s.get('vit_couche_ext','Aucune')
        c_i = s.get('vit_couche_int','Aucune')
        
        sf_e = "FE" if "FE" in c_e else (" CS" if "Contrôle" in c_e else "")
        sf_i = "FE" if "FE" in c_i else ""
        
        ty_e = s.get('vit_type_ext','Clair')
        st_e = f" {ty_e}" if ty_e != "Clair" else ""
        
        ty_i = s.get('vit_type_int','Clair')
        st_i = f" {ty_i}" if ty_i != "Clair" else ""
        
        gaz = s.get('vit_gaz','Argon').upper()
        inter = s.get('vit_intercalaire','Alu').upper()
        
        resume = f"Vit. {ep_e}{st_e}{sf_e} / {ep_a} / {ep_i}{st_i}{sf_i} - {inter} + GAZ {gaz}"

    elif vt == "Simple Vitrage":
        ep_e = s.get('vit_ep_ext','4').replace(' mm', '')
        ty_e = s.get('vit_type_ext','Clair')
        resume = f"Simple {ep_e} {ty_e}"
    else:
        resume = "Panneau Plein"
    data['vit_resume'] = resume
    
    # Add Standard Keys for Project Management
    # V11 FIX: Default to next Ref if missing
    data['ref_id'] = st.session_state.get('vit_ref', get_next_project_ref())
    data['qte_val'] = st.session_state.get('vit_qte', 1)
    data['mode_module'] = 'Vitrage'
    return data
        
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
    if 'project' in st.session_state and 'configs' in st.session_state['project']:
        old_len = len(st.session_state['project']['configs'])
        # V76 Debug: Use list comprehension to create NEW list (effectively deleting)
        new_list = [c for c in st.session_state['project']['configs'] if c['id'] != config_id]
        
        st.session_state['project']['configs'] = new_list
        
        # DEBUG
        diff = old_len - len(new_list)
        # st.toast(f"DEBUG: Deleted {diff} items. Remaining: {len(new_list)}")
        print(f"DEBUG: Delete requested for {config_id}. Count before: {old_len}, Count after: {len(new_list)}")

def convert_hab_json_to_state(data):
    """Converts a Habillage JSON export into a Session State compatible dict."""
    state = {}
    
    # 1. Base Copy
    state.update(data)
    
    # 2. Map Model Name -> Key
    model_name = data.get('modele')
    model_key = None
    if model_name:
        for k, v in PROFILES_DB.items():
            if v['name'] == model_name:
                model_key = k
                break
    
    if model_key:
        state['hab_model_selector'] = model_key
        # Map Dimensions
        dims = data.get('dims', {})
        if isinstance(dims, dict):
            for p, val in dims.items():
                state[f"hab_{model_key}_{p}"] = val
                
    # 3. Map Common Fields
    if 'longueur' in data:
        state['hab_length_input'] = data['longueur']
        
    if 'finition' in data:
        state['hab_type_fin'] = data['finition']
        
    if 'epaisseur' in data:
        state['hab_ep_v2'] = data['epaisseur']
        
    if 'observations' in data:
        state['hab_obs'] = data['observations']
    elif 'hab_obs' in data:
        state['hab_obs'] = data['hab_obs']
        
    # 4. Ensure ID/Ref
    if 'ref' in data: state['ref_id'] = data['ref']
    if 'qte' in data: state['qte_val'] = data['qte']
    
    return state

def render_top_navigation():
    """Affiche la navigation supérieure (Projet, Mode, Liste)."""
    
    # 1. Ligne Supérieure : Nom Projet & Imports
    # V77 FIX: More space for buttons to prevent wrapping (2.5 vs 1.5)
    c_proj, c_imp = st.columns([2.5, 1.5], vertical_alignment="bottom")
    
    with c_proj:
        # Style 'Title' for Project Name
        proj_name = st.text_input("Nom du Chantier", st.session_state['project']['name'], key="proj_name_top")
        if proj_name != st.session_state['project']['name']:
            st.session_state['project']['name'] = proj_name
            
    with c_imp:
        col_new, col_opt = st.columns([1, 1])
        with col_new:
            if st.button("🗑️ Nouveau", help="Tout effacer et recommencer", use_container_width=True):
                st.session_state.clear()
                st.rerun()
        
        with col_opt:
            with st.popover("⚙️ Options", use_container_width=True):
                st.markdown("### Import / Export")
                proj_data = json.dumps(st.session_state['project'], indent=2)
                raw_name = st.session_state['project'].get('name', 'Projet_Fenetre')
                safe_name = "".join([c if c.isalnum() else "_" for c in raw_name])
                dl_name = f"{safe_name}.json"
                
                st.download_button("Export (JSON)", proj_data, file_name=dl_name, mime="application/json")
                
                def import_project_callback():
                    uploaded = st.session_state.get('uploader_json')
                    if uploaded:
                        try:
                            uploaded.seek(0)
                            data = json.load(uploaded)
                            
                            # CASE 1: Full Project Import
                            if isinstance(data, dict) and 'configs' in data:
                                st.session_state['project'] = data
                                st.session_state['active_config_id'] = None
                                st.toast("✅ Projet complet chargé avec succès !")
                                
                            # CASE 2: Single Config Import (Add to current project)
                            elif isinstance(data, dict) and ('ref_id' in data or 'mat_type' in data):
                                # Determine Ref
                                ref = data.get('ref_id', f"Import_{len(st.session_state['project']['configs'])+1}")
                                new_id = str(uuid.uuid4())
                                st.session_state['project']['configs'].append({
                                    "id": new_id,
                                    "ref": ref,
                                    "data": data
                                })
                                st.toast(f"➕ Configuration '{ref}' ajoutée au projet !")
                                
                            # CASE 3: Habillage Import (Specific Keys or Rendered Report)
                            elif isinstance(data, dict) and ('developpe' in data or 'modele' in data):
                                # Convert Report Data to Session State format
                                state_data = convert_hab_json_to_state(data)
                                state_data['mode_module'] = 'Habillage'
                                
                                ref = data.get('ref', f"Habillage_{len(st.session_state['project']['configs'])+1}")
                                
                                # CHECK FOR DUPLICATES
                                existing = next((c for c in st.session_state['project']['configs'] if c['ref'] == ref), None)
                                
                                if existing:
                                    existing['data'] = state_data
                                    st.toast(f"🔄 Habillage '{ref}' mis à jour !")
                                else:
                                    new_id = str(uuid.uuid4())
                                    st.session_state['project']['configs'].append({
                                        "id": new_id,
                                        "ref": ref,
                                        "data": state_data
                                    })
                                    st.toast(f"➕ Habillage '{ref}' ajouté au projet !")

                                # RESET UI EXPANDERS
                                st.session_state['ui_reset_counter'] = st.session_state.get('ui_reset_counter', 0) + 1
                                
                            else:
                                keys = list(data.keys()) if isinstance(data, dict) else str(type(data))
                                st.error(f"Format JSON inconnu. Clés trouvées: {keys}")
                                
                        except Exception as e:
                            st.error(f"Erreur lors de l'import : {e}")
                            
                st.file_uploader("Import JSON", type=['json'], key='uploader_json')
                st.button("📥 Charger le Projet / Config", on_click=import_project_callback)

    st.markdown("---")
    
    # 2. Ligne Navigation : Mode & Liste Configs
    c_mode, c_list = st.columns([2.5, 1.5]) # V74 Fix: More space to right
    
    with c_mode:
        # MODE SWITCH
        nav_options = ["Menuiserie", "Volet Roulant", "Vitrage", "Habillage"]
        current_mode = st.session_state.get('mode_module', 'Menuiserie')
        
        # Ensure valid
        if current_mode not in nav_options: current_mode = "Menuiserie"
        
        user_mode = st.radio("Module", nav_options, index=nav_options.index(current_mode), horizontal=True, label_visibility="collapsed", key="nav_mode_top")
        
        if user_mode != current_mode:
            st.session_state['mode_module'] = user_mode
            # REVERTED V77: Do NOT clear active config on switch, as user perceives it as data loss.
            # We accept that "Repère 1" stays active even if we switch module views.
            st.rerun()
            
    with c_list:
        configs = st.session_state['project']['configs']
        
        # V74 FIX: Unified List (User Request)
        filtered_configs = configs 
        
        if not filtered_configs:
            options = {}
        else:
            options = {c['id']: f"{c['ref']}" for c in filtered_configs}
            
        if options:
            # Handle pending selection
            if 'pending_new_id' in st.session_state:
                target_id = st.session_state.pop('pending_new_id')
                if target_id in options:
                    st.session_state['mgr_sel_id'] = target_id
            
            # Ensure valid selection
            if 'mgr_sel_id' not in st.session_state or st.session_state['mgr_sel_id'] not in options:
                st.session_state['mgr_sel_id'] = list(options.keys())[0]
                
            sel_id = st.session_state['mgr_sel_id']
            
            # STATE MACHINE FOR CONFIRMATION
            # Helper to clear state
            def clear_confirm():
                 st.session_state.pop('confirm_action', None)
                 st.session_state.pop('confirm_target_id', None)
                 
            # Check if we are in confirmation mode for THIS selected item (or generic)
            current_action = st.session_state.get('confirm_action')
            target_id = st.session_state.get('confirm_target_id')
            
            if current_action and target_id == sel_id:
                 # SHOW CONFIRMATION UI (FULL WIDTH of c_list)
                 # Avoid splitting columns to maximize space for the warning message
                 
                 ref_name = options.get(target_id, "???")
                 if current_action == 'open':
                     msg = f"⚠️ Ouvrir **{ref_name}** ?"
                     sub_msg = "Non sauvegardé = Perdu"
                 else:
                     msg = f"🗑️ Supprimer **{ref_name}** ?"
                     sub_msg = "Irréversible"
                     
                 # Compact Warning Box
                 with st.container(border=True):
                     st.write(f"{msg}")
                     st.caption(f"({sub_msg})")
                     
                     cc_yes, cc_no = st.columns(2)
                     
                     # DEFINE CALLBACKS
                     def on_confirm_open(tid):
                         target = next((c for c in configs if c['id'] == tid), None)
                         if target:
                              # CLEANUP 
                              keys_to_cl = [k for k in st.session_state.keys() if k.startswith(("vr_", "men_", "hab_", "vit_", "active_reference", "vr_ref_in"))]
                              for k in keys_to_cl: del st.session_state[k]
                              
                              deserialize_config(target["data"])
                              st.session_state['active_config_id'] = target['id']
                              st.session_state.get('pending_updates', {})['ref_id'] = target['ref'] 
                              
                              # Mode switch
                              st.session_state['mode_module'] = target['data'].get('mode_module', 'Menuiserie')
                              st.session_state['ui_reset_counter'] = st.session_state.get('ui_reset_counter', 0) + 1
                              st.session_state.pop('confirm_action', None)
                              

                     def on_confirm_delete(tid):
                         if 'project' in st.session_state and 'configs' in st.session_state['project']:
                             # 1. Mutate
                             st.session_state['project']['configs'] = [
                                 c for c in st.session_state['project']['configs'] if c['id'] != tid
                             ]
                             # 2. Clear
                             st.session_state['mgr_sel_id'] = None
                             if st.session_state.get('active_config_id') == tid:
                                  st.session_state['active_config_id'] = None
                                  st.session_state['clean_config_snapshot'] = None
                                  if 'ref_id' in st.session_state: del st.session_state['ref_id']
                             
                             st.session_state.pop('confirm_action', None)
                     
                     # CONDITIONAL BUTTON RENDER
                     if current_action == 'open':
                         st.button("✅ OUI", use_container_width=True, key="btn_yes_open", on_click=on_confirm_open, args=(target_id,))
                     else:
                         st.button("✅ OUI", use_container_width=True, key="btn_yes_del", on_click=on_confirm_delete, args=(target_id,))
                             
                     if cc_no.button("❌ NON", use_container_width=True, key="btn_no"):
                         clear_confirm()
                         st.rerun()
                     
            else:
                 # STANDARD UI (Selector + Buttons)
                 c_l_sel, c_l_btn = st.columns([1.2, 0.8])
                 
                 sel_id = c_l_sel.selectbox(
                    "Configurations", 
                    options.keys(), 
                    format_func=lambda x: options[x], 
                    key='mgr_sel_id', 
                    label_visibility="collapsed"
                 )
                 
                 with c_l_btn:
                     cb_open, cb_del = st.columns(2)
                     if cb_open.button("📂", use_container_width=True, help="Ouvrir"):
                        # REVERT TO DIRECT LOGIC (V76 Fix - Critical)
                        # We bypass the dirty check because it is unreliable (likely serialization mismatch).
                        # We force load the target configuration directly.
                        # This satisfies "No double click if no changes" (by removing double click entirely for now to fix the bug)
                        # Ideally we would check `is_dirty` but it seems to be failing.
                        
                        target = next((c for c in configs if c['id'] == sel_id), None)
                        if target:
                             # CLEANUP OLD KEYS (Crucial for context switch)
                             keys_to_clear = [k for k in st.session_state.keys() if k.startswith(("vr_", "men_", "hab_", "vit_", "active_reference", "vr_ref_in"))]
                             for k in keys_to_clear: del st.session_state[k]
                             
                             deserialize_config(target["data"])
                             st.session_state['active_config_id'] = target['id']
                             st.session_state['ref_id'] = target['ref']
                             st.session_state['vr_ref_in'] = target['ref']
                             
                             new_mode = target['data'].get('mode_module', 'Menuiserie')
                             st.session_state['mode_module'] = new_mode
                             
                             st.toast(f"✅ Ouverture de '{target['ref']}'")
                             st.session_state['ui_reset_counter'] = st.session_state.get('ui_reset_counter', 0) + 1
                             st.rerun()
                        
                     if cb_del.button("🗑️", use_container_width=True, help="Supprimer"):
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
    Parcourt toutes les configurations pour trouver le prochain numéro.
    V10 STRICT: Harmonisation globale "Repère N" (1, 2, 3...)
    Ignorer les préfixes exotiques (V-, F-).
    """
    import re
    max_num = 0
    
    # Analyze all existing refs to find ANY number 
    # to continue the sequence "Repère N"
    if 'project' in st.session_state and 'configs' in st.session_state['project']:
        configs = st.session_state['project']['configs']
        for cfg in configs:
            ref = cfg.get('ref', '')
            # Capture any trailing number
            match = re.search(r'(\d+)\s*$', ref)
            if match:
                try:
                    num = int(match.group(1))
                    if num > max_num: max_num = num
                except:
                    pass

    next_num = max_num + 1
    
    # STRICT FORMAT: "Repère N"
    return f"Repère {next_num}"

def get_next_ref(current_ref):
    """
    Incrémente la partie numérique d'une référence spécifique (Locale).
    Utilisé si on veut incrémenter par rapport à ce qu'on vient de saisir.
    MAIS le client veut une harmonisation globale.
    """
    return get_next_project_ref() # OVERRIDE TO USE GLOBAL LOGIC

# --- HELPER: GENERATION DU SVG (PARTIE 3 - CUSTOM PROFILES) ---
TYPES_OUVRANTS = ["Fixe", "1 Vantail", "2 Vantaux", "Coulissant", "Soufflet"]

# Listes de données Vitrage (NEW V75)
EPAISSEURS = ["3 mm", "4 mm", "5 mm", "6 mm", "8 mm", "10 mm", "12 mm"]
FEUILLETES = ["33.2", "44.2", "SP10", "55.2", "SP512", "66.2", "SP514", "SP615B", "88.2", "10.10.2", "12.12.2"]
ALL_GLASS = EPAISSEURS + FEUILLETES

TYPES_VERRE = ["Clair", "Imprimé 200", "Dépoli", "Armé", "Trempé"]

VIDE_AIR = ["6 mm", "8 mm", "10 mm", "12 mm", "14 mm", "16 mm", "18 mm", "20 mm", "24 mm"]

INTERCALAIRES = [
    "Alu Standard", "Alu Blanc", "Alu Noir",
    "Warm Edge Noir", "Warm Edge Blanc",
    "Swisspacer Blanc", "Swisspacer Noir"
]

# Règles de couches
COUCHES_INT = ["Aucune", "FE (Faible Émissivité)"]
COUCHES_EXT = ["Aucune", "SUN", "CS 70/30", "CS 60/40"]

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
        ct1, ct2 = st.columns(2)
        p['traverses'] = ct1.number_input("Traverses Horiz.", 0, 10, 0, key=f"{key_prefix}_trav")
        p['traverses_v'] = ct2.number_input("Traverses Vert.", 0, 10, 0, key=f"{key_prefix}_trav_v")
        
        nb_h = p['traverses']
        nb_v = p['traverses_v']
        
        if nb_h > 0 or nb_v > 0:
            # Common Thickness
            p['epaisseur_traverse'] = st.number_input("Épaisseur Traverse (mm)", 10, 100, 20, step=5, key=f"{key_prefix}_eptrav")
            
            # MODE SOUBASSEMENT (Strictly 1 H, 0 V)
            if nb_h == 1 and nb_v == 0:
                p['pos_traverse'] = st.radio("Position", ["Centrée", "Sur mesure (du bas)"], horizontal=True, key=f"{key_prefix}_pos_t")
                if p['pos_traverse'] == "Sur mesure (du bas)":
                    p['h_traverse_custom'] = st.number_input("Cote axe depuis bas (mm)", 100, 2000, 800, 10, key=f"{key_prefix}_h_t")
                cr1, cr2 = st.columns(2)
                p['remp_haut'] = cr1.radio("Remplissage HAUT", ["Vitrage", "Panneau"], key=f"{key_prefix}_rh")
                p['remp_bas'] = cr2.radio("Remplissage BAS", ["Panneau", "Vitrage"], key=f"{key_prefix}_rb")
            else:
                # MODE PETITS BOIS (Grid)
                st.info(f"Grille décorative : {nb_h} Horiz. x {nb_v} Vert.")
                p['remplissage_global'] = st.radio("Remplissage Global", ["Vitrage", "Panneau"], horizontal=True, key=f"{key_prefix}_rg_grid")
        else:
            p['remplissage_global'] = st.radio("Remplissage Global", ["Vitrage", "Panneau"], horizontal=True, key=f"{key_prefix}_rg")
        
        st.markdown("🔍 **Composition Vitrage**")
        
        # --- NEW GLAZING CONFIGURATION ---
        
        # 1. Selection Mode: Simple vs Double
        p['type_vitrage'] = st.radio("Type de Vitrage", ["Double Vitrage", "Simple Vitrage"], horizontal=True, key=f"{key_prefix}_tv")
        
        if p['type_vitrage'] == "Double Vitrage":
            c_v1, c_v2, c_v3 = st.columns(3)
            
            # COL 1 : EXTERIEUR (Swapped as requested)
            with c_v1:
                st.caption("Extérieur")
                # Default: 4mm (Index 1), Clair (Index 0)
                p['vitrage_ext_ep'] = st.selectbox("Épaisseur Ext", ALL_GLASS, index=1, key=f"{key_prefix}_veep")
                p['vitrage_ext_type'] = st.selectbox("Type Ext", TYPES_VERRE, index=0, key=f"{key_prefix}_vety")
                p['vitrage_ext_couche'] = st.selectbox("Couche Ext", COUCHES_EXT, index=0, key=f"{key_prefix}_veco")
                
            # COL 2 : INTERCALAIRE / AIR
            with c_v2:
                st.caption("Lame d'Air")
                # Default: 20mm (Index 7), Warm Edge Noir (Index 3)
                p['vide_air_ep'] = st.selectbox("Épaisseur Air", VIDE_AIR, index=7, key=f"{key_prefix}_vae")
                p['intercalaire_type'] = st.selectbox("Intercalaire", INTERCALAIRES, index=3, key=f"{key_prefix}_intc")
                
            # COL 3 : INTERIEUR
            with c_v3:
                st.caption("Intérieur")
                # Default: 4mm (Index 1), Clair (Index 0), FE (Index 1)
                p['vitrage_int_ep'] = st.selectbox("Épaisseur Int", ALL_GLASS, index=1, key=f"{key_prefix}_viep")
                p['vitrage_int_type'] = st.selectbox("Type Int", TYPES_VERRE, index=0, key=f"{key_prefix}_vity")
                p['vitrage_int_couche'] = st.selectbox("Couche Int", COUCHES_INT, index=1, key=f"{key_prefix}_vico")
            
            # FORMULA GENERATION: "4 / 20 / 4FE - WARM EDGE NOIR + GAZ ARGON"
            ep_ext = p['vitrage_ext_ep'].replace(' mm', '').strip()
            # Clean Couche Ext
            c_ext = p['vitrage_ext_couche']
            c_ext_str = "" if c_ext == "Aucune" else c_ext.replace("CS ", "CS").split(' ')[0] # Simplify
            
            air = p['vide_air_ep'].replace(' mm', '').strip()
            
            ep_int = p['vitrage_int_ep'].replace(' mm', '').strip()
            # Clean Couche Int
            c_int = p['vitrage_int_couche']
            c_int_str = "" if c_int == "Aucune" else "FE" # Force FE notation
            
            inter = p['intercalaire_type'].upper()
            
            # Build parts
            # Ext part: "4" or "4SUN"
            part_ext = f"{ep_ext}{c_ext_str}"
            # Int part: "4FE"
            part_int = f"{ep_int}{c_int_str}"
            
            p['vitrage_resume'] = f"{part_ext} / {air} / {part_int} - {inter} + GAZ ARGON"
            
        else: # Simple Vitrage
            c_v1, _ = st.columns([1, 2])
            with c_v1:
                st.caption("Vitrage Unique")
                p['vitrage_simple_ep'] = st.selectbox("Épaisseur", ALL_GLASS, key=f"{key_prefix}_vsep")
                p['vitrage_simple_type'] = st.selectbox("Type", TYPES_VERRE, key=f"{key_prefix}_vsty")
                p['vitrage_simple_couche'] = st.selectbox("Couche", ["Aucune", "FE", "SUN", "CS 70/30"], key=f"{key_prefix}_vsco")
            
            p['vitrage_resume'] = f"{p['vitrage_simple_ep']} {p['vitrage_simple_type']} {p['vitrage_simple_couche']}"

        # Compatibility Keys (Keep existing keys for SVG if needed)
        p['vitrage_ext'] = p.get('vitrage_ext_type', 'V.Ext') 
        p['vitrage_int'] = p.get('vitrage_int_type', 'V.Int')

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
            # Default to 0 to avoid huge gaps (User Feedback: "70mm en trop")
            # The sash frame itself provides visual thickness.
            
            # MIGRATION: If value is 70 (Old Default), force it to 0
            current_th = int(node.get('traverse_thickness', 0))
            if current_th == 70:
                node['traverse_thickness'] = 0
                
            if 'traverse_thickness' not in node:
                node['traverse_thickness'] = 0
                
            node['traverse_thickness'] = st.number_input(
                "Épaisseur Traverse / Meneau (mm)", 
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
    
    # V9 FIX: AGGRESSIVE VITRAGE RESET
    # Explicitly set WIDGET keys to Default Values to force UI reset
    st.session_state['vit_w'] = 1000
    st.session_state['vit_h'] = 1000
    st.session_state['vit_ref_in'] = st.session_state['ref_id']
    st.session_state['vit_qte_in'] = 1
    
    # Also clear other keys just in case
    extra_keys = ['vit_obs_in', 'vit_hb']
    for k in extra_keys:
        if k in st.session_state: del st.session_state[k]
    
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
    # V77 FIX: Fully Proportional Dimensions
    # Derive tick size and layout spacing from font_size to ensure visibility at all scales
    tick_size = font_size * 0.4  # e.g. 24 -> 10, 60 -> 24
    text_gap = font_size * 0.6   # e.g. 24 -> 15
    stroke_w = max(1, int(font_size * 0.05)) # Scale stroke slightly (1..3)
    
    display_text = f"{text_prefix}{int(value)}"
    
    if orientation == "H":
        y_line = y1 + offset 
        draw_rect(svg_content, x1, y_line, x2-x1, stroke_w+1, "black", "black", 0, z_index)
        
        # Lignes de rappel
        start_y1 = leader_fixed_start if leader_fixed_start is not None else y1
        start_y2 = leader_fixed_start if leader_fixed_start is not None else y2
        
        svg_content.append((z_index, f'<line x1="{x1}" y1="{start_y1}" x2="{x1}" y2="{y_line + tick_size}" stroke="black" stroke-width="{stroke_w}" stroke-dasharray="{stroke_w*4},{stroke_w*4}" />'))
        svg_content.append((z_index, f'<line x1="{x2}" y1="{start_y2}" x2="{x2}" y2="{y_line + tick_size}" stroke="black" stroke-width="{stroke_w}" stroke-dasharray="{stroke_w*4},{stroke_w*4}" />'))
        draw_text(svg_content, (x1 + x2) / 2, y_line - text_gap, display_text, font_size=font_size, weight="bold", z_index=z_index)
    elif orientation == "V":
        x_line = x1 - offset
        # V79 FIX: Ensure height is positive for rect
        h_line = y2 - y1
        y_rect = y1
        if h_line < 0:
            h_line = abs(h_line)
            y_rect = y2
        draw_rect(svg_content, x_line, y_rect, stroke_w+1, h_line, "black", "black", 0, z_index)
        
        start_x1 = leader_fixed_start if leader_fixed_start is not None else x1
        start_x2 = leader_fixed_start if leader_fixed_start is not None else x2

        svg_content.append((z_index, f'<line x1="{start_x1}" y1="{y1}" x2="{x_line - tick_size}" y2="{y1}" stroke="black" stroke-width="{stroke_w}" stroke-dasharray="{stroke_w*4},{stroke_w*4}" />'))
        svg_content.append((z_index, f'<line x1="{start_x2}" y1="{y2}" x2="{x_line - tick_size}" y2="{y2}" stroke="black" stroke-width="{stroke_w}" stroke-dasharray="{stroke_w*4},{stroke_w*4}" />'))
        
        txt_x = x_line - text_gap
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

def draw_sash_content(svg, x, y, w, h, type_ouv, params, config_global, z_base=10, font_dim_ref=16):
    c_frame = config_global['color_frame']
    vis_ouvrant = 55 
    
    # Helper interne pour dessiner un "bloc vitré/panneau"
    def draw_leaf_interior(lx, ly, lw, lh, z_start=None):
        nb_h = params.get('traverses', 0)
        nb_v = params.get('traverses_v', 0)
        z_eff = z_start if z_start is not None else z_base
        
        # MODE SOUBASSEMENT (Strictly 1 H, 0 V)
        if nb_h == 1 and nb_v == 0:
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
            ltx = lx + lw - 30 
            if pos_trav == "Sur mesure (du bas)":
               # Cote depuis le bas
               draw_dimension_line(svg, ltx, y_center, ltx, ly+lh, h_custom, "", -10, "V", font_size=font_dim_ref, z_index=z_eff+10)
            else:
               h_reel_bas = (ly+lh) - y_center
               draw_dimension_line(svg, ltx, y_center, ltx, ly+lh, h_reel_bas, "", -10, "V", font_size=font_dim_ref, z_index=z_eff+10)

        else:
            # MODE GLOBAL / PETITS BOIS (GRID)
            remp_glob = params.get('remplissage_global', 'Vitrage') or params.get('remplissage_global', 'Vitrage') # Fallback
            # Note: config_zone_ui uses 'remplissage_global' for grid too.
            
            col_g = "#F0F0F0" if remp_glob == "Panneau" else config_global['color_glass']
            draw_rect(svg, lx, ly, lw, lh, col_g, "black", 1, z_eff+1)
            
            # Only draw grid if there are traverses
            if nb_h > 0 or nb_v > 0:
                ep_trav = params.get('epaisseur_traverse', 20)
                
                # DRAW HORIZONTAL
                if nb_h > 0:
                    section_h = lh / (nb_h + 1)
                    for k in range(1, nb_h + 1):
                        ty = ly + (section_h * k) - (ep_trav/2)
                        draw_rect(svg, lx, ty, lw, ep_trav, c_frame, "black", 1, z_eff+2)
                
                # DRAW VERTICAL
                if nb_v > 0:
                    section_w = lw / (nb_v + 1)
                    for k in range(1, nb_v + 1):
                        tx = lx + (section_w * k) - (ep_trav/2)
                        # Vertical bar spans full height (crosses horizontal)
                        # Or should it be cut? Usually petits bois are continuous or mortised.
                        # Drawing V on top or below H implies joint type. To keep simple, draw V full height.
                        draw_rect(svg, tx, ly, ep_trav, lh, c_frame, "black", 1, z_eff+2)

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

def render_html_habillage(cfg, svg_string, logo_b64, dev_val, schema_b64):
    # Pre-calc Observations
    obs_hab_html = ""
    if st.session_state.get('hab_obs'):
        obs_hab_html = f"""
            <div class="section-block">
                <h3>Observations</h3>
                <div class="panel">
                    <div class="panel-row" style="display:block; min-height:auto; padding:10px;"><span class="val" style="text-align:left; width:100%; white-space: pre-wrap;">{st.session_state.get('hab_obs')}</span></div>
                </div>
            </div>
        """
    """HTML generation for Habillage printing (Single Page, Compact, Logo Header)."""
    
    css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
        body { font-family: 'Roboto', sans-serif; -webkit-print-color-adjust: exact; padding: 0; margin: 0; background-color: #fff; color: #333; }
        
        .page-container { 
            max-width: 210mm; 
            margin: 0 auto; 
            padding: 20px;
        }

        /* HEADER */
        .header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; border-bottom: 3px solid #2c3e50; padding-bottom: 15px; }
        .header-left img { max-height: 70px; width: auto; }
        .header-left .subtitle { color: #3498db; font-size: 14px; margin-top: 5px; font-weight: 400; }
        
        .header-right { text-align: right; padding-right: 5px; }
        .header-right .label { font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 2px; }
        .header-right .ref { font-size: 24px; font-weight: bold; color: #000; margin-bottom: 2px; line-height: 1; }
        .header-right .date { font-size: 11px; color: #666; }

        /* GRID LAYOUT */
        .grid-container { display: grid; grid-template-columns: 35% 60%; gap: 5%; margin-bottom: 20px; }
        
        /* HEADINGS */
        h3 { 
            font-size: 14px; color: #2c3e50; margin: 0 0 10px 0; 
            border-left: 4px solid #3498db; padding-left: 8px; 
            line-height: 1.2;
        }
        
        /* PANELS */
        .panel { background: #f9f9f9; padding: 10px; border-radius: 4px; font-size: 12px; }
        .panel-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid #eee; }
        .panel-row:last-child { border-bottom: none; }
        .panel-row .lbl { font-weight: bold; color: #555; }
        .panel-row .val { font-weight: normal; color: #000; text-align: right; }
        
        .schema-box { 
            border: 1px solid #eee; border-radius: 4px; padding: 5px; 
            text-align: center; height: 160px; display: flex; align-items: center; justify-content: center;
            margin-bottom: 15px;
        }
        .schema-box img { max-width: 100%; max-height: 100%; object-fit: contain; }
        
        .visual-box {
            border: 1px solid #eee; border-radius: 4px; height: 280px;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            position: relative;
        }
        .visual-box svg { max-height: 250px; width: auto; max-width: 95%; }
        
        /* TABLE DETAILS */
        table { width: 100%; border-collapse: collapse; font-size: 11px; margin-top: 10px; }
        th { background: #2c3e50; color: white; padding: 6px; text-align: left; text-transform: uppercase; font-size: 10px; }
        td { border-bottom: 1px solid #eee; padding: 6px; color: #444; }
        tr:nth-child(even) { background-color: #f8f9fa; }
        
        .footer { 
            margin-top: 25px; border-top: 1px solid #eee; padding-top: 10px; 
            font-size: 9px; color: #999; text-align: center; 
        }

        @media print {
            @page { size: A4; margin: 5mm; }
            body { padding: 0; background: white; -webkit-print-color-adjust: exact; }
            .page-container { margin: 0; padding: 0; box-shadow: none; max-width: none; width: 100%; transform: scale(0.95); transform-origin: top center; }
            .no-print { display: none; }
        }
    </style>
    """
    
    # Precompute
    import datetime
    prof_name = cfg['prof']['name']
    
    # Dims string logic
    exclude_keys = ['ref', 'qte', 'length', 'finition', 'epaisseur', 'couleur', 'modele']
    dim_str_display = ", ".join([f"{k}={v}" for k,v in cfg['inputs'].items() if k not in exclude_keys])
    
    # Surface
    try:
        surface = (dev_val * cfg['length'] * cfg['qte']) / 1000000
    except:
        surface = 0

    # Schema Image HTML
    schema_html = ""
    if schema_b64:
        schema_html = f'<img src="data:image/jpeg;base64,{schema_b64}">'
    else:
        schema_html = '<span style="color:#ccc;">Aucune image</span>'

    # Logo HTML (Replaces Title)
    logo_html = f"<h1>Fiche Technique</h1>"
    if logo_b64:
        logo_html = f'<img src="data:image/jpeg;base64,{logo_b64}" alt="Logo">'

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{css}</head>
    <body>
        <div class="page-container">
            <!-- HEADER -->
            <div class="header">
                <div class="header-left">
                    {logo_html}
                    <div class="subtitle">{prof_name}</div>
                </div>
                <div class="header-right">
                    <div class="label">RÉFÉRENCE CHANTIER</div>
                    <div class="ref">{cfg['ref']}</div>
                    <div class="date">{datetime.datetime.now().strftime('%d/%m/%Y')}</div>
                </div>
            </div>
            
            <!-- MAIN GRID -->
            <div class="grid-container">
                <!-- LEFT COLUMN -->
                <div>
                    <h3>Schéma de Principe</h3>
                    <div class="schema-box">
                        {schema_html}
                    </div>
                    
                    <h3>Caractéristiques</h3>
                    <div class="panel">
                        <div class="panel-row"><span class="lbl">Quantité</span> <span class="val">{cfg['qte']}</span></div>
                        <div class="panel-row"><span class="lbl">Longueur</span> <span class="val">{cfg['length']} mm</span></div>
                        <div class="panel-row"><span class="lbl">Développé</span> <span class="val">{int(dev_val)} mm</span></div>
                        <div class="panel-row"><span class="lbl">Matière</span> <span class="val">{cfg['finition']}</span></div>
                        <div class="panel-row"><span class="lbl">Couleur</span> <span class="val">{cfg['couleur']}</span></div>
                        <div class="panel-row"><span class="lbl">Épaisseur</span> <span class="val">{cfg['epaisseur']}</span></div>
                        
                        <div style="margin-top:10px; padding-top:10px; border-top:1px solid #ddd;">
                            <span class="lbl">Dimensions :</span> <br>
                            <span style="font-family:monospace; color:#333;">{dim_str_display}</span>
                        </div>
                    </div>
                </div>
                
                <!-- RIGHT COLUMN -->
                <div>
                    <h3>Visualisation 3D</h3>
                    <div class="visual-box">
                        {svg_string}
                        <div style="position:absolute; bottom:10px; font-size:10px; color:#aaa;">Vue filaire indicative</div>
                    </div>
                </div>
            </div>
            
            <!-- OBSERVATIONS -->
            <!-- OBSERVATIONS -->
            {obs_hab_html}
            
            <!-- FOOTER TABLE -->
            <h3>Détails de Commande</h3>
            <table>
                <thead>
                    <tr><th>Libellé</th><th style="text-align:right;">Valeur</th></tr>
                </thead>
                <tbody>
                    <tr><td>Référence</td><td style="text-align:right;">{cfg['ref']}</td></tr>
                    <tr><td>Modèle</td><td style="text-align:right;">{prof_name}</td></tr>
                    <tr><td>Quantité</td><td style="text-align:right;">{cfg['qte']}</td></tr>
                    <tr><td>Dimensions</td><td style="text-align:right;">{dim_str_display}</td></tr>
                    <tr><td>Longueur</td><td style="text-align:right;">{cfg['length']} mm</td></tr>
                    <tr><td>Développé</td><td style="text-align:right;">{int(dev_val)} mm</td></tr>
                    <tr><td>Surface Totale</td><td style="text-align:right;">{surface:.2f} m²</td></tr>
                </tbody>
            </table>
            
            <div class="footer">
                Document généré automatiquement - Miroiterie Yerroise<br>
                Merci de vérifier les cotes avant validation définitive.
            </div>
        </div>
        <script>
            setTimeout(() => {{ window.print(); }}, 800);
        </script>
    </body>
    </html>
    """
    return html

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

    # --- PRINT BUTTON (HTML) ---
    st.markdown("---")
    if st.button("🖨️ Imprimer", key="btn_print_hab"):
        # Import helper (or define it in app.py)
        # For simplicity, we inline the logic or assume the function is pasted in app.py
        # Since I wrote it to a separate file, I should read it or paste it. 
        # But wait, I can just define it inside app.py for simplicity as requested by user constraints (single file preference?)
        # Let's assume I actually put `render_html_habillage` IN app.py in a previous step or will do it now.
        # I'll put the function definition at the top of app.py or near render_html_template.
        
        # Prepare Schema B64 (Restored)
        schema_b64 = ""
        img_p = os.path.join(ARTIFACT_DIR, prof['image_key'])
        if os.path.exists(img_p):
             import base64
             with open(img_p, "rb") as f:
                 schema_b64 = base64.b64encode(f.read()).decode()

        st.session_state['print_ts_hab'] = datetime.datetime.now().isoformat()
        
        # Pass SVG, Logo (Global), Dev, and Schema
        html_content = render_html_habillage(cfg, svg, LOGO_B64, dev, schema_b64)
        html_content += f"<!-- TS: {st.session_state['print_ts_hab']} -->"
        
        import streamlit.components.v1 as components
        components.html(html_content, height=0, width=0)
        st.info(f"Impression lancée... ({st.session_state['print_ts_hab'].split('T')[1][:8]})")

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
        if st.session_state.get('hab_obs'):
            st.markdown("---")
            st.markdown(f"**Observations** : {st.session_state.get('hab_obs')}")
        
    with col_export:
        st.write("")
        st.write("")
        
        # JSON EXPORT
        hab_data = {
            "ref": cfg['ref'], "modele": prof['name'], "qte": cfg['qte'],
            "dims": cfg['inputs'], "longueur": cfg['length'], "developpe": dev,
            "finition": cfg['finition'], "epaisseur": cfg['epaisseur'], "couleur": cfg['couleur'],
            "observations": st.session_state.get('hab_obs', '')
        }
        json_hab = json.dumps(hab_data, indent=2, ensure_ascii=False)
        st.download_button("💾 Export JSON", json_hab, f"habillage_{cfg['ref']}.json", "application/json", use_container_width=True)

        # Legacy HTML Report Removed (Cleaned up)
        pass

def render_habillage_form():
    """Renders the Sidebar inputs for Habillage and returns the config dict."""
    config = {}
    
    # Reset Mechanism: Visible Suffix (Robust)
    # Using visible dots to force reset.
    ctr = st.session_state.get('ui_reset_counter', 0)
    # DEBUG - REMOVE AFTER VERIFICATION
    # st.write(f"DEBUG REST CTR: {ctr}") 
    
    suffixes = ["", " .", " ..", " ..."]
    reset_suffix = suffixes[ctr % 4]
    
    # 0. Identification
    with st.expander(f"📝 1. Repère et quantité{reset_suffix}", expanded=False):
        c_ref, c_qte = st.columns([3, 1])
        
        # HANDLE PENDING REF UPDATE (Fix StreamlitAPIException)
        if 'pending_ref_id' in st.session_state:
            st.session_state['ref_id'] = st.session_state.pop('pending_ref_id')
            
        base_ref = st.session_state.get('ref_id', get_next_project_ref())
        # Ensure key exists to avoid warning
        if 'ref_id' not in st.session_state:
            st.session_state['ref_id'] = base_ref

        # Removed `value` argument because key is present in session_state
        ref_chantier = c_ref.text_input("Référence", key="ref_id")
        qte_piece = c_qte.number_input("Qté", 1, 100, 1, key="qte_val")
        config["ref"] = ref_chantier
        config["qte"] = qte_piece

    # 1. Model Selection
    profile_keys = list(PROFILES_DB.keys())
    model_labels = {k: PROFILES_DB[k]["name"] for k in profile_keys}
    
    with st.expander(f"📐 2. Modèle & Dimensions{reset_suffix}", expanded=False):
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
    with st.expander(f"🎨 3. Finition{reset_suffix}", expanded=False):
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
    
    # 4. Observations
    with st.expander(f"📝 4. Observations{reset_suffix}", expanded=False):
        c_obs = st.container()
        st.session_state['hab_obs'] = c_obs.text_area("Notes", value=st.session_state.get('hab_obs', ''), key="hab_obs_in")
    
    # --- ACTIONS ---
    st.markdown("### 💾 Actions")
    
    # 0. Show Edition Status
    active_id = st.session_state.get('active_config_id')
    if active_id:
        # Check if active is Habillage?
        # Yes, because we loaded it.
        st.caption(f"✏️ Édition en cours : {st.session_state.get('ref_id', '???')}")
        
    c_btn0, c_btn1, c_btn2 = st.columns(3)
    
    # ACTION: UPDATE (Only if active file)
    # V75 UPDATE: Consolidated "Enregistrer" Button
    c_btn0, c_btn1, c_btn2 = st.columns(3)
    
    # 1. ENREGISTRER (Save current state, whether New or Existing)
    if c_btn0.button("💾 Enregistrer", use_container_width=True, help="Sauvegarder la configuration actuelle"):
         data = serialize_config()
         data['mode_module'] = 'Habillage' 
         
         if active_id:
             # UPDATE EXISTING
             current_ref = st.session_state.get('ref_id', 'Repère 1')
             update_current_config_in_project(active_id, data, current_ref)
             
             # Update Snapshot
             st.session_state['clean_config_snapshot'] = get_config_snapshot(data)
             
             st.toast(f"✅ {current_ref} mis à jour !")
             st.rerun()
         else:
             # CREATE NEW
             new_ref = st.session_state.get('ref_id', 'Repère 1')
             new_id = add_config_to_project(data, new_ref)
             
             # Set as Active
             st.session_state['active_config_id'] = new_id
             
             # Update Snapshot
             st.session_state['clean_config_snapshot'] = get_config_snapshot(data)
             
             st.toast(f"✅ {new_ref} enregistré !")
             st.rerun()
    
    # 1. Dupliquer (Save Copy)
    if c_btn1.button("Dupliquer", use_container_width=True, key="hab_btn_add", help="Créer une copie"):
        data = serialize_config()
        data['mode_module'] = 'Habillage'
        
        current_ref = st.session_state.get('ref_id', 'H1')
        new_ref = f"{current_ref} (Copie)"
        
        new_id = add_config_to_project(data, new_ref)
        
        # Switch to duplicate
        st.session_state['active_config_id'] = new_id
        
        # V76 Fix: Use pending_updates for widget keys
        if 'pending_updates' not in st.session_state: st.session_state['pending_updates'] = {}
        st.session_state['pending_updates']['ref_id'] = new_ref

        st.session_state['clean_config_snapshot'] = get_config_snapshot(data)
        
        st.toast(f"✅ Copie créée : {new_ref}")
        st.rerun()

    # 2. Nouveau (Reset)
    if c_btn2.button("Nouveau (Reset)", use_container_width=True, key="hab_btn_new", help="Sauvegarder et Réinitialiser"):
        data = serialize_config()
        data['mode_module'] = 'Habillage'
        current_ref = st.session_state.get('ref_id', 'Repère 1')
        
        if active_id:
            # UPDATE EXISTING
            update_current_config_in_project(active_id, data, current_ref)
            st.toast(f"✅ {current_ref} mis à jour !")
        else:
            # CREATE NEW
            add_config_to_project(data, current_ref)
            st.toast(f"✅ {current_ref} enregistré !")
        
        # Reset but DO NOT RERUN yet
        reset_config(rerun=False)
        st.session_state['clean_config_snapshot'] = None
        st.session_state['active_config_id'] = None
        
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
    with st.expander("📝 1. Repère et quantité", expanded=False):
        c1, c2 = st.columns([3, 1])
        
        # HANDLE PENDING REF UPDATE (Fix StreamlitAPIException)
        if 'pending_ref_id' in st.session_state:
            st.session_state['ref_id'] = st.session_state.pop('pending_ref_id')
            
        rep = c1.text_input("Repère", st.session_state.get('ref_id', get_next_project_ref()), key="ref_id")
        qte = c2.number_input("Qté", 1, 100, 1, key="qte_val")

    # --- SECTION 2 : MATERIAU ---
    # --- SECTION 2 : MATERIAU ---
    # --- SECTION 2 : MATERIAU ---
    with st.expander("🧱 2. Matériau & Ailettes", expanded=False):
        # 1. PROJET (Left) & MATERIAU (Right)
        c_m1, c_m2 = st.columns(2)
        type_projet = c_m1.radio("Type de Projet", ["Rénovation", "Neuf"], index=0, horizontal=True, key="proj_type")
        mat = c_m2.radio("Matériau", ["PVC", "ALU"], horizontal=True, key="mat_type")

        # Color Logic handled below in section 6

        st.markdown("<hr style='margin:5px 0'>", unsafe_allow_html=True)

        # 2. TYPE DE POSE & DORMANT
        c_pose1, c_pose2 = st.columns([2, 1])
        
        if type_projet == "Rénovation":
            liste_pose = ["Pose en rénovation (R)", "Pose en rénovation Dépose Totale (RT)"]
        else:
            liste_pose = ["Pose en applique avec doublage (A)", "Pose en applique avec embrasures (E)", 
                          "Pose en feuillure (F)", "Pose en tunnel nu intérieur (T)", "Pose en tunnel milieu de mur (TM)"]
        
        type_pose = c_pose1.selectbox("Type de Pose", liste_pose, key="pose_type")
        ep_dormant = c_pose2.number_input("Dormant", 50, 200, 70, step=10, help="Largeur visible du profilé", key="frame_thig")
        
        st.markdown("<hr style='margin:5px 0'>", unsafe_allow_html=True)
        
        # 4. AILETTES & SEUIL (Aligned)
        # Checkbox ABOVE to allow perfect alignment of inputs
        bas_identique = st.checkbox("Seuil identique aux ailettes ?", False, key="same_bot")
        
        c_ail1, c_ail2 = st.columns(2)
        ail_val = c_ail1.number_input(f"Ailettes (mm)", min_value=0, value=60, step=5, key="fin_val")
        
        val_bas_input = 0
        if not bas_identique:
             val_bas_input = c_ail2.number_input(f"Seuil (mm)", min_value=0, value=0, step=5, key="fin_bot")
        else:
             # Make it look like a disabled input or just text aligned
             # Using disabled input is better for visual alignment
             c_ail2.number_input(f"Seuil (mm)", value=ail_val, disabled=True, key="fin_bot_disabled")
             
        # 5. APPUI
        # Condensed & Centered: 15px Top push, 0px Bottom manual margin (relies on widget padding)
        st.markdown("<hr style='margin:10px 0 15px 0'>", unsafe_allow_html=True)
        
        # Left Aligned
        is_appui_rap = st.checkbox("Appui Rapporté ?", False, key="is_appui_rap")
        
        if is_appui_rap:
            largeur_appui = st.number_input("Largeur Appui (mm)", 0, 500, 100, step=10, key="width_appui")
        
        # 6. COULEURS
        # Pull bottom line closer
        st.markdown("<hr style='margin:0px 0 10px 0'>", unsafe_allow_html=True)
        cc1, cc2 = st.columns(2)
        
        # DEFINITION DES COULEURS (Market Standards)
        if mat == "PVC":
            liste_couleurs = [
                "Blanc (Masse)",
                "Beige (Masse)",
                "Gris Anthracite (Plaxé 7016)",
                "Chêne Doré (Plaxé)",
                "Autre / RAL Spécifique"
            ]
        else: # ALU
            liste_couleurs = [
                "Blanc Satiné (9016)",
                "Gris Anthracite Texturé (7016)",
                "Noir Sablé (2100)",
                "Gris Pierre de Lune (7035)",
                "AS (Aluminium Standard / Anodisé)",
                "Gris Argent (9006)",
                "Brun (8019)",
                "Autre / RAL Spécifique"
            ]
            
        # INTERIEUR
        sel_c1 = cc1.selectbox("Couleur Int", liste_couleurs, key="col_in_select")
        if sel_c1 == "Autre / RAL Spécifique":
            st.session_state['col_in'] = cc1.text_input("RAL Int.", placeholder="Ex: Rouge 3004", key="col_in_custom")
        else:
            st.session_state['col_in'] = sel_c1
            
        # EXTERIEUR
        sel_c2 = cc2.selectbox("Couleur Ext", liste_couleurs, key="col_ex_select")
        if sel_c2 == "Autre / RAL Spécifique":
            st.session_state['col_ex'] = cc2.text_input("RAL Ext.", placeholder="Ex: Bleu 5003", key="col_ex_custom")
        else:
            st.session_state['col_ex'] = sel_c2

    # --- SECTION 3 : DIMENSIONS ---
    with st.expander("📐 3. Dimensions & VR", expanded=False):
        # New Dimensions Type Dropdown (Removed "Côtes tableau")
        dim_opts = ["Côtes fabrication", "Côtes passage", "Côtes dos de dormant"]
        # Handle Legacy Value if it was set to Tableau
        curr_dim = st.session_state.get('dim_type', "Côtes dos de dormant")
        if curr_dim == "Côtes tableau": 
             curr_dim = "Côtes fabrication"
             
        if curr_dim not in dim_opts: curr_dim = "Côtes dos de dormant"

        dim_type = st.selectbox("Type de Côtes", dim_opts, index=dim_opts.index(curr_dim), key="dim_type")
        c3, c4 = st.columns(2)
        
        # Determine labels based on selection
        lbl_w = "Largeur"
        lbl_h = "Hauteur"
        if "fabrication" in dim_type: lbl_w += " (Fab)"; lbl_h += " (Fab)"
        elif "passage" in dim_type: lbl_w += " (Passage)"; lbl_h += " (Passage)"
        else: lbl_w += " (Dos de Dormant)"; lbl_h += " (Dos de Dormant)"

        l_dos_dormant = c3.number_input(f"{lbl_w} (mm)", 100, 5000, 1000, step=10, key="width_dorm")
        h_dos_dormant = c4.number_input(f"{lbl_h} (mm)", 100, 5000, 1400, step=10, help="Hauteur totale incluant le coffre", key="height_dorm")
        
        # Hauteur d'Allège
        h_allege = st.number_input("Hauteur Allège", 0, 2500, 900, step=10, key="h_allege")

        vr_opt = st.toggle("Volet Roulant", False, key="vr_enable")
        
        # NOUVEAU: Côtes Tableau Extérieur (Sous VR)
        st.markdown("**(Optionnel) Côtes Tableau Extérieur**")
        c_te1, c_te2 = st.columns(2)
        
        # V8 FIX: Smart Defaults for Tableau (Tunnel/Gap)
        # User Rule: If Frame=1000, Tableau=1020. (+20mm Total => +10mm Gap/Side)
        if st.session_state.get('men_w_ex_in', 0) == 0:
             st.session_state['men_w_ex_in'] = l_dos_dormant + 20
        
        if st.session_state.get('men_h_ex_in', 0) == 0:
             st.session_state['men_h_ex_in'] = h_dos_dormant + 20

        st.session_state['men_w_tab_ex'] = c_te1.number_input("Largeur Tab. Ext.", value=st.session_state.get('men_w_tab_ex', 0), step=10, key="men_w_ex_in")
        st.session_state['men_h_tab_ex'] = c_te2.number_input("Hauteur Tab. Ext.", value=st.session_state.get('men_h_tab_ex', 0), step=10, key="men_h_ex_in")
        
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
    with st.expander("⚙️ 4. Structure & Finitions", expanded=False):
        # mode_structure = st.radio("Mode Structure", ["Simple (1 Zone)", "Divisée (2 Zones)"], horizontal=True, key="struct_mode", index=0)
        st.caption("Arbre de configuration (Diviser/Fusionner)")

        # Initialisation de l'arbre si absent
        if 'zone_tree' not in st.session_state:
            st.session_state['zone_tree'] = init_node('root')
            
        # Rendu UI Récursif
        render_node_ui(st.session_state['zone_tree'], l_dos_dormant, h_menuiserie)
             
        # Calcul des zones à plat pour le dessin
        zones_config = flatten_tree(st.session_state['zone_tree'], 0, 0, l_dos_dormant, h_menuiserie)
        
        # Compatibility with legacy code
        col_int = st.session_state.get('col_in', 'Blanc')
        # col_ext = st.session_state.get('col_ex', 'Blanc')
        
        
        color_map = {"Blanc": "#FFFFFF", "Gris": "#383E42", "Noir": "#1F1F1F", "Chêne": "#C19A6B"}
        hex_col = "#FFFFFF"
        for k, v in color_map.items():
            if k in col_int: 
                hex_col = v

        cfg_global = {
            'color_frame': hex_col,
            'color_glass': "#d6eaff"
        }
    # 7. Observations
    with st.expander("📝 Observations", expanded=False):
         st.session_state['men_obs'] = st.text_area("Notes", value=st.session_state.get('men_obs', ''), key="men_obs_in")
    
    # --- MERGED VISUALIZER 3D LOGIC ---
    import streamlit.components.v1 as components
    
    def render_3d_menuiserie(width_mm, height_mm, depth_mm=70, frame_color="#ffffff", glass_color="#aaddff", zones=[], 
                             wall_depth=340, ext_reveal_w=0, ext_reveal_h=0, overlap=30, allege_mm=0):
        """
        Renders a 3D visualization.
        FEATURES:
        - CSG Wall Logic (Shape - Hole)
        - Strict Z-Layering
        - Allège (Sill Height) Support: Generates separate Floor and Wall extension.
        - Sash logic: ensure adjacent sashes form a mullion.
        """
        
        if ext_reveal_w <= 0: ext_reveal_w = width_mm - (2 * overlap)
        if ext_reveal_h <= 0: ext_reveal_h = height_mm - overlap 
        
        # JSON data
        data_json = json.dumps({
            "width": width_mm,
            "height": height_mm,
            "depth": depth_mm,
            "color": frame_color,
            "glassColor": glass_color,
            "zones": zones,
            "wallDepth": wall_depth,
            "revealW": ext_reveal_w,
            "revealH": ext_reveal_h,
            "overlap": overlap,
            "allege": allege_mm
        })
    
        html_code = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ margin: 0; overflow: hidden; background-color: #f0f2f6; }}
                canvas {{ display: block; }}
                #info {{
                    position: absolute; top: 10px; width: 100%; text-align: center;
                    font-family: sans-serif; font-size: 14px; color: #333; pointer-events: none;
                }}
                #err {{
                    position: absolute; top: 40px; width: 100%; color: red; background: rgba(255,255,255,0.95); z-index: 1000; padding: 10px; text-align: center; display: none; border: 1px solid red;
                }}
            </style>
            <script>
                window.onerror = function(msg, url, line) {{
                    const d = document.getElementById('err');
                    d.style.display = 'block';
                    d.innerHTML += "JS Error: " + msg + "<br/>Line: " + line + "<br/>Url: " + url + "<br/>";
                    return false;
                }};
            </script>
            <script type="importmap">
                {{
                    "imports": {{
                        "three": "https://unpkg.com/three@0.128.0/build/three.module.js",
                        "three/examples/jsm/controls/OrbitControls": "https://unpkg.com/three@0.128.0/examples/jsm/controls/OrbitControls.js"
                    }}
                }}
            </script>
        </head>
        <body>
            <div id="err"></div>
            <div id="info">Visualisation 3D (Configuration & Details) - v{datetime.datetime.now().strftime('%H:%M:%S')}</div>
            
            <script type="application/json" id="3d-data">
                {data_json}
            </script>
    
            <script type="module">
                import * as THREE from 'three';
                import {{ OrbitControls }} from 'three/examples/jsm/controls/OrbitControls';
    
                try {{
                    const dataElement = document.getElementById('3d-data');
                    if (!dataElement) throw new Error("Data element not found");
                    const data = JSON.parse(dataElement.textContent);
                    
                    const scene = new THREE.Scene();
                    scene.background = new THREE.Color(0xf0f2f6);
                    
                    const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100000);
                    camera.position.set(0, 1500, 6000);
                    
                    const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
                    renderer.setSize(window.innerWidth, window.innerHeight);
                    renderer.shadowMap.enabled = true;
                    renderer.shadowMap.type = THREE.PCFSoftShadowMap; 
                    document.body.appendChild(renderer.domElement);
                    
                    const controls = new OrbitControls(camera, renderer.domElement);
                    controls.enableDamping = true;
                    controls.target.set(0, 0, 0);
                    
                    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
                    scene.add(ambientLight);
                    
                    const sunLight = new THREE.DirectionalLight(0xffffff, 0.8);
                    sunLight.position.set(1000, 2000, 2000);
                    sunLight.castShadow = true;
                    scene.add(sunLight);
                     
                    const backLight = new THREE.DirectionalLight(0xffffff, 0.3);
                    backLight.position.set(0, 500, -2000);
                    scene.add(backLight);
                    
                    // --- MATERIALS ---
                    const frameMat = new THREE.MeshStandardMaterial({{ color: data.color, roughness: 0.5, metalness: 0.1, transparent: false, depthWrite: true }});
                    const glassMat = new THREE.MeshPhysicalMaterial({{ color: data.glassColor, metalness: 0, roughness: 0, transmission: 0.9, transparent: true, opacity: 0.6, depthWrite: false }});
                    
                    const colorBeige = 0xe8dcc5; 
                    const colorWhite = 0xffffff; 
                    const colorConc = 0x999999; 
                    const colorMetal = 0xdddddd; 
                    const colorFloor = 0xdddddd;
                    const colorIntWall = 0xD3C6A6; 
                    
                    const wallExtMat = new THREE.MeshStandardMaterial({{ color: colorBeige, roughness: 1, transparent: false, depthWrite: true }}); 
                    const wallIntMat = new THREE.MeshStandardMaterial({{ color: colorIntWall, roughness: 0.5, transparent: false, depthWrite: true }}); 
                    const sillMat = new THREE.MeshStandardMaterial({{ color: colorConc, roughness: 0.9, transparent: false, depthWrite: true }}); 
                    const habillageMat = new THREE.MeshStandardMaterial({{ color: data.color, roughness: 0.5, metalness: 0.1, transparent: false, depthWrite: true }});
                    const bavetteMat = new THREE.MeshStandardMaterial({{ color: 0xffffff, roughness: 0.3, metalness: 0.1, side: THREE.DoubleSide, transparent: false, depthWrite: true }});
                    const floorMat = new THREE.MeshStandardMaterial({{ color: colorFloor, roughness: 0.8, transparent: false, depthWrite: true }});
    
                    const rootGroup = new THREE.Group();
                    scene.add(rootGroup);
                    
                    const fW = data.width;
                    const fH = data.height;
                    const fD = data.depth;       
                    const frameW = 50;
                    
                    const wDepth = data.wallDepth;
                    const holeW = data.revealW;
                    const holeH = data.revealH;
                    const allege = data.allege || 0;
                    
                    const wallCanvasW = Math.max(3000, holeW * 3);
                    const wallCanvasH = Math.max(3000, (holeH + allege) * 2);
    
                    function createWallWithHole(fullW, fullH, cutW, cutH, depth, mat, shiftY) {{
                        const shape = new THREE.Shape();
                        shape.moveTo(-fullW/2, -fullH/2 + shiftY);
                        shape.lineTo(-fullW/2, fullH/2 + shiftY);
                        shape.lineTo(fullW/2, fullH/2 + shiftY);
                        shape.lineTo(fullW/2, -fullH/2 + shiftY);
                         shape.lineTo(-fullW/2, -fullH/2 + shiftY);
                        
                        const hole = new THREE.Path();
                        hole.moveTo(-cutW/2, -cutH/2);
                        hole.lineTo(cutW/2, -cutH/2);
                        hole.lineTo(cutW/2, cutH/2);
                        hole.lineTo(-cutW/2, cutH/2);
                        hole.lineTo(-cutW/2, -cutH/2);
                        shape.holes.push(hole);
                        
                        const geo = new THREE.ExtrudeGeometry(shape, {{ depth: depth, bevelEnabled: false }});
                        const mesh = new THREE.Mesh(geo, mat);
                        return mesh;
                    }}
    
                    const winTopY = holeH/2;
                    const winBotY = -holeH/2;
                    const rejH = 40;
                    const frameCenterY_World = winBotY + 15 + fH/2;
                    
                    const floorY = winBotY - allege;
                    const roomHeight = 3000;
                    const wallH = roomHeight;
                    const wallCenterY = floorY + roomHeight/2;
                    const fullWallDepth = wDepth; 
                    const wallStartZ = -fullWallDepth; 
                    const wallW = Math.max(4000, holeW * 4);
                    
                    const unifiedWallMesh = createWallWithHole(wallW, wallH, holeW, holeH, fullWallDepth, wallExtMat, wallCenterY);
                    unifiedWallMesh.position.set(0, 0, wallStartZ);
                    rootGroup.add(unifiedWallMesh);
    
                    // --- 3-PART SILL ---
                    const upH = 15;
                    const sillOffset = -5;
                    const extension = 20; 
                    const noseH = 50; 
                    
                    // MIDDLE
                    const sShapeMid = new THREE.Shape();
                    sShapeMid.moveTo(0, upH); 
                    sShapeMid.lineTo(-fD, upH); 
                    sShapeMid.lineTo(-fD, 0); 
                    sShapeMid.lineTo(-(wDepth + extension), -10); 
                    sShapeMid.lineTo(-(wDepth + extension), -noseH); 
                    sShapeMid.lineTo(0, -noseH); 
                    sShapeMid.lineTo(0, upH);
                    
                    const sGeoMid = new THREE.ExtrudeGeometry(sShapeMid, {{ depth: fW, bevelEnabled: false }});
                    const sMeshMid = new THREE.Mesh(sGeoMid, sillMat);
                    sMeshMid.rotation.y = -Math.PI/2;
                    sMeshMid.position.set(fW/2, winBotY, sillOffset);
                    rootGroup.add(sMeshMid);
                    
                    // SIDES
                    const sideW = ((holeW + 60) - fW) / 2;
                    const sShapeSide = new THREE.Shape();
                    sShapeSide.moveTo(0, 0); 
                    sShapeSide.lineTo(-fD, 0); 
                    sShapeSide.lineTo(-(wDepth + extension), -10); 
                    sShapeSide.lineTo(-(wDepth + extension), -noseH); 
                    sShapeSide.lineTo(0, -noseH); 
                    sShapeSide.lineTo(0, 0);
                    
                    const sGeoSide = new THREE.ExtrudeGeometry(sShapeSide, {{ depth: sideW, bevelEnabled: false }});
                    
                    const sMeshLeft = new THREE.Mesh(sGeoSide, sillMat);
                    sMeshLeft.rotation.y = -Math.PI/2;
                    const sMeshLeftPos = new THREE.Mesh(sGeoSide, sillMat);
                    sMeshLeftPos.rotation.y = -Math.PI/2;
                    sMeshLeftPos.position.set(-fW/2, winBotY, sillOffset);
                    rootGroup.add(sMeshLeftPos);
                    
                    const sMeshRightPos = new THREE.Mesh(sGeoSide, sillMat);
                    sMeshRightPos.rotation.y = -Math.PI/2;
                    sMeshRightPos.position.set((holeW+60)/2, winBotY, sillOffset);
                    rootGroup.add(sMeshRightPos);
                    
                    // DOUBLAGE FILLER
                    const doubGeo = new THREE.BoxGeometry(holeW + 2, 65, 5);
                    const doubMesh = new THREE.Mesh(doubGeo, wallExtMat);
                    doubMesh.position.set(0, winBotY - 17.5, -2.5);
                    rootGroup.add(doubMesh);
                    
                    const floorGeo = new THREE.PlaneGeometry(wallW, wallW);
                    const floorMesh = new THREE.Mesh(floorGeo, floorMat);
                    floorMesh.rotation.x = -Math.PI/2;
                    floorMesh.position.set(0, floorY, 0);
                    rootGroup.add(floorMesh);
                    
                    const ceilGeo = new THREE.PlaneGeometry(wallW, wallW);
                    const ceilMesh = new THREE.Mesh(ceilGeo, wallExtMat); 
                    ceilMesh.rotation.x = Math.PI/2;
                    ceilMesh.position.set(0, floorY + roomHeight, 0);
                    rootGroup.add(ceilMesh);
                    
                    const winGroup = new THREE.Group();
                    winGroup.position.set(0, frameCenterY_World, -fD/2);
                    rootGroup.add(winGroup);
    
                    // FRAMES
                    const fLeftMesh = new THREE.Mesh(new THREE.BoxGeometry(frameW, fH, fD), frameMat);
                    fLeftMesh.position.set(-fW/2 + frameW/2, 0, 0);
                    winGroup.add(fLeftMesh);
                    const fRightMesh = new THREE.Mesh(new THREE.BoxGeometry(frameW, fH, fD), frameMat);
                    fRightMesh.position.set(fW/2 - frameW/2, 0, 0);
                    winGroup.add(fRightMesh);
                    const fTopMesh = new THREE.Mesh(new THREE.BoxGeometry(fW, frameW, fD), frameMat);
                    fTopMesh.position.set(0, fH/2 - frameW/2, 0);
                    winGroup.add(fTopMesh);
                    const fBotMesh = new THREE.Mesh(new THREE.BoxGeometry(fW, frameW, fD), frameMat);
                    fBotMesh.position.set(0, -fH/2 + frameW/2, 0);
                    winGroup.add(fBotMesh);
                    
                    const wingS = 27; 
                    const wingTh = 2;
                    
                    const ailTop = new THREE.Mesh(new THREE.BoxGeometry(fW + 2*wingS, wingS, wingTh), frameMat);
                    ailTop.position.set(0, fH/2 + wingS/2, fD/2 + wingTh/2); 
                    winGroup.add(ailTop);
                    
                    const ailLeft = new THREE.Mesh(new THREE.BoxGeometry(wingS, fH + 2*wingS, wingTh), frameMat);
                    ailLeft.position.set(-fW/2 - wingS/2, 0, fD/2 + wingTh/2);
                    winGroup.add(ailLeft);
                    
                    const ailRight = new THREE.Mesh(new THREE.BoxGeometry(wingS, fH + 2*wingS, wingTh), frameMat);
                    ailRight.position.set(fW/2 + wingS/2, 0, fD/2 + wingTh/2);
                    winGroup.add(ailRight);
                    
                    const ailBot = new THREE.Mesh(new THREE.BoxGeometry(fW + 2*wingS, wingS, wingTh), frameMat);
                    ailBot.position.set(0, -fH/2 - wingS/2, fD/2 + wingTh/2);
                    winGroup.add(ailBot);
                    
                    const wingThick = 2; const wingW = 20; const wingZ = fD/2 + wingThick/2;
                    const wTopM = new THREE.Mesh(new THREE.BoxGeometry(fW, wingW, wingThick), frameMat);
                    wTopM.position.set(0, fH/2 - wingW/2, wingZ);
                    winGroup.add(wTopM);
                    const wBotM = new THREE.Mesh(new THREE.BoxGeometry(fW, wingW, wingThick), frameMat);
                    wBotM.position.set(0, -fH/2 + wingW/2, wingZ);
                    winGroup.add(wBotM);
                    const wLeftM = new THREE.Mesh(new THREE.BoxGeometry(wingW, fH, wingThick), frameMat);
                    wLeftM.position.set(-fW/2 + wingW/2, 0, wingZ);
                    winGroup.add(wLeftM);
                    const wRightM = new THREE.Mesh(new THREE.BoxGeometry(wingW, fH, wingThick), frameMat);
                    wRightM.position.set(fW/2 - wingW/2, 0, wingZ);
                    winGroup.add(wRightM);
    
                    // --- SASHES & MULLIONS ---
                    const drawSashFrame = (grp, w, h, depth, withGlass, handlePos) => {{
                        const sP = 55;
                        const shape = new THREE.Shape();
                        shape.moveTo(-w/2, -h/2); shape.lineTo(w/2, -h/2); shape.lineTo(w/2, h/2); shape.lineTo(-w/2, h/2); shape.lineTo(-w/2, -h/2);
                        const hole = new THREE.Path();
                        hole.moveTo(-w/2+sP, -h/2+sP); hole.lineTo(w/2-sP, -h/2+sP); hole.lineTo(w/2-sP, h/2-sP); hole.lineTo(-w/2+sP, h/2-sP); hole.lineTo(-w/2+sP, -h/2+sP);
                        shape.holes.push(hole);
                        const geo = new THREE.ExtrudeGeometry(shape, {{ depth: depth, bevelEnabled: false }});
                        const mesh = new THREE.Mesh(geo, frameMat); mesh.position.set(0, 0, -depth/2); grp.add(mesh);
                        
                        if (withGlass) {{
                            const gl = new THREE.Mesh(new THREE.BoxGeometry(w - 2*sP, h - 2*sP, 6), glassMat); 
                            grp.add(gl);
                        }}
                        
                        if (handlePos) {{
                            const hM = new THREE.Mesh(new THREE.BoxGeometry(20, 100, 20), new THREE.MeshStandardMaterial({{color: 0xeeeeee}}));
                            let hX = 0, hY = 0;
                            if (handlePos === 'left') hX = -w/2 + sP/2;
                            else if (handlePos === 'right') hX = w/2 - sP/2;
                            else if (handlePos === 'top') {{ hY = h/2 - sP/2; hM.rotation.z = Math.PI/2; }}
                            hM.position.set(hX, hY, depth/2 + 10); 
                            grp.add(hM);
                        }}
                    }};
    
                    if (data.zones && data.zones.length > 0) {{
                        data.zones.forEach((zone, idx) => {{
                            let sX = zone.x; let sY = zone.y; let sW = zone.w; let sH = zone.h;
                            const tol = 1;
                            if (sX < tol) {{ sX += frameW; sW -= frameW; }}
                            if ((zone.x + zone.w) > fW - tol) {{ sW -= frameW; }}
                            if (sY < tol) {{ sY += frameW; sH -= frameW; }}
                            if ((zone.y + zone.h) > fH - tol) {{ sH -= frameW; }}
    
                            // MULLIONS
                            if (zone.x > tol) {{
                                const mul = new THREE.Mesh(new THREE.BoxGeometry(frameW, zone.h, fD), frameMat);
                                const mX = (-fW/2) + zone.x;
                                const mY = (fH/2) - (zone.y + zone.h/2);
                                mul.position.set(mX, mY, 0);
                                winGroup.add(mul);
                                sX += frameW/2; sW -= frameW/2; 
                            }}
                            if (zone.y > tol) {{
                                const tr = new THREE.Mesh(new THREE.BoxGeometry(zone.w, frameW, fD), frameMat);
                                const tX = (-fW/2) + (zone.x + zone.w/2);
                                const tY = (fH/2) - zone.y;
                                tr.position.set(tX, tY, 0);
                                winGroup.add(tr);
                                sY += frameW/2; sH -= frameW/2;
                            }}
    
                            let newW = sW; let newH = sH;
                            if (newW <= 0 || newH <= 0) return;
                            
                            const zCenterX = (-fW/2) + sX + newW/2;
                            const zCenterY = (fH/2) - sY - newH/2;
                            
                            const sGroup = new THREE.Group();
                            sGroup.position.set(zCenterX, zCenterY, 0);
                            winGroup.add(sGroup);
                            
                            const type = (zone.type || '').toLowerCase();
                            const sD = fD - 10;
                            
                            if (type.includes('fixe')) {{
                                drawSashFrame(sGroup, newW, newH, sD, true, null);
                            }} else if (type.includes('coulissant')) {{
                                const sashW = (newW / 2) + 20; 
                                const lGrp = new THREE.Group(); lGrp.position.set(-newW/4, 0, -10); sGroup.add(lGrp);
                                drawSashFrame(lGrp, sashW, newH, sD, true, 'right');
                                const rGrp = new THREE.Group(); rGrp.position.set(newW/4, 0, 10); sGroup.add(rGrp);
                                drawSashFrame(rGrp, sashW, newH, sD, true, 'left');
                            }} else if (type.includes('soufflet')) {{
                                drawSashFrame(sGroup, newW, newH, sD, true, 'top');
                            }} else if (type.includes('2 vantaux') || type.includes('double')) {{
                                const sashW = (newW / 2) - 2;
                                const lGrp = new THREE.Group(); lGrp.position.set(-newW/4, 0, 0); sGroup.add(lGrp);
                                drawSashFrame(lGrp, sashW, newH, sD, true, null);
                                const rGrp = new THREE.Group(); rGrp.position.set(newW/4, 0, 0); sGroup.add(rGrp);
                                drawSashFrame(rGrp, sashW, newH, sD, true, 'left');
                                const batt = new THREE.Mesh(new THREE.BoxGeometry(40, newH, sD+5), frameMat);
                                batt.position.set(0, 0, 5); sGroup.add(batt);
                            }} else {{
                                drawSashFrame(sGroup, newW, newH, sD, true, 'left');
                            }}
                        }});
                    }}
    
                    // HABILLAGE
                    const gapH = (holeW - fW);
                    const gapTop = Math.max(0, holeH - 40 - fH);
                    const habThick = 4;
                    const habDepth = 40; 
                    const habZ = -fD - habThick/2;
                    
                    const topH_Height = Math.max(habDepth, gapTop);
                    const hTop = new THREE.Mesh(new THREE.BoxGeometry(holeW + 80, topH_Height, habThick), habillageMat);
                    hTop.position.set(0, winTopY - topH_Height/2, habZ); 
                    rootGroup.add(hTop);
                    
                    const gapSide = Math.max(0, gapH / 2);
                    const cornierW = Math.max(habDepth, gapSide);
                    
                    const hLeft = new THREE.Mesh(new THREE.BoxGeometry(cornierW, holeH + topH_Height, habThick), habillageMat);
                    hLeft.position.set(-fW/2 - cornierW/2, 0 + topH_Height/2 - habDepth/2, habZ); 
                    rootGroup.add(hLeft);
                    
                    const hRight = new THREE.Mesh(new THREE.BoxGeometry(cornierW, holeH + topH_Height, habThick), habillageMat);
                    hRight.position.set(fW/2 + cornierW/2, 0 + topH_Height/2 - habDepth/2, habZ);
                    rootGroup.add(hRight);
    
                    const bavGeo = new THREE.PlaneGeometry(fW + 40, 60);
                    const bav = new THREE.Mesh(bavGeo, bavetteMat);
                    bav.rotation.x = 0.5; 
                    bav.position.set(0, winBotY + 15 + 2, -fD - 20); 
                    rootGroup.add(bav);
    
                    function animate() {{
                        requestAnimationFrame(animate);
                        controls.update();
                        renderer.render(scene, camera);
                    }}
                    animate();
                    
                    window.addEventListener('resize', () => {{
                        camera.aspect = window.innerWidth / window.innerHeight;
                        camera.updateProjectionMatrix();
                        renderer.setSize(window.innerWidth, window.innerHeight);
                    }});
                }} catch (e) {{
                    const d = document.getElementById('err');
                    d.style.display = 'block';
                    d.innerHTML = "Init Error: " + e.message;
                    console.error(e);
                }}
            </script>
        </body>
        </html>
        """
        
        components.html(html_code, height=600, scrolling=False)

     # --- 8. VISUALISATION 3D ---
    with st.expander("🖥️ Visualisation 3D 360°", expanded=False):
        st.info("Visualisation 3D expérimentale (WebGL). Cliquez pour activer.")
        if st.checkbox("Activer la vue 3D", key="view_3d_toggle"):
            # Prepare Data
            d_mm = 70
            try:
                ft = st.session_state.get('frame_thig', "70 mm")
                d_mm = int(str(ft).replace('mm','').strip())
            except: pass
            
            try:
                # Call local function directly (Merged)
                render_3d_menuiserie(
                    width_mm=l_dos_dormant,
                    height_mm=h_menuiserie,
                    depth_mm=d_mm,
                    frame_color=hex_col,
                    glass_color="#aaddff",
                    zones=zones_config,
                    ext_reveal_w=st.session_state.get('men_w_tab_ex', 0),
                    ext_reveal_h=st.session_state.get('men_h_tab_ex', 0),
                    allege_mm=st.session_state.get('h_allege', 0)
                )
            except Exception as e:
                st.error(f"Erreur 3D : {e}")

     # --- ACTIONS ---
    st.markdown("### 💾 Actions")
    
    active_id = st.session_state.get('active_config_id')
    if active_id:
        st.caption(f"✏️ Édition en cours : {st.session_state.get('ref_id', '???')}")
        
    c_btn0, c_btn1, c_btn2 = st.columns(3)
    
    # ACTION: UPDATE (Menuiserie)
    # ACTION: UPDATE (Menuiserie)
    # V75 UPDATE: Consolidated "Enregistrer" Button
    if c_btn0.button("💾 Enregistrer", use_container_width=True, help="Sauvegarder la configuration actuelle"):
         data = serialize_config()
         data['mode_module'] = 'Menuiserie'
         
         if active_id:
             # UPDATE EXISTING
             current_ref = st.session_state.get('ref_id', 'Repère 1')
             update_current_config_in_project(active_id, data, current_ref)
             
             # Update Snapshot
             st.session_state['clean_config_snapshot'] = get_config_snapshot(data)
             
             st.toast(f"✅ {current_ref} mis à jour !")
             st.rerun()
         else:
             # CREATE NEW
             new_ref = st.session_state.get('ref_id', 'Repère 1')
             new_id = add_config_to_project(data, new_ref)
             
             # Set as Active
             st.session_state['active_config_id'] = new_id
             
             # Update Snapshot
             st.session_state['clean_config_snapshot'] = get_config_snapshot(data)
             
             st.toast(f"✅ {new_ref} enregistré !")
             st.rerun()

    # 1. Dupliquer (Save Copy)
    if c_btn1.button("Dupliquer", use_container_width=True, help="Créer une copie de la configuration actuelle"):
        data = serialize_config()
        data['mode_module'] = 'Menuiserie'
        
        # If we are editing "Repère 1", we want the copy to be "Repère 1 (Copie)" or similar?
        # Or just "Repère 1" (new ID).
        # Standard behavior: Add as NEW entry.
        
        current_ref = st.session_state.get('ref_id', 'Repère 1')
        new_ref = f"{current_ref} (Copie)"
        
        new_id = add_config_to_project(data, new_ref)
        
        # Switch to the duplicate?
        st.session_state['active_config_id'] = new_id
        
        # V76 Fix: Use pending_updates for widget keys
        if 'pending_updates' not in st.session_state: st.session_state['pending_updates'] = {}
        st.session_state['pending_updates']['ref_id'] = new_ref
        
        st.session_state['clean_config_snapshot'] = get_config_snapshot(data)
        
        st.toast(f"✅ Copie créée : {new_ref}")
        st.rerun()
        
    # 2. Enregistrer & Nouveau (Save & Reset)
    if c_btn2.button("Nouveau (Reset)", use_container_width=True, help="Sauvegarder et Réinitialiser"):
        data = serialize_config()
        data['mode_module'] = 'Menuiserie'
        current_ref = st.session_state.get('ref_id', 'Repère 1')
        
        if active_id:
            # UPDATE EXISTING
            update_current_config_in_project(active_id, data, current_ref)
            st.toast(f"✅ {current_ref} mis à jour !")
        else:
            # CREATE NEW
            add_config_to_project(data, current_ref)
            st.toast(f"✅ {current_ref} enregistré !")
            
        # RESET
        reset_config(rerun=False)
        st.session_state['clean_config_snapshot'] = None # Clear snapshot on reset
        st.session_state['active_config_id'] = None
        st.session_state['pending_ref_id'] = get_next_project_ref()
        st.rerun()
        # RESET (No Rerun)
        reset_config(rerun=False) 
        # AUTO-INCREMENT REF
        st.session_state['pending_ref_id'] = get_next_project_ref()
        st.rerun()
    




# --- 3. GÉNÉRATEUR SVG FINAL ---
def generate_svg_v73():
    # RETRIEVE VARIABLES FROM SESSION STATE (Fix NameError)
    # Must match keys used in Sidebar
    
    # 1. Basic Dimensions
    l_dos_dormant = st.session_state.get('width_dorm', 1200)
    h_dos_dormant = st.session_state.get('height_dorm', 1400)
    
    # 2. Options
    vr_opt = st.session_state.get('vr_enable', False)
    h_vr = st.session_state.get('vr_h', 185) if vr_opt else 0
    vr_grille = st.session_state.get('vr_g', False)
    
    h_menuiserie = h_dos_dormant - h_vr
    
    # 3. Ailettes & Dormant
    ep_dormant = st.session_state.get('frame_thig', 70)
    ail_val = st.session_state.get('fin_val', 60)
    
    same_bot = st.session_state.get('same_bot', False)
    # Logic from Sidebar: if same, use ail_val, else use fin_bot input
    if same_bot: ail_bas = ail_val
    else: ail_bas = st.session_state.get('fin_bot', 0)
    
    # 4. Colors
    col_int = st.session_state.get('col_in', 'Blanc')
    # Config Global
    color_map = {"Blanc": "#FFFFFF", "Gris": "#383E42", "Noir": "#1F1F1F", "Chêne": "#C19A6B"}
    hex_col = "#FFFFFF"
    for k, v in color_map.items():
        if k in col_int: hex_col = v
        
    cfg_global = {
        'color_frame': hex_col,
        'color_glass': "#d6eaff"
    }

    # 5. Zones
    zones_config = flatten_tree(st.session_state.get('zone_tree', init_node('root')), 0, 0, l_dos_dormant, h_menuiserie)
    
    svg = []
    col_fin = "#D3D3D3"
    
    ht_haut = h_vr + ail_val if vr_opt else ail_val
    ht_bas = ail_bas
    
    bx = -ail_val
    by = -ht_haut
    bw = l_dos_dormant + 2*ail_val
    bh = h_menuiserie + ht_haut + ht_bas
    
    # V76 FIX: Dynamic Font Size for Scaling
    # Base font size = 1.5% of the largest dimension, clamped between 12 and 100
    max_dim = max(bw, bh)
    font_dim = max(16, int(max_dim * 0.02))
    
    # V73 FIX: Visible Dormant Frame (Stroke black)
    draw_rect(svg, bx, by, bw, bh, col_fin, "black", 1, 0)
    
    if vr_opt:
        draw_rect(svg, 0, -h_vr, l_dos_dormant, h_vr, cfg_global['color_frame'], "black", 1, 1)
        draw_text(svg, l_dos_dormant/2, -h_vr/2, f"COFFRE {int(h_vr)}", font_size=font_dim, fill="white" if "Blanc" not in col_int else "black", weight="bold", z_index=5)
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
        draw_sash_content(svg, z['x'], z['y'], z['w'], z['h'], z['type'], z['params'], cfg_global, z_base=4, font_dim_ref=font_dim)
        
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
        # font_dim already calculated above
        
        # OFFSETS
        # OFFSETS
        # V78 FIX: Robust Layering System
        # We define 3 layers of dimensions: Details, Frame, Total
        # Each layer is spaced by 'dim_step'
        dim_step = font_dim * 2.0 # Generous spacing
        
        # OFFSETS (Positive values, direction handled by draw_dimension_line)
        # H: Added to y (Down)
        # V: Subtracted from x (Left)
        layer_1 = dim_step       # Details
        layer_2 = dim_step * 2.2 # Frame (Slightly more gap)
        layer_3 = dim_step * 3.4 # Total

        # 1. COTES CUMULEES (Détails des zones)
        # Display only if there are multiple zones (otherwise redundant with overall dimensions)
        if len(zones_config) > 1:
            # Horizontal (Largeur)
            xs = sorted(list(set([z['x'] for z in zones_config] + [z['x']+z['w'] for z in zones_config])))
            for k in range(len(xs)-1):
                val = xs[k+1] - xs[k]
                if val > 1: # Ignore micro-gaps
                    draw_dimension_line(svg, xs[k], 0, xs[k+1], 0, val, "", h_menuiserie+layer_1, "H", font_dim-4, 9)
                    
            # Vertical (Hauteur)
            # Vertical (Hauteur)
            # Use Layer 1 
            v_dim_offset = layer_1
            
            ys = sorted(list(set([z['y'] for z in zones_config] + [z['y']+z['h'] for z in zones_config])))
            for k in range(len(ys)-1):
                val = ys[k+1] - ys[k]
                if val > 1:
                    # Pass offset as POSITIVE because function subtracts it for "V"
                    draw_dimension_line(svg, 0, ys[k], 0, ys[k+1], val, "", v_dim_offset, "V", font_dim-4, 9)

        # 2. COTES TOTALES (Existantes, repoussées)
        # 2. COTES TOTALES (Existantes, repoussées)
        # Cadre (Largeur) -> Layer 2
        draw_dimension_line(svg, 0, 0, l_dos_dormant, 0, l_dos_dormant, "", h_menuiserie+layer_2, "H", font_dim, 9)
        
        # Hors Tout (Largeur) -> Layer 3
        l_ht = l_dos_dormant + 2*ail_val
        draw_dimension_line(svg, -ail_val, 0, l_dos_dormant+ail_val, 0, l_ht, "", h_menuiserie+layer_3, "H", font_dim, 9)


        # Cadre (Hauteur)
        top_dormant_y = -h_vr if vr_opt else 0
        h_dos_calc = h_menuiserie + (h_vr if vr_opt else 0)
        # Offset positif pour "V" part vers la gauche.
        draw_dimension_line(svg, 0, top_dormant_y, 0, h_menuiserie, h_dos_calc, "", layer_2, "V", font_dim, 9)

        # Hors Tout (Hauteur)
        ht_haut = h_vr + ail_val if vr_opt else ail_val
        ht_bas = ail_bas
        y_start_ht = -ht_haut
        y_end_ht = h_menuiserie + ht_bas
        h_visuel_total = abs(y_end_ht - y_start_ht)
        draw_dimension_line(svg, 0, y_start_ht, 0, y_end_ht, h_visuel_total, "", layer_3, "V", font_dim, 9)

        # HP (si applicable) - Iterate ALL valid zones (V75 Fix)
        for hp_z in zones_config:
            if 'h_poignee' in hp_z['params'] and hp_z['params']['h_poignee'] > 0:
                 hp_val = hp_z['params']['h_poignee']
                 # Reference : Bas de la zone concernée
                 y_bottom_zone = hp_z['y'] + hp_z['h']
                 
                 # Position Poignée (Y dans SVG)
                 y_hp = y_bottom_zone - hp_val
                 
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
                 # Use font_dim proportional offset
                 dist_offset = font_dim * 3.5
                 sash_center_x = ox + ow / 2
                 if x_handle_pos < sash_center_x:
                     offset_line = -dist_offset 
                 else:
                     offset_line = dist_offset
                 
                 # Only draw if handle pos is reasonable
                 draw_dimension_line(svg, x_handle_pos + offset_line, y_hp, x_handle_pos + offset_line, y_bottom_zone, hp_val, "HP : ", 0, "V", font_dim, 20, leader_fixed_start=x_handle_pos)

             

        
        # ANCIEN CODE (Supprimé)
        # has_ouvrant = any(z['type'] != "Fixe" for z in zones_config)
        # if has_ouvrant:
        #    hp_val = 1050 ...

        # Cadre (Hauteur) -> Layer 2
        top_dormant_y = -h_vr if vr_opt else 0
        h_dos_calc = h_menuiserie + (h_vr if vr_opt else 0)
        # Offset is POSITIVE for V because it goes Left
        draw_dimension_line(svg, 0, top_dormant_y, 0, h_menuiserie, h_dos_calc, "", layer_2, "V", font_dim, 9)

        # Hors Tout (Hauteur) -> Layer 3
        ht_haut = h_vr + ail_val if vr_opt else ail_val
        ht_bas = ail_bas
        y_start_ht = -ht_haut
        y_end_ht = h_menuiserie + ht_bas
        h_visuel_total = abs(y_end_ht - y_start_ht)
        draw_dimension_line(svg, 0, y_start_ht, 0, y_end_ht, h_visuel_total, "", layer_3, "V", font_dim, 9)

        # DEFS & RETURN
        defs = ""
        svg_str = "".join([el[1] for el in sorted(svg, key=lambda x:x[0])])
        
        # V79 FIX: Dynamic ViewBox Margins
        # Ensure the viewbox includes the furthest dimension layer (layer_3) plus padding for text
        safe_margin = layer_3 + (font_dim * 2.5) 
        
        # Current Bounding Box of the Object
        obj_x_min = -ail_val
        obj_y_min = -ht_haut
        obj_x_max = l_dos_dormant + ail_val
        obj_y_max = h_menuiserie + ht_bas
        
        # ViewBox definition
        vb_x = obj_x_min - safe_margin  # Left Margin (for Vertical dims)
        vb_y = obj_y_min - 50            # Top Margin (Minimal, unless Top dims added later)
        
        vb_w = (obj_x_max - vb_x) + safe_margin   # Right Margin Dynamic

        vb_h = (obj_y_max - vb_y) + safe_margin # Height = Object Bottom - VB Top + Bottom Margin (for Horizontal dims)
        
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb_x} {vb_y} {vb_w} {vb_h}" style="background-color:white;">{defs}{svg_str}</svg>'
    except Exception as e:
        import traceback
        return f'<svg width="600" height="200" viewBox="0 0 600 200"><rect width="600" height="200" fill="#fee"/><text x="10" y="30" fill="red" font-family="monospace" font-size="12">Erreur: {str(e)}</text><text x="10" y="50" fill="red" font-family="monospace" font-size="10">{traceback.format_exc().split("line")[-1]}</text></svg>'


# ==============================================================================
# --- MODULE VOLET ROULANT (NOUVEAU) ---
# ==============================================================================

def render_volet_form():
    """Formulaire de configuration Volet Roulant"""
    s = st.session_state
    
    # 1. Header: Repère et Quantité (Matching Menuiserie Style)
    # Silent Defaults
    s['vr_mat'] = "Aluminium" 

    with st.expander("📝 Repère et quantité", expanded=False):
        c_ref, c_qte = st.columns([3, 1])
        with c_ref:
            # Repère editable
            curr_ref = s.get('ref_id', get_next_project_ref())
            new_ref_in = st.text_input("Repère", value=curr_ref, key="vr_ref_in")
            if new_ref_in != curr_ref:
                s['ref_id'] = new_ref_in
        with c_qte:
             s['vr_qte'] = st.number_input("Qté", value=s.get('vr_qte', 1), min_value=1, step=1, key="vr_qte_in")

    # 1.5 Type de Volet (NOUVEAU)
    with st.expander("🏗️ Type de Volet", expanded=True):
        type_opts = ["Coffre rénovation", "Coffre traditionnel en bois", "Coffre Bloc baie", "Coffre titan extérieur"]
        s['vr_type_coffre'] = st.selectbox("Type de Coffre", type_opts, index=0, key="vr_type_c_sel")

    # 2. Dimensions
    with st.expander("📐 Dimensions", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            dim_opts = ["Côtes Tableau", "Côtes dos de coulisses", "Dimensions du tablier"]
            
            # Smart Index Logic
            curr_dim = s.get('vr_dim_type', "Côtes Tableau")
            if curr_dim not in dim_opts: curr_dim = "Côtes Tableau"
            
            s['vr_dim_type'] = st.selectbox("Type de côtes", dim_opts, index=dim_opts.index(curr_dim), key="vr_dim_sel")
        
        c_w, c_h = st.columns(2)
        with c_w:
            s['vr_width'] = st.number_input("Largeur (mm)", value=s.get('vr_width', 1000), step=10, key="vr_w_in")
        with c_h:
            s['vr_height'] = st.number_input("Hauteur (mm)", value=s.get('vr_height', 1000), step=10, key="vr_h_in")
            
        # Qte moved to header
        
        # Option Enroulement
        st.write("") # Spacer
        s['vr_add_winding'] = st.checkbox("Ajouter enroulement sur la hauteur", value=s.get('vr_add_winding', False), key="vr_add_winding_chk")
    
    # 3. Configuration Lames & Options
    with st.expander("🛠️ 3. Configuration Lames & Options", expanded=False):
        # Logic: > 3000 mm -> 50 mm default
        width = s.get('vr_width', 1000)
        lame_opts = ["40 mm", "50 mm"]
        
        # Init default logic based on Width if not set
        if 'vr_lame_init_done' not in s or s.get('last_vr_width') != width:
             s['last_vr_width'] = width
             s['vr_lame_init_done'] = True
             if width > 3000:
                  s['vr_lame_thick'] = "50 mm"
                  # st.toast("Largeur > 3m : Lames 50mm")
             elif 'vr_lame_thick' not in s:
                  s['vr_lame_thick'] = "40 mm"

        curr = s.get('vr_lame_thick', "40 mm")
        idx = 1 if curr == "50 mm" else 0
        s['vr_lame_thick'] = st.selectbox("Épaisseur des Lames", lame_opts, index=idx, key="vr_lame_k")
        if width > 3000 and s['vr_lame_thick'] == "40 mm":
             st.warning("Attention : Pour une largeur > 3m, 50 mm est recommandé.")

        s['vr_bord_mer'] = st.checkbox("Thermique bord de mer", key="vr_bdm")
        st.info("ℹ️ Coulisses : L 56 x P 30 mm")

    # 4. Couleurs (Nouveau)
    col_opts = ["Blanc 9010", "Gris Anthracite 7016", "Gris Clair 7035", "Noir 2100", "Ivoire 1015", "Chêne Doré", "Autre (RAL)"]
    
    with st.expander("🎨 4. Couleurs", expanded=False):
        # Helper to render color select + input
        def color_picker(label, key_prefix):
            c_sel = st.selectbox(label, col_opts, index=0, key=f"{key_prefix}_sel")
            if c_sel == "Autre (RAL)":
                c_ral = st.text_input(f"RAL {label}", value="", key=f"{key_prefix}_ral")
                return f"RAL {c_ral}" if c_ral else "RAL ?"
            return c_sel

        c_col1, c_col2 = st.columns(2)
        with c_col1:
            s['vr_col_coffre'] = color_picker("Couleur Coffre", "vr_c_coffre")
            s['vr_col_coulisses'] = color_picker("Couleur Coulisses", "vr_c_coul")
        with c_col2:
            s['vr_col_tablier'] = color_picker("Couleur Tablier", "vr_c_tab")
            s['vr_col_lame_fin'] = color_picker("Couleur Lame Finale", "vr_c_lame")

    # 5. Manoeuvre
    with st.expander("🎮 5. Manoeuvre / Motorisation", expanded=False):
        mech = st.radio("Type", ["Manuel", "Motorisé"], horizontal=True, index=0 if s.get('vr_type') == "Manuel" else 1, key="vr_mech_in")
        s['vr_type'] = mech
        
        if mech == "Manuel":
            s['vr_motor'] = None
            c_man1, c_man2 = st.columns(2)
            with c_man1:
                s['vr_crank_side'] = st.radio("Sortie Manivelle", ["Droite", "Gauche"], horizontal=True, index=0 if s.get('vr_crank_side') == "Droite" else 1, key="vr_crank_side_in")
            with c_man2:
                s['vr_crank_len'] = st.text_input("Longueur Manivelle (mm)", value=s.get('vr_crank_len', "1200"), key="vr_crank_len_in")

        else: # Motorisé
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                # Default to SOMFY if not set
                current_motor = s.get('vr_motor')
                if current_motor is None: current_motor = "SOMFY"
                
                mot = st.selectbox("Marque", ["SOMFY", "SIMU"], index=0 if current_motor == "SOMFY" else 1, key="vr_mot_in")
                s['vr_motor'] = mot
                
                # Protocol (IO/RTS/Filaire + IO SOLAIRE)
                proto = st.selectbox("Protocole", ["IO", "RTS", "Filaire", "IO SOLAIRE"], index=0, key="vr_proto_in")
                s['vr_proto'] = proto
                
            with c_m2:
                # Power (Nm)
                power = st.selectbox("Puissance", ["10 Nm", "20 Nm", "30 Nm", "40 Nm", "50 Nm"], index=0, key="vr_power_in")
                s['vr_power'] = power
            
            st.write("---")
            c_c1, c_c2 = st.columns(2)
            with c_c1:
                # Cable Side (Swapped: Gauche / Droite as requested for visual match)
                s['vr_cable_side'] = st.radio("Sortie de fil", ["Gauche", "Droite"], horizontal=True, index=0 if s.get('vr_cable_side') == "Gauche" else 1, key="vr_cable_side_in")
            with c_c2:
                # Cable Length (5ML, 10ML, Other)
                c_len = st.selectbox("Longueur Câble", ["5 ML (Standard)", "10 ML", "Autre"], index=0, key="vr_cable_len_in")
                if c_len == "Autre":
                    s['vr_cable_len'] = st.text_input("Préciser longueur", key="vr_cable_len_custom")
                else:
                    s['vr_cable_len'] = c_len


    # 6. Observations
    with st.expander("📝 6. Observations", expanded=False):
         st.session_state['vr_obs'] = st.text_area("Notes", value=st.session_state.get('vr_obs', ''), key="vr_obs_in")

    # 6. Gestion / Sauvegarde
    st.markdown("### 💾 Actions")
    
    active_id = s.get('active_config_id')
    curr_ref = s.get('ref_id', 'VR-01')
    
    if active_id:
        st.caption(f"✏️ Édition en cours : {curr_ref}")
    
    # Logic to Add/Save
    def get_next_ref():
        configs = s.get('project', {}).get('configs', [])
        max_n = 0
        for c in configs:
            import re
            m = re.search(r'\d+', c.get('ref', ''))
            if m:
                n = int(m.group(0))
                if n > max_n: max_n = n
        return f"VR-{max_n + 1:02d}"

    def prepare_data():
        vr_data = {k: v for k, v in s.items() if k.startswith('vr_')}
        vr_data['mode_module'] = 'Volet Roulant' 
        # Fix VR-XX: Prefer widget input, then session ref, then calc new one
        vr_data['ref_id'] = s.get('vr_ref_in', s.get('ref_id', get_next_ref()))
        return vr_data

    # Layout: 3 Columns, Col 0 only if Active
    c_btn0, c_btn1, c_btn2 = st.columns(3)

    # 1. UPDATE (Mettre à jour) - Only if editing existing
    # V75 UPDATE: Consolidated "Enregistrer" Button
    if c_btn0.button("💾 Enregistrer", use_container_width=True, help="Sauvegarder la configuration actuelle"):
        # Update Logic
        configs = s.get('project', {}).get('configs', [])
        
        # Determine Reference: Logic is slightly complex for VR because of manual input vs auto
        data = prepare_data()
        current_ref = data['ref_id'] 

        if active_id:
            # UPDATE EXISTING
            target_idx = next((i for i, c in enumerate(configs) if c['id'] == active_id), -1)
            
            if target_idx >= 0:
                configs[target_idx]['data'] = data
                configs[target_idx]['ref'] = current_ref
                # Sync session ref
                s['ref_id'] = current_ref
                
                # Update Snapshot
                st.session_state['clean_config_snapshot'] = get_config_snapshot(data)
                
                st.toast(f"✅ {current_ref} mis à jour !")
                st.rerun()
            else:
                st.error("Erreur: Configuration introuvable pour mise à jour.")
        else:
             # CREATE NEW (Save)
             # Add to project
             new_id = str(uuid.uuid4())
             new_config = {
                'id': new_id,
                'ref': current_ref,
                'data': data,
                'config_type': 'Volet Roulant'
            }
             if 'project' not in s: s['project'] = {'configs': []}
             s['project']['configs'].append(new_config)
             
             # Set Active
             s['active_config_id'] = new_id
             
             # Update Snapshot
             st.session_state['clean_config_snapshot'] = get_config_snapshot(data)
             
             st.toast(f"✅ {current_ref} enregistré !")
             st.rerun()

    # 2. Ajouter & Dupliquer
    # 2. Dupliquer (Save Copy)
    if c_btn1.button("Dupliquer", use_container_width=True, help="Créer une copie"):
        new_id = str(uuid.uuid4())
        
        current_ref = s.get('ref_id', 'VR-01')
        new_ref = f"{current_ref} (Copie)"
        
        data = prepare_data()
        data['ref_id'] = new_ref # Force new ref
        
        new_config = {
            'id': new_id,
            'ref': new_ref,
            'data': data,
            'config_type': 'Volet Roulant'
        }
        
        if 'project' not in s: s['project'] = {'configs': []}
        s['project']['configs'].append(new_config)
        
        # Switch to new duplicate
        s['active_config_id'] = new_id
        
        # V76 Fix: Use pending_updates for widget keys
        if 'pending_updates' not in st.session_state: st.session_state['pending_updates'] = {}
        st.session_state['pending_updates']['ref_id'] = new_ref
        
        st.session_state['clean_config_snapshot'] = get_config_snapshot(data)
        
        st.toast(f"✅ Copie créée : {new_ref}")
        st.rerun()
            
    # 3. Nouveau (Reset)
    if c_btn2.button("Nouveau (Reset)", use_container_width=True, help="Sauvegarder et remet à zéro"):
        data = prepare_data()
        current_ref = data['ref_id']
        
        if active_id:
            # UPDATE EXISTING
            configs = s.get('project', {}).get('configs', [])
            target_idx = next((i for i, c in enumerate(configs) if c['id'] == active_id), -1)
            if target_idx >= 0:
                configs[target_idx]['data'] = data
                configs[target_idx]['ref'] = current_ref
                st.toast(f"✅ {current_ref} mis à jour !")
        else:
             # CREATE NEW
             new_id = str(uuid.uuid4())
             new_config = {
                'id': new_id,
                'ref': current_ref,
                'data': data,
                'config_type': 'Volet Roulant'
            }
             if 'project' not in s: s['project'] = {'configs': []}
             s['project']['configs'].append(new_config)
             st.toast(f"✅ {current_ref} enregistré !")
             
        # RESET
        keys_vr = [k for k in s.keys() if k.startswith('vr_')]
        for k in keys_vr: del s[k]
        
        s['active_config_id'] = None
        s['ref_id'] = get_next_ref()
        s['clean_config_snapshot'] = None
        st.rerun()

        new_id = str(uuid.uuid4())
        new_ref = get_next_ref()
        
        data = prepare_data()
        data['ref_id'] = new_ref
        
        new_config = {
            'id': new_id,
            'ref': new_ref,
            'data': data,
            'config_type': 'Volet Roulant'
        }
        
        if 'project' not in s: s['project'] = {'configs': []}
        s['project']['configs'].append(new_config)
        
        st.toast(f"✅ {new_ref} ajouté !")
        
        # RESET Form - ROBUST CLEANUP
        # 1. Delete all vr_ keys from session_state (including widgets)
        keys_to_reset = [k for k in s.keys() if k.startswith('vr_')]
        for k in keys_to_reset:
             del s[k]
        
        # 2. Explicitly Re-init Defaults in Session State AND Widget Keys
        # This ensures that when widgets re-mount, they see these default values
        
        # Keys for widgets
        s['vr_w_in'] = 1000
        s['vr_h_in'] = 1000
        s['vr_qte_in'] = 1
        s['vr_ref_in'] = get_next_ref()
        
        # Keys for logic
        s['vr_mat'] = "Aluminium"
        s['vr_width'] = 1000
        s['vr_height'] = 1000
        s['vr_qte'] = 1
        s['ref_id'] = s['vr_ref_in']
        s['active_config_id'] = None
        s['vr_cable_side'] = "Gauche"
        s['vr_cable_side_in'] = "Gauche"
        s['vr_cable_len'] = "5 ML (Standard)"
            
        st.rerun()

    return s

def generate_svg_volet():
    """Génère le dessin SVG simplifié du Volet Roulant"""
    s = st.session_state
    w = s.get('vr_width', 1000)
    h = s.get('vr_height', 1000)
    
    h = s.get('vr_height', 1000)
    
    # V76 FIX: Revert to Real Dimensions (remove scale 0.3)
    # The container now handles the scaling via viewBox
    dw = w 
    dh = h 
    
    # Adjust visual constants relative to size?
    # Coffre/Coulisse sizes are physical constants usually (e.g. 150-300mm box)
    # But let's keep them as visual defaults if not specified.
    coffre_h = 180  # Default Box 180mm
    coulisse_w = 50 # Default Guide 50mm
    
    # Dynamic Font
    max_dim = max(dw, dh + coffre_h)
    font_dim = max(16, int(max_dim * 0.025))
    
    # V79 FIX for Volet Roulant: Dynamic ViewBox & Proportional Ticks

    # 1. Base Dimensions
    tick_size = font_dim * 0.6
    text_offset = font_dim * 1.2
    
    # 2. ViewBox Margins (Dynamic) - INCREASED
    safe_margin = font_dim * 8.0 # Was 4.0 - Doubled to ensure no clipping
    
    # Define bounding box including the box (coffre)
    # Origin is (0,0) for the object (coffre top-left) excluding margins
    # Object goes from (0,0) to (dw, dh)
    
    vb_x = -safe_margin
    vb_y = -safe_margin
    vb_w = dw + (safe_margin * 2)
    vb_h = dh + (safe_margin * 2)

    # Helper for Color Mapping
    def get_color_hex(c_name, default="#e0e0e0"):
        if not c_name or c_name == "-": return default
        c_map = {
            "Blanc 9010": "#ffffff",
            "Gris Anthracite 7016": "#383e42",
            "Gris Clair 7035": "#d7d7d7",
            "Noir 2100": "#1a1a1a",
            "Ivoire 1015": "#e6d690",
            "Chêne Doré": "#b08d55",
        }
        return c_map.get(c_name, default)

    # Local Helper for Rectangle (Returns String) - Fixes conflict with global draw_rect
    def draw_rect(x, y, w, h, fill, stroke="none", sw=1):
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" />'

    # Styles with dynamic colors
    fill_coffre = get_color_hex(s.get('vr_col_coffre'), "#e0e0e0")
    fill_tablier = get_color_hex(s.get('vr_col_tablier'), "#f0f8ff")
    fill_coulisse = get_color_hex(s.get('vr_col_coulisses'), "#ffffff")
    stroke_lame = get_color_hex(s.get('vr_col_lame_fin'), "#bcd") if s.get('vr_col_lame_fin') != "Autre (RAL)" else "#bcd" 
    
    style_coffre = f"fill:{fill_coffre}; stroke:#666; stroke-width:2;"
    style_tablier = f"fill:{fill_tablier}; stroke:#ccc; stroke-width:1;"
    style_lame = "stroke:#bcd; stroke-width:1;" 
    style_coulisse = f"fill:{fill_coulisse}; stroke:#888; stroke-width:1;"
    
    # Type of Visualization
    vr_type = s.get('vr_type_coffre', 'Coffre rénovation')
    is_axe_view = vr_type in ["Coffre traditionnel en bois", "Coffre titan extérieur"]

    # Draw Group starting at (0,0) - ViewBox handles the padding
    # Draw Group starting at (0,0) - ViewBox handles the padding
    svg_parts = []
    svg_parts.append(f'<g>')
    
    # 1. COFFRE / AXE
    # 1. COFFRE / AXE / TABLIER / COULISSES (Layering depends on view type)
    if is_axe_view:
        # --- AXIS VIEW (Tube + Flasques) ---
        axe_h = 50 # Diameter of the tube visual - Reduced from 80
        axe_y = 50 # Offset from top
        axe_mid_y = axe_y + (axe_h / 2) # 50 + 25 = 75
        
        # A. TABLIER (Background - Starts at middle of tube)
        y_tablier = axe_mid_y
        h_tablier_vis = dh - y_tablier
        
        # Tablier Background (Restored Color Logic)
        svg_parts.append(draw_rect(coulisse_w, y_tablier, dw - (2*coulisse_w), h_tablier_vis, fill_tablier, stroke="#ccc"))
        
        # Horizontal Slats Lines
        lame_type = s.get('vr_lame_thick', '40 mm')
        slat_h = 50 if "50" in lame_type else 40
        curr_y = y_tablier + slat_h
        while curr_y < dh - 20: 
            svg_parts.append(f'<line x1="{coulisse_w}" y1="{curr_y}" x2="{dw-coulisse_w}" y2="{curr_y}" style="{style_lame}" />')
            curr_y += slat_h

        # Lame Finale
        svg_parts.append(draw_rect(coulisse_w, dh - 20, dw - (2*coulisse_w), 20, get_color_hex(s.get("vr_col_lame_fin"), "#bcd"), stroke="#888"))

        # B. COULISSES (Guides - Start below brackets?)
        # Let's assume brackets are ~150 tall, guides start there.
        c_start_y = 150
        c_h = dh - c_start_y
        svg_parts.append(draw_rect(0, c_start_y, coulisse_w, c_h, fill_coulisse, stroke="#888")) # Left
        svg_parts.append(draw_rect(dw-coulisse_w, c_start_y, coulisse_w, c_h, fill_coulisse, stroke="#888")) # Right

        # C. TUBE / AXIS (Foreground)
        # Left Flasque (Bracket)
        svg_parts.append(draw_rect(0, 0, 10, 150, "#888"))
        # Right Flasque (Bracket)
        svg_parts.append(draw_rect(dw-10, 0, 10, 150, "#888"))
        
        # Tube (Cylinder) - BOTTOM HALF ONLY (Plain Tube)
        # Top half (axe_y to axe_mid_y) is covered by rolled slats
        # Bottom half (axe_mid_y to axe_y + axe_h) is visible tube
        
        # 1. ROLLED SLATS on TOP HALF (axe_y to axe_mid_y)
        # Draw background for rolled part (same width as tablier)
        roll_h = axe_mid_y - axe_y
        svg_parts.append(draw_rect(coulisse_w, axe_y, dw-(2*coulisse_w), roll_h, fill_tablier, stroke="#999"))
        # Draw slats lines on the roll - Use consistent slat_h
        # Start slightly offset so we see a line if space is tight
        roll_y = axe_y + (slat_h * 0.5) 
        while roll_y < axe_mid_y:
            svg_parts.append(f'<line x1="{coulisse_w}" y1="{roll_y}" x2="{dw-coulisse_w}" y2="{roll_y}" style="{style_lame}" />')
            roll_y += slat_h 
            
        # 2. VISIBLE TUBE on BOTTOM HALF (axe_mid_y to bottom of axis)
        # Bottom half height is also roll_h basically
        svg_parts.append(draw_rect(10, axe_mid_y, dw-20, roll_h, "#d0d0d0", stroke="#999"))
        # Tube visual details
        svg_parts.append(draw_rect(10, axe_mid_y+5, dw-20, 1, "#bbb"))
        svg_parts.append(draw_rect(10, axe_mid_y+15, dw-20, 1, "#bbb"))
        
        # D. ATTACHES / CLIPS (On top of Tube)
        nb_attaches = 2 if dw < 1200 else (3 if dw < 2000 else 4)
        spacing = (dw - 20) / (nb_attaches + 1)
        clip_w = 20
        
        for i in range(1, nb_attaches + 1):
             cx = 10 + (spacing * i) - (clip_w / 2)
             # Draw strap/clip crossing the tube/tablier junction
             svg_parts.append(draw_rect(cx, axe_mid_y - 5, clip_w, 15, "#444")) # Clip body
             svg_parts.append(draw_rect(cx+5, axe_mid_y - 12, 10, 8, "#222")) # Hook/Buckle

    else:
        # --- BOX VIEW (Standard) ---
        # A. TABLIER (Below Box)
        y_tablier = coffre_h
        h_tablier_vis = dh - coffre_h
        
        svg_parts.append(f'<rect x="{coulisse_w}" y="{y_tablier}" width="{dw - (2*coulisse_w)}" height="{h_tablier_vis}" style="{style_tablier}" />')
        
        # Slats
        lame_type = s.get('vr_lame_thick', '40 mm')
        slat_h = 50 if "50" in lame_type else 40
        curr_y = y_tablier + slat_h
        while curr_y < dh - 20: 
            svg_parts.append(f'<line x1="{coulisse_w}" y1="{curr_y}" x2="{dw-coulisse_w}" y2="{curr_y}" style="{style_lame}" />')
            curr_y += slat_h
            
        # Lame Finale
        svg_parts.append(f'<rect x="{coulisse_w}" y="{dh - 20}" width="{dw - (2*coulisse_w)}" height="20" fill="{get_color_hex(s.get("vr_col_lame_fin"), "#bcd")}" stroke="#888" />')

        # B. COULISSES
        svg_parts.append(f'<rect x="0" y="{coffre_h}" width="{coulisse_w}" height="{dh - coffre_h}" style="{style_coulisse}" />') # Left
        svg_parts.append(f'<rect x="{dw - coulisse_w}" y="{coffre_h}" width="{coulisse_w}" height="{dh - coffre_h}" style="{style_coulisse}" />') # Right

        # C. COFFRE (Box - Drawn LAST to cover top)
        svg_parts.append(f'<rect x="0" y="0" width="{dw}" height="{coffre_h}" style="{style_coffre}" />')
    
    # Solar Panel
    if s.get('vr_proto') == "IO SOLAIRE":
        side = s.get('vr_cable_side', 'Droite')
        sp_w = 400 
        sp_h = 80 
        sp_y = (coffre_h - sp_h) / 2
        sp_x = (dw - sp_w - 50) if side == "Droite" else 50
        
        svg_parts.append(f'<rect x="{sp_x}" y="{sp_y}" width="{sp_w}" height="{sp_h}" fill="#2c3e50" stroke="#111" />')
        svg_parts.append(f'<line x1="{sp_x + sp_w/2}" y1="{sp_y}" x2="{sp_x + sp_w/2}" y2="{sp_y+sp_h}" stroke="#555" />')

    # Cable Exit
    if s.get('vr_type') == "Motorisé":
        side = s.get('vr_cable_side', 'Droite')
        cx = dw if side == "Droite" else 0
        cy = coffre_h / 2
        d_cable = f"M{cx},{cy} Q{cx+15},{cy} {cx+15},{cy+15} T{cx+15},{cy+30}" if side == "Droite" else f"M{cx},{cy} Q{cx-15},{cy} {cx-15},{cy+15} T{cx-15},{cy+30}"
        svg_parts.append(f'<path d="{d_cable}" stroke="orange" stroke-width="3" fill="none" />')
        svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="3" fill="orange" />')
        
    # Crank
    if s.get('vr_type') == "Manuel":
        side = s.get('vr_crank_side', 'Droite')
        offset = 15 if side == "Droite" else -15 
        cx = (dw - (coulisse_w/2)) if side == "Droite" else (coulisse_w/2)
        cy_top = coffre_h
        try: l_mm = int(s.get('vr_crank_len', '1200'))
        except: l_mm = 1200
        l_vis = l_mm 
        cy_bot = cy_top + l_vis
        rod_x = (dw - 5) if side == "Droite" else 5
        
        svg_parts.append(f'<line x1="{rod_x}" y1="{cy_top}" x2="{rod_x}" y2="{cy_bot}" stroke="#666" stroke-width="5" stroke-linecap="round" />')
        svg_parts.append(f'<line x1="{rod_x}" y1="{cy_bot}" x2="{rod_x + (10 if side=="Droite" else -10)}" y2="{cy_bot+10}" stroke="#666" stroke-width="5" stroke-linecap="round" />')
        svg_parts.append(f'<line x1="{rod_x}" y1="{cy_top}" x2="{rod_x}" y2="{cy_bot}" stroke="#f0f0f0" stroke-width="3" stroke-linecap="round" />')
        svg_parts.append(f'<line x1="{rod_x}" y1="{cy_bot}" x2="{rod_x + (10 if side=="Droite" else -10)}" y2="{cy_bot+10}" stroke="#f0f0f0" stroke-width="3" stroke-linecap="round" />')

        # Dimension Line for Crank
        dim_x = rod_x + (font_dim * 3 if side == "Droite" else -(font_dim * 3))
        
        svg_parts.append(f'<line x1="{dim_x}" y1="{cy_top}" x2="{dim_x}" y2="{cy_bot}" stroke="#444" stroke-width="1" />')
        
        # Arrows for Crank
        ts = tick_size # shorthand
        svg_parts.append(f'<path d="M{dim_x-ts*0.5},{cy_top+ts} L{dim_x},{cy_top} L{dim_x+ts*0.5},{cy_top+ts}" fill="none" stroke="#444" />')
        svg_parts.append(f'<path d="M{dim_x-ts*0.5},{cy_bot-ts} L{dim_x},{cy_bot} L{dim_x+ts*0.5},{cy_bot-ts}" fill="none" stroke="#444" />')
        
        # Text Label
        text_x = dim_x + (text_offset if side == "Droite" else -text_offset)
        text_y = cy_top + (l_vis / 2)
        svg_parts.append(f'<text x="{text_x}" y="{text_y}" text-anchor="middle" transform="rotate(-90, {text_x}, {text_y})" font-family="sans-serif" font-size="{font_dim}" fill="#444">{l_mm}</text>')
        svg_parts.append(f'<line x1="{rod_x}" y1="{cy_top}" x2="{dim_x}" y2="{cy_top}" stroke="#ccc" stroke-dasharray="2,2" />')

    # Box X cross
    svg_parts.append(f'<line x1="0" y1="0" x2="{dw}" y2="{coffre_h}" stroke="#ccc" />')
    svg_parts.append(f'<line x1="0" y1="{coffre_h}" x2="{dw}" y2="0" stroke="#ccc" />')
    
    # 4. Dimensions Arrows (FIXED PROPORTIONS)
    # Width (Bottom)
    dim_y_w = dh + (font_dim * 3.5) # Pushed down (was 2)
    svg_parts.append(f'<line x1="0" y1="{dim_y_w}" x2="{dw}" y2="{dim_y_w}" stroke="black" />')
    # Width Ticks
    svg_parts.append(f'<path d="M{tick_size},{dim_y_w-tick_size} L0,{dim_y_w} L{tick_size},{dim_y_w+tick_size}" fill="none" stroke="black" />')
    svg_parts.append(f'<path d="M{dw-tick_size},{dim_y_w-tick_size} L{dw},{dim_y_w} L{dw-tick_size},{dim_y_w+tick_size}" fill="none" stroke="black" />')
    # Width Text
    svg_parts.append(f'<text x="{dw/2}" y="{dim_y_w - text_offset}" text-anchor="middle" font-family="sans-serif" font-size="{font_dim*1.2}">{int(w)} mm</text>')
    
    # Height (Left)
    dim_x_h = -(font_dim * 3.5) # Pushed left (was 2)
    svg_parts.append(f'<line x1="{dim_x_h}" y1="0" x2="{dim_x_h}" y2="{dh}" stroke="black" />')
    # Height Ticks
    svg_parts.append(f'<path d="M{dim_x_h-tick_size},{tick_size} L{dim_x_h},0 L{dim_x_h+tick_size},{tick_size}" fill="none" stroke="black" />')
    svg_parts.append(f'<path d="M{dim_x_h-tick_size},{dh-tick_size} L{dim_x_h},{dh} L{dim_x_h+tick_size},{dh-tick_size}" fill="none" stroke="black" />')
    # Height Text
    svg_parts.append(f'<text x="{dim_x_h - text_offset}" y="{dh/2}" text-anchor="middle" transform="rotate(-90, {dim_x_h - text_offset}, {dh/2})" font-family="sans-serif" font-size="{font_dim*1.2}">{int(h)} mm</text>')
    
    # Projection lines for dimensions
    # Vertical projections for Width Dim
    svg_parts.append(f'<line x1="0" y1="{dh}" x2="0" y2="{dim_y_w}" stroke="#ccc" stroke-dasharray="4,4" />')
    svg_parts.append(f'<line x1="{dw}" y1="{dh}" x2="{dw}" y2="{dim_y_w}" stroke="#ccc" stroke-dasharray="4,4" />')
    # Horizontal projections for Height Dim
    svg_parts.append(f'<line x1="0" y1="0" x2="{dim_x_h}" y2="0" stroke="#ccc" stroke-dasharray="4,4" />')
    svg_parts.append(f'<line x1="0" y1="{dh}" x2="{dim_x_h}" y2="{dh}" stroke="#ccc" stroke-dasharray="4,4" />')
    
    svg_parts.append('</g>')
    
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb_x} {vb_y} {vb_w} {vb_h}" style="background-color:white;">{"".join(svg_parts)}</svg>'

def render_html_volet(s, svg_string, logo_b64):
    """Génération HTML pour Volet Roulant"""
    
    # Pre-calc Observations
    obs_vr_html = ""
    if s.get('vr_obs'):
        obs_vr_html = f"""
            <div class="section-block">
                <h3>Observations</h3>
                <div class="panel">
                    <div class="panel-row" style="display:block; min-height:auto; padding:10px;"><span class="val" style="text-align:left; width:100%; white-space: pre-wrap;">{s.get('vr_obs')}</span></div>
                </div>
            </div>
        """

    css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
        body { font-family: 'Roboto', sans-serif; -webkit-print-color-adjust: exact; padding: 0; margin: 0; background-color: #fff; color: #333; }
        .page-container { max-width: 210mm; margin: 0 auto; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; border-bottom: 3px solid #2c3e50; padding-bottom: 15px; }
        .header-left img { max-height: 70px; width: auto; }
        .header-left .subtitle { color: #3498db; font-size: 14px; margin-top: 5px; font-weight: 400; }
        .header-right { text-align: right; padding-right: 5px; }
        .header-right .label { font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 2px; }
        .header-right .ref { font-size: 24px; font-weight: bold; color: #000; margin-bottom: 2px; line-height: 1; }
        .header-right .date { font-size: 11px; color: #666; }
        
        .section-block { margin-bottom: 25px; break-inside: avoid; }
        h3 { font-size: 15px; color: #2c3e50; margin: 0 0 12px 0; border-left: 5px solid #3498db; padding-left: 10px; line-height: 1.2; text-transform: uppercase; letter-spacing: 0.5px; }
        
        .panel { background: #fdfdfd; padding: 15px; border: 1px solid #eee; border-radius: 4px; font-size: 11px; }
        .panel-row { display: flex; justify-content: space-between; align-items: center; padding: 5px 0; border-bottom: 1px dotted #ccc; height: 26px; }
        .panel-row:last-child { border-bottom: none; }
        .panel-row .lbl { font-weight: bold; color: #444; width: 40%; display: flex; align-items: center; }
        .panel-row .val { font-weight: normal; color: #000; text-align: right; width: 60%; display: flex; align-items: center; justify-content: flex-end; }
        
        .visual-box { border: 1px solid #eee; margin-top: 20px; display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative; width: 100%; height: auto; min-height: 500px; padding: 20px 0 40px 0; }
        .visual-box svg { height: auto; width: auto; max-width: 95%; max-height: 450px; }
        
        .footer { position: fixed; bottom: 5mm; left: 0; right: 0; font-size: 9px; color: #999; text-align: center; }

        @media print {
            @page { size: A4; margin: 12mm; }
            body { padding: 0; background: white; -webkit-print-color-adjust: exact; }
            .page-container { margin: 0; padding: 0; box-shadow: none; max-width: none; width: 100%; }
            h3 { break-after: avoid; }
            .page-break { page-break-before: always; padding-top: 30px; }
        }
    </style>
    """
    
    # Pre-calc Observations
    obs_vr_html = ""
    if s.get('vr_obs'):
        obs_vr_html = f"""
            <div class="section-block">
                <h3>Observations</h3>
                <div class="panel">
                    <div class="panel-row" style="display:block; min-height:auto; padding:10px;"><span class="val" style="text-align:left; width:100%; white-space: pre-wrap;">{s.get('vr_obs')}</span></div>
                </div>
            </div>
        """

    # Logo
    logo_html = "<h1>Fiche Technique</h1>"
    if logo_b64:
        logo_html = f'<img src="data:image/jpeg;base64,{logo_b64}" alt="Logo">'
    
    ref_id = s.get('ref_id', 'VR-01')
    import datetime
    
    # Pre-calculate Motor Details HTML to avoid f-string syntax errors
    if s.get('vr_type') == 'Motorisé':
        motor_details_html = f"""
                    <div class="panel-row"><span class="lbl">Motorisation</span> <span class="val">{s.get('vr_motor', '-')}</span></div>
                    <div class="panel-row"><span class="lbl">Puissance</span> <span class="val">{s.get('vr_power', '-')}</span></div>
                    <div class="panel-row"><span class="lbl">Protocole</span> <span class="val">{s.get('vr_proto', '-')}</span></div>
                    <div class="panel-row"><span class="lbl">Sortie de fil</span> <span class="val">{s.get('vr_cable_side', '-')}</span></div>
                    <div class="panel-row"><span class="lbl">Longueur Câble</span> <span class="val">{s.get('vr_cable_len', '-')}</span></div>
        """
    else:
        motor_details_html = f"""
                    <div class="panel-row"><span class="lbl">Sortie Manivelle</span> <span class="val">{s.get('vr_crank_side', '-')}</span></div>
                    <div class="panel-row"><span class="lbl">Longueur Manivelle</span> <span class="val">{s.get('vr_crank_len', '-')} mm</span></div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{css}</head>
    <body>
        <div class="page-container">
            <!-- HEADER -->
            <div class="header">
                <div class="header-left">
                    {logo_html}
                    <div class="subtitle">Volet Roulant {s.get('vr_mat', 'Aluminium')}</div>
                </div>
                <div class="header-right">
                    <div class="label">RÉFÉRENCE CHANTIER</div>
                    <div class="ref">{ref_id}</div>
                    <div class="date">{datetime.datetime.now().strftime('%d/%m/%Y')}</div>
                </div>
            </div>
            
            <!-- INFORMATIONS -->
            <div class="section-block">
                <h3>Informations Générales</h3>
                <div class="panel">
                    <div class="panel-row"><span class="lbl">Repère</span> <span class="val">{ref_id}</span></div>
                    <div class="panel-row"><span class="lbl">Quantité</span> <span class="val">{s.get('vr_qte', 1)}</span></div>
                    <div class="panel-row"><span class="lbl">Type de Coffre</span> <span class="val">{s.get('vr_type_coffre', '-')}</span></div>
                    <div class="panel-row"><span class="lbl">Type de côtes</span> <span class="val">{s.get('vr_dim_type', 'Côtes Tableau')}</span></div>
                    <div class="panel-row"><span class="lbl">Dimensions</span> <span class="val">L {s.get('vr_width', 0)} x H {s.get('vr_height', 0)} mm{" + enroulement" if s.get('vr_add_winding') else ""}</span></div>
                </div>
            </div>

            <!-- DETAILS TECHNIQUES -->
            <div class="section-block">
                <h3>Détails Techniques</h3>
                <div class="panel">
                    <div class="panel-row"><span class="lbl">Couleur Coffre</span> <span class="val">{s.get('vr_col_coffre', '-')}</span></div>
                    <div class="panel-row"><span class="lbl">Couleur Coulisses</span> <span class="val">{s.get('vr_col_coulisses', '-')}</span></div>
                    <div class="panel-row"><span class="lbl">Couleur Tablier</span> <span class="val">{s.get('vr_col_tablier', '-')}</span></div>
                    <div class="panel-row"><span class="lbl">Couleur Lame Finale</span> <span class="val">{s.get('vr_col_lame_fin', '-')}</span></div>
                    
                    <div class="panel-row" style="border-top: 2px solid #eee; margin-top: 5px; padding-top: 5px;"><span class="lbl">Type de Manoeuvre</span> <span class="val">{s.get('vr_type', 'Manuel')}</span></div>
                    
                    {motor_details_html}
                </div>
            </div>
            
            <!-- PLAN -->
            <div class="section-block">
                <h3>Schéma Technique</h3>
                <div class="visual-box">
                    {svg_string}
                    <div style="position:absolute; bottom:10px; font-size:10px; color:#aaa;">Vue Extérieure - {s.get('vr_dim_type')}</div>
                </div>
            </div>

            <!-- OBSERVATIONS -->
            <!-- OBSERVATIONS -->
            {obs_vr_html}
            
            <div class="footer">
                Document généré automatiquement - Miroiterie Yerroise
            </div>
        </div>
    </body>
    </html>
    """
    return html

# --- MODULE HABILLAGE (INTÉGRÉ) ---
# ==============================================================================

# Base directory for artifacts
# Base directory for artifacts
# (Déplacé en haut de fichier pour portée globale)

# Define Profile Models based on User Images (1-5)

# Define Profile Models based on User Images (1-5)







# ==============================================================================
# --- MODULE VITRAGE (NOUVEAU) ---
# ==============================================================================






def serialize_vitrage_config():
    """Capture toutes les variables Vitrage pour la sauvegarde."""
    # V10 FIX: Exclude ephemeral button keys from save
    data = {}
    for k, v in st.session_state.items():
        if k.startswith('vit_') or k.startswith('v_'):
            # Filter out known button keys
            if 'btn' in k or 'updup' in k or 'save_u' in k or 'del_u' in k or 'add_new' in k:
                continue
            data[k] = v
            
    # FORCE RECALC RESUME (Fix for "None" or stale data)
    s = st.session_state
    vt = s.get('vit_type_mode', 'Double Vitrage')
    if vt == "Double Vitrage":
        # Format V11: Vit. ep_ext / ep_air / ep_int - inter + GAZ gaz
        ep_e = s.get('vit_ep_ext','4').replace(' mm', '')
        ep_i = s.get('vit_ep_int','4').replace(' mm', '')
        ep_a = s.get('vit_ep_air','16').replace(' mm', '')
        
        c_e = s.get('vit_couche_ext','Aucune')
        c_i = s.get('vit_couche_int','Aucune')
        
        sf_e = "FE" if "FE" in c_e else (" CS" if "Contrôle" in c_e else "")
        sf_i = "FE" if "FE" in c_i else ""
        
        ty_e = s.get('vit_type_ext','Clair')
        st_e = f" {ty_e}" if ty_e != "Clair" else ""
        
        ty_i = s.get('vit_type_int','Clair')
        st_i = f" {ty_i}" if ty_i != "Clair" else ""
        
        gaz = s.get('vit_gaz','Argon').upper()
        inter = s.get('vit_intercalaire','Alu').upper()
        
        resume = f"Vit. {ep_e}{st_e}{sf_e} / {ep_a} / {ep_i}{st_i}{sf_i} - {inter} + GAZ {gaz}"

    elif vt == "Simple Vitrage":
        ep_e = s.get('vit_ep_ext','4').replace(' mm', '')
        ty_e = s.get('vit_type_ext','Clair')
        resume = f"Simple {ep_e} {ty_e}"
    else:
        resume = "Panneau Plein"
    data['vit_resume'] = resume
    
    # Add Standard Keys for Project Management
    # V11 FIX: Default to next Ref if missing
    data['ref_id'] = st.session_state.get('vit_ref', get_next_project_ref())
    data['qte_val'] = st.session_state.get('vit_qte', 1)
    data['mode_module'] = 'Vitrage'
    return data

def render_vitrage_form():
    """Formulaire de configuration Vitrage (Avancé)"""
    s = st.session_state
    
    # 0. Sync Ref
    if 'ref_id' not in s: s['ref_id'] = get_next_project_ref()

    # 1. Repère et Quantité
    with st.expander("📝 1. Repère et quantité", expanded=False):
        c_ref, c_qte = st.columns([3, 1])
        base_ref = s.get('ref_id', get_next_project_ref())
        s['vit_ref'] = c_ref.text_input("Repère", value=base_ref, key="vit_ref_in")
        s['ref_id'] = s['vit_ref']
        s['vit_qte'] = c_qte.number_input("Qté", 1, 100, 1, key="vit_qte_in")

    # 2. Matériaux et Cadre
    with st.expander("🧱 2. Châssis & Support", expanded=False):
        mat_options = ["Châssis aluminium", "Châssis PVC", "Châssis bois", "Chassis Acier", "Porte Sécurit", "Mur", "Vitrage Seul"]
        curr_mat = s.get('vit_mat', "Châssis aluminium")
        idx_mat = mat_options.index(curr_mat) if curr_mat in mat_options else 0
        s['vit_mat'] = st.selectbox("Matériau", mat_options, index=idx_mat, key="vit_mat_sel")
        
        chassis_opts = []
        if s['vit_mat'] == "Châssis aluminium": chassis_opts = ["Fixe", "Ouvrants", "Coulissant", "Basculant", "Mur rideau", "Verrière"]
        elif s['vit_mat'] == "Châssis PVC": chassis_opts = ["Fixe", "Ouvrants"]
        elif s['vit_mat'] == "Châssis bois": chassis_opts = ["Parecloses + Clous", "Mastic"]
        elif s['vit_mat'] == "Chassis Acier": chassis_opts = ["Mastic", "Marquise", "Fer à T", "Châssis U"]
        elif s['vit_mat'] == "Porte Sécurit": chassis_opts = ["Verre seul"]
        elif s['vit_mat'] == "Mur": chassis_opts = ["A coller", "Rail haut et bas"]
        else: chassis_opts = ["Standard"]
            
        s['vit_type_chassis'] = st.selectbox("Type de châssis", chassis_opts, key="vit_chas_sel")

    # 3. Composition Vitrage (V9: CLOSED DEFAULT)
    with st.expander("🔍 3. Composition Vitrage", expanded=False):
        # Type de Vitrage Checkbox/Radio
        vit_type_mode = st.radio("Type de Vitrage", ["Double Vitrage", "Simple Vitrage", "Panneau"], horizontal=True, key="vit_type_mode")
        
        c_ext, c_air, c_int = st.columns(3)
        
        # EXTÉRIEUR
        with c_ext:
            st.markdown("**Extérieur**")
            s['vit_ep_ext'] = st.selectbox("Épaisseur Ext", ["4 mm", "6 mm", "8 mm", "10 mm", "33.2", "44.2", "SP10", "Panneau"], key="v_ep_e")
            s['vit_type_ext'] = st.selectbox("Type Ext", TYPES_VERRE + ["Granité", "Delta Mat", "Antelio"], key="v_ty_e")
            s['vit_couche_ext'] = st.selectbox("Couche Ext", ["Aucune", "FE (Faible Émissivité)", "Contrôle Solaire"], key="v_co_e")
            s['vit_fac_ext'] = st.selectbox("Façonnage Ext", ["CB", "JPP", "JPI"], key="v_fa_e")
            
        # LAME D'AIR (Si Double)
        with c_air:
            if vit_type_mode == "Double Vitrage":
                st.markdown("**Lame d'Air**")
                s['vit_ep_air'] = st.selectbox("Épaisseur Air", ["6 mm", "8 mm", "10 mm", "12 mm", "14 mm", "16 mm", "18 mm", "20 mm"], index=7, key="v_ep_a")
                s['vit_gaz'] = st.selectbox("Gaz", ["Argon", "Air", "Krypton"], key="v_gaz")
                s['vit_intercalaire'] = st.selectbox("Intercalaire", ["Alu", "Warm Edge Noir", "Warm Edge Gris"], index=1, key="v_int_c")
            else:
                st.markdown("")
                # V9 Polish: Removed Info
                s['vit_ep_air'] = "-"
                
        # INTÉRIEUR
        with c_int:
            if vit_type_mode == "Double Vitrage":
                st.markdown("**Intérieur**")
                s['vit_ep_int'] = st.selectbox("Épaisseur Int", ["4 mm", "6 mm", "8 mm", "10 mm", "33.2", "44.2"], key="v_ep_i")
                s['vit_type_int'] = st.selectbox("Type Int", ["Clair", "Dépoli"], key="v_ty_i")
                s['vit_couche_int'] = st.selectbox("Couche Int", ["Aucune", "FE (Faible Émissivité)"], index=1, key="v_co_i")
                s['vit_fac_int'] = st.selectbox("Façonnage Int", ["CB", "JPP", "JPI"], key="v_fa_i")
            else:
                 st.markdown("")
                 # V9 Polish: Removed Info

        # Calcul Resume
        if vit_type_mode == "Double Vitrage":
            resume = f"{s['vit_ep_ext']} {s['vit_type_ext']} / {s['vit_ep_air']} {s['vit_gaz']} / {s['vit_ep_int']} {s['vit_type_int']}"
            if s['vit_couche_ext'] != "Aucune": resume += f" [{s['vit_couche_ext']}]"
            if s['vit_couche_int'] != "Aucune": resume += f" [{s['vit_couche_int']}]"
        elif vit_type_mode == "Simple Vitrage":
            resume = f"Simple {s['vit_ep_ext']} {s['vit_type_ext']}"
        else:
            resume = "Panneau Plein"
        s['vit_resume'] = resume

    # 4. Dimensions & Formes
    with st.expander("📐 4. Dimensions & Formes", expanded=False):
        # SHAPE SELECTION
        # SHAPE SELECTION
        shape_opts = ["Rectangulaire", "Forme A1 (Trapèze)", "Forme A2 (Pan Coupé)", "Forme B (Trapèze Double)", "Forme C (Cintre)", "Forme D (Rond/Ovale)", "Forme E (Découpe)"]
        s['vit_shape'] = st.selectbox("Forme du vitrage", shape_opts, key="vit_shape_sel")
        
        dim_types = ["Cotes Fabrication", "Clair de vue", "Fond de feuillure"]
        s['vit_dim_type'] = st.selectbox("Type de côtes", dim_types, key="vit_dim_t")
        
        c_w, c_h = st.columns(2)
        s['vit_width'] = c_w.number_input("Largeur (mm)", 0, 10000, 1000, 10, key="vit_w")
        s['vit_height'] = c_h.number_input("Hauteur (mm)", 0, 10000, 1000, 10, key="vit_h")
        
        # DYNAMIC SHAPE PARAMS
        if s['vit_shape'] != "Rectangulaire":
            st.markdown("##### Paramètres de la Forme")
            c_s1, c_s2 = st.columns(2)
            if "Forme A1" in s['vit_shape']:
                s['vit_sh_h1'] = c_s1.number_input("Hauteur Petite (H1)", 0, 10000, 500, key="v_sh_a_h1")
                s['vit_sh_h2'] = c_s2.number_input("Hauteur Grande (H2)", 0, 10000, 1000, key="v_sh_a_h2")
            elif "Forme A2" in s['vit_shape']:
                s['vit_sh_lc'] = c_s1.number_input("Largeur Coupe (Lx)", 0, 5000, 200, key="v_sh_a2_lx")
                s['vit_sh_hc'] = c_s2.number_input("Hauteur Coupe (Ly)", 0, 5000, 200, key="v_sh_a2_ly")
            elif "Forme B" in s['vit_shape']:
                c_a, c_b = st.columns(2)
                s['vit_sh_h1'] = c_a.number_input("Hauteur Gauche (H1)", 0, 10000, 500, key="v_sh_b_h1")
                s['vit_sh_h2'] = c_b.number_input("Hauteur Droite (H2)", 0, 10000, 500, key="v_sh_b_h2")
                c_c, c_d, c_e = st.columns(3)
                s['vit_sh_h3'] = c_c.number_input("Hauteur Pointe/Plat (H3)", 0, 10000, 750, key="v_sh_b_h3")
                s['vit_sh_l1'] = c_d.number_input("Pos. Début (L1)", 0, 10000, 500, key="v_sh_b_l1")
                s['vit_sh_l2'] = c_e.number_input("Largeur Plat (L2)", 0, 10000, 0, key="v_sh_b_l2")
            elif "Forme C" in s['vit_shape']:
                s['vit_sh_fleche'] = c_s1.number_input("Flèche (mm)", 0, 5000, 200, key="v_sh_c_f")
                s['vit_sh_ray'] = c_s2.number_input("Rayon (mm)", 0, 10000, 0, key="v_sh_c_r")
            elif "Forme D" in s['vit_shape']:
                st.info("Ellipse définie par Largeur x Hauteur.")
            elif "Forme E" in s['vit_shape']:
                s['vit_sh_enc_w'] = c_s1.number_input("Largeur Encoche", 0, 5000, 200, key="v_sh_e_w")
                s['vit_sh_enc_h'] = c_s2.number_input("Hauteur Encoche", 0, 5000, 200, key="v_sh_e_h")
            
        s['vit_h_bas'] = st.number_input("Hauteur bas du verre (mm)", 0, 5000, 0, 10, key="vit_hb")

        # Petits bois
        s['vit_pb_enable'] = st.checkbox("Petits bois (Traverses)", key="vit_pb_check")
        if s['vit_pb_enable']:
            c_pb1, c_pb2, c_pb3 = st.columns(3)
            s['vit_pb_hor'] = c_pb1.number_input("Traver. Horiz.", 0, 20, 0, key="vit_pb_h")
            s['vit_pb_vert'] = c_pb2.number_input("Traver. Vert.", 0, 20, 0, key="vit_pb_v")
            s['vit_pb_thick'] = c_pb3.number_input("Épaisseur (mm)", 10, 50, 26, key="vit_pb_th")

    # 5. Usinage / Façonnage Spécial
    with st.expander("🛠️ 5. Usinage / Façonnage Spécial", expanded=False):
        s['vit_usi_enable'] = st.checkbox("Activer l'usinage", key="v_usi_en")
        if s['vit_usi_enable']:
            st.markdown("**Trous**")
            nb_trous = st.number_input("Nombre de trous", 0, 10, 0, key="v_nb_trous")
            s['vit_nb_trous'] = nb_trous
            for i in range(nb_trous):
                st.markdown(f"**Trou {i+1}**")
                # V15 Polish: Selectbox on its own row
                st.selectbox(f"Bord (Trou {i+1})", ["1 (Bas G)", "2 (Haut G)", "3 (Haut D)", "4 (Bas D)"], index=0, key=f"v_t_ref_{i}")
                
                c_bx, c_by, c_bd = st.columns(3)
                c_bx.number_input(f"X (mm)", 0, 5000, 100, key=f"v_t_x_{i}")
                c_by.number_input(f"Y (mm)", 0, 5000, 100, key=f"v_t_y_{i}")
                c_bd.number_input(f"Dia (mm)", 0, 200, 10, key=f"v_t_d_{i}")
            
            st.markdown("---")
            st.markdown("**Encoches (Rectangulaires)**")
            nb_enc = st.number_input("Nombre d'encoches", 0, 4, 0, key="v_nb_enc")
            s['vit_nb_enc'] = nb_enc
            for i in range(nb_enc):
                st.markdown(f"**Encoche {i+1}**")
                # V15 Polish: Selectbox on its own row
                st.selectbox(f"Bord (Encoche {i+1})", ["1 (Bas G)", "2 (Haut G)", "3 (Haut D)", "4 (Bas D)"], index=0, key=f"v_e_ref_{i}")
                
                c_ex, c_ey, c_ew, c_eh = st.columns(4)
                c_ex.number_input(f"X (mm)", 0, 5000, 0, key=f"v_e_x_{i}")
                c_ey.number_input(f"Y (mm)", 0, 5000, 0, key=f"v_e_y_{i}")
                c_ew.number_input(f"Largeur", 0, 5000, 50, key=f"v_e_w_{i}")
                c_eh.number_input(f"Hauteur", 0, 5000, 50, key=f"v_e_h_{i}")

            st.markdown("---")
            # Mickey 101 - UI Update per Request
            # 1. Checkbox First
            s['vit_mickey_101'] = st.checkbox("Encoche 101 (Mickey)", key="v_mic_on")
            
            # 2. Logic if Checked
            if s['vit_mickey_101']:
                 s['vit_mickey_side'] = st.radio("Côté", ["Gauche", "Droite"], horizontal=True, key="v_mic_side")
                 st.caption("ℹ️ Axe du carré à 65 mm du bord")

    # 6. Observations
    with st.expander("📝 6. Observations", expanded=False):
        s['vit_obs'] = st.text_area("Notes", value=s.get('vit_obs', ''), key="vit_obs_in")
        
    # --- ACTIONS CRUD ---
    st.markdown("### 💾 Actions")
    active_id = s.get('active_config_id')
    if active_id: st.caption(f"✏️ Édition : {s.get('vit_ref', 'V-??')}")

    c_btn0, c_btn1, c_btn2 = st.columns(3)
    
    # UPDATE
    # UPDATE
    # V75 UPDATE: Consolidated "Enregistrer" Button
    if c_btn0.button("💾 Enregistrer", use_container_width=True, key="vit_upd", help="Sauvegarder la configuration actuelle"):
         data = serialize_vitrage_config()
         
         if active_id:
             # UPDATE EXISTING
             update_current_config_in_project(active_id, data, s['vit_ref'])
             
             # Update Snapshot
             st.session_state['clean_config_snapshot'] = get_config_snapshot(data)
             
             st.toast(f"✅ {s['vit_ref']} mis à jour !")
             st.rerun()
         else:
             # CREATE NEW
             new_ref = s.get('vit_ref', 'V-01')
             new_id = add_config_to_project(data, new_ref)
             
             # Set as Active
             st.session_state['active_config_id'] = new_id
             
             # Update Snapshot
             st.session_state['clean_config_snapshot'] = get_config_snapshot(data)
             
             st.toast(f"✅ {new_ref} enregistré !")
             st.rerun()

    # DUPLICAT (Save Copy)
    if c_btn1.button("Dupliquer", use_container_width=True, key="vit_updup", help="Créer une copie"):
        data = serialize_vitrage_config()
        # New Ref
        current_ref = s.get('vit_ref', 'V-01')
        new_ref = f"{current_ref} (Copie)"
        
        new_id = add_config_to_project(data, new_ref)
        s['pending_new_id'] = new_id
        # Auto Increment
        s['pending_ref_id'] = get_next_ref(new_ref)
        
        st.session_state['active_config_id'] = new_id
        
        # V76 Fix: Use pending_updates for widget keys
        if 'pending_updates' not in st.session_state: st.session_state['pending_updates'] = {}
        st.session_state['pending_updates']['ref_id'] = new_ref
        
        st.session_state['clean_config_snapshot'] = get_config_snapshot(data)
        
        st.toast(f"✅ Copie créée : {new_ref}")
        st.rerun()

    # NOUVEAU (Reset)
    if c_btn2.button("Nouveau (Reset)", use_container_width=True, key="vit_upnew", help="Sauvegarder et Réinitialiser"):
        data = serialize_vitrage_config()
        current_ref = s.get('vit_ref', 'V-01')
        
        if active_id:
            # UPDATE EXISTING
            update_current_config_in_project(active_id, data, current_ref)
            st.toast(f"✅ {current_ref} mis à jour !")
        else:
             # CREATE NEW
             new_id = add_config_to_project(data, current_ref)
             st.toast(f"✅ {current_ref} enregistré !")
             
        # RESET
        reset_config(rerun=False)
        s['active_config_id'] = None
        s['clean_config_snapshot'] = None
        s['pending_ref_id'] = get_next_project_ref()
        st.rerun()

    return s










def generate_svg_vitrage():
    """Génère le dessin SVG Vitrage (Style Menuiserie V73) - V7 White + Axis Dims"""
    s = st.session_state
    
    # 1. Setup Canvas
    w_mm = s.get('vit_width', 1000)
    h_mm = s.get('vit_height', 1000)
    
    # V76 FIX: Dynamic Font
    max_dim = max(w_mm, h_mm)
    font_dim = max(16, int(max_dim * 0.025))

    
    # Layers (Z-Index equivalent via sort)
    # 0: BG, 10: Frame, 20: Glass, 30: Petit Bois/Usi, 40: Dims
    z_bg, z_outer, z_frame, z_glass, z_pb, z_dim = 0, 5, 10, 20, 30, 40

    # HELPER: Smart Offset based on Value (Legacy - Removed in favor of Rank System)
    # def get_dim_offset(val): ... 

    # SMART DIMENSION SYSTEM v1
    # Buckets to collect dimensions per edge
    dim_buckets = {
        "bottom": [], # (val, x1, y1, x2, y2, color, label, avoid_pt)
        "top": [],
        "left": [],
        "right": []
    }

    def add_smart_dim(edge, val, x1, y1, x2, y2, color="blue", label="", avoid_pt=None):
        dim_buckets[edge].append({
            "val": val, 
            "pts": (x1, y1, x2, y2),
            "color": color,
            "label": label,
            "avoid": avoid_pt
        })

    # HELPER: Draw Dimension (Low Level) - V79 Dynamic
    def draw_dim(x1, y1, x2, y2, val, offset=50, color="blue", label_prefix="", avoid_point=None):
        import math
        d = math.sqrt((x2-x1)**2 + (y2-y1)**2)
        if d == 0: return ""
        ux, uy = (x2-x1)/d, (y2-y1)/d
        nx, ny = -uy, ux # Initial Normal
        
        mx, my = (x1+x2)/2, (y1+y2)/2
        
        # Auto-Flip if avoid_point provided (Center of glass)
        if avoid_point:
            cx, cy = avoid_point
            # Vector Center -> Midpoint
            vx, vy = mx - cx, my - cy
            # Dot product with Normal
            dot = nx * vx + ny * vy
            if dot < 0:
                nx, ny = -nx, -ny
                
        # Apply Offset
        ax, ay = x1 + nx*offset, y1 + ny*offset
        bx, by = x2 + nx*offset, y2 + ny*offset
        
        # PROPORTIONAL MARKERS
        mk_len = font_dim * 0.5
        stroke_w = max(1, font_dim * 0.05)
        
        out = ""
        out += f'<line x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}" stroke="{color}" stroke-width="{stroke_w}" />'
        
        # Ticks
        out += f'<line x1="{ax - ux*mk_len - nx*mk_len}" y1="{ay - uy*mk_len - ny*mk_len}" x2="{ax + ux*mk_len + nx*mk_len}" y2="{ay + uy*mk_len + ny*mk_len}" stroke="{color}" stroke-width="{stroke_w}" />'
        out += f'<line x1="{bx - ux*mk_len - nx*mk_len}" y1="{by - uy*mk_len - ny*mk_len}" x2="{bx + ux*mk_len + nx*mk_len}" y2="{by + uy*mk_len + ny*mk_len}" stroke="{color}" stroke-width="{stroke_w}" />'
        out += f'<line x1="{x1}" y1="{y1}" x2="{ax}" y2="{ay}" stroke="{color}" stroke-width="{stroke_w*0.5}" stroke-dasharray="2,2" />'
        out += f'<line x1="{x2}" y1="{y2}" x2="{bx}" y2="{by}" stroke="{color}" stroke-width="{stroke_w*0.5}" stroke-dasharray="2,2" />'
        
        mx_dim, my_dim = (ax+bx)/2, (ay+by)/2
        
        sign_off = 1 if offset >= 0 else -1
        txt_gap = font_dim * 0.6 
        
        tx = mx_dim + nx * (sign_off * txt_gap)
        ty = my_dim + ny * (sign_off * txt_gap)
        
        suffix = ""
        if "Axe" in label_prefix: suffix = " mm"
        
        out += f'<text x="{tx}" y="{ty}" fill="{color}" font-size="{font_dim}" font-weight="bold" text-anchor="middle" dominant-baseline="middle" transform="rotate(0, {mx_dim}, {my_dim})" paint-order="stroke" stroke="white" stroke-width="3">{label_prefix}{val:.0f}{suffix}</text>'
        return out

    # 2. Logic: Glass Only?
    # Corrected Logic: Check Material (vit_mat) AND Type Mode
    # If "Porte Sécurit", "Vitrage Seul", or "Mur" -> No Frame
    mat = s.get('vit_mat', '')
    glass_only = (mat in ["Porte Sécurit", "Vitrage Seul", "Mur"] or s.get('vit_type_mode') == "Panneau")
    
    # 3. Define Draw Area (Dynamic ViewBox)
    # Origin is (0,0) inside the SVG, but we use ViewBox to shift margins
    # The Object (Glass/Frame) starts at (0,0) in our coordinate system
    
    # Dynamic Margins for ViewBox - INCREASED AGAIN for Extreme Sizes
    margin_safe = font_dim * 10.0 
    
    x0, y0 = 0, 0 # Object Start
    
    # ViewBox definition
    # Left/Top needs negative margin to show dimensions
    vb_x = -margin_safe
    vb_y = -margin_safe
    # Width/Height extends beyond object size
    vb_w = w_mm + (margin_safe * 2)
    vb_h = h_mm + (margin_safe * 2)

    
    svg_list = []
    
    # Frame/Glass Rect Logic
    th_inner = 26
    th_outer = 14
    
    # Default: Frame Draw
    if glass_only:
        # Just Glass Area - No Frame Offset
        ix, iy, iw, ih = x0, y0, w_mm, h_mm
        # Dashed Outline for context
        svg_list.append((z_outer, f'<rect x="{x0}" y="{y0}" width="{w_mm}" height="{h_mm}" fill="none" stroke="#ddd" stroke-dasharray="4" />'))
    else:
        # Draw Frame (Dormant)
        ox, oy = x0 - th_outer, y0 - th_outer
        ow, oh = w_mm + (th_outer*2), h_mm + (th_outer*2)
        
        svg_list.append((z_outer, f'<rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" fill="white" stroke="#999" stroke-width="1" />'))
        svg_list.append((z_outer, f'<line x1="{ox}" y1="{oy}" x2="{x0}" y2="{y0}" stroke="#aaa" stroke-width="1" />'))
        svg_list.append((z_outer, f'<line x1="{ox+ow}" y1="{oy}" x2="{x0+w_mm}" y2="{y0}" stroke="#aaa" stroke-width="1" />'))
        svg_list.append((z_outer, f'<line x1="{ox}" y1="{oy+oh}" x2="{x0}" y2="{y0+h_mm}" stroke="#aaa" stroke-width="1" />'))
        svg_list.append((z_outer, f'<line x1="{ox+ow}" y1="{oy+oh}" x2="{x0+w_mm}" y2="{y0+h_mm}" stroke="#aaa" stroke-width="1" />'))

        # Inner Frame
        col_stroke = "#AAA"
        svg_list.append((z_frame, f'<rect x="{x0}" y="{y0}" width="{w_mm}" height="{h_mm}" fill="white" stroke="{col_stroke}" stroke-width="2" />'))
        
        # Calculate Glass Position (Inside Frame)
        ix, iy = x0 + th_inner, y0 + th_inner
        iw, ih = w_mm - (th_inner*2), h_mm - (th_inner*2)
        
        svg_list.append((z_frame, f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" fill="none" stroke="#555" stroke-width="1" />'))
        svg_list.append((z_frame, f'<line x1="{x0}" y1="{y0}" x2="{ix}" y2="{iy}" stroke="{col_stroke}" stroke-width="1" />'))
        svg_list.append((z_frame, f'<line x1="{x0+w_mm}" y1="{y0}" x2="{ix+iw}" y2="{iy}" stroke="{col_stroke}" stroke-width="1" />'))
        svg_list.append((z_frame, f'<line x1="{x0}" y1="{y0+h_mm}" x2="{ix}" y2="{iy+ih}" stroke="{col_stroke}" stroke-width="1" />'))
        svg_list.append((z_frame, f'<line x1="{x0+w_mm}" y1="{y0+h_mm}" x2="{ix+iw}" y2="{iy+ih}" stroke="{col_stroke}" stroke-width="1" />'))

    # 4. Glass & Shapes
    g_fill = "#d6eaff" if s.get('vit_type_mode') != "Panneau" else "#eeeeee"
    shape = s.get('vit_shape', 'Rectangulaire')
    path_d = ""
    
    # Center Point for Dimension Orientation (Avoid Point)
    center_pt = (ix + iw/2, iy + ih/2)
    
    if shape == "Rectangulaire":
        path_d = f"M {ix},{iy} h {iw} v {ih} h -{iw} z"
        # RESTORED: No explicit Blue Dims here. We rely on the Global Frame dims (Black) at the end.
        
    elif "Forme A1" in shape:
        h1, h2 = s.get('vit_sh_h1', ih), s.get('vit_sh_h2', ih)
        y_tl, y_tr = (iy + ih) - h1, (iy + ih) - h2
        path_d = f"M {ix},{iy+ih} L {ix+iw},{iy+ih} L {ix+iw},{y_tr} L {ix},{y_tl} z"
        svg_list.append((z_dim, draw_dim(ix, iy+ih, ix, y_tl, h1, 80, "red", "H1=", avoid_point=center_pt)))
        svg_list.append((z_dim, draw_dim(ix+iw, iy+ih, ix+iw, y_tr, h2, 80, "red", "H2=", avoid_point=center_pt)))
        
    elif "Forme A2" in shape: # Pan Coupé
        lx, ly = s.get('vit_sh_lc', 200), s.get('vit_sh_hc', 200)
        path_d = f"M {ix},{iy} L {ix+iw-lx},{iy} L {ix+iw},{iy+ly} L {ix+iw},{iy+ih} L {ix},{iy+ih} z"
        svg_list.append((z_dim, draw_dim(ix+iw-lx, iy, ix+iw, iy, lx, 80, "red", "Lx=", avoid_point=center_pt)))
        svg_list.append((z_dim, draw_dim(ix+iw, iy, ix+iw, iy+ly, ly, 80, "red", "Ly=", avoid_point=center_pt)))
        
    elif "Forme B" in shape:
        h1, h2 = s.get('vit_sh_h1', ih), s.get('vit_sh_h2', ih)
        h3 = s.get('vit_sh_h3', ih)
        l1 = s.get('vit_sh_l1', iw/2)
        l2 = s.get('vit_sh_l2', 0)
        
        y_l, y_r = (iy + ih) - h1, (iy + ih) - h2
        y_peak = (iy + ih) - h3
        
        path_d = f"M {ix},{iy+ih} L {ix+iw},{iy+ih} L {ix+iw},{y_r} L {ix+l1+l2},{y_peak} L {ix+l1},{y_peak} L {ix},{y_l} z"
        
        svg_list.append((z_dim, draw_dim(ix, iy+ih, ix, y_l, h1, 80, "red", "H1=", avoid_point=center_pt)))
        svg_list.append((z_dim, draw_dim(ix+iw, iy+ih, ix+iw, y_r, h2, 80, "red", "H2=", avoid_point=center_pt)))
        svg_list.append((z_dim, draw_dim(ix+l1, iy+ih, ix+l1, y_peak, h3, -20, "red", "H3=", avoid_point=None))) 
        svg_list.append((z_dim, draw_dim(ix, iy+ih, ix+l1, iy+ih, l1, 120, "red", "L1=", avoid_point=center_pt))) 
        if l2 > 0:
             svg_list.append((z_dim, draw_dim(ix+l1, iy+ih, ix+l1+l2, iy+ih, l2, 120, "red", "L2=", avoid_point=center_pt)))

    elif "Forme C" in shape:
        fleche = s.get('vit_sh_fleche', 0)
        path_d = f"M {ix},{iy+ih} L {ix+iw},{iy+ih} L {ix+iw},{iy+fleche} Q {ix+(iw/2)},{iy} {ix},{iy+fleche} z"
        svg_list.append((z_dim, draw_dim(ix+iw/2, iy, ix+iw/2, iy+fleche, fleche, -40, "red", "F=")))
        
    elif "Forme D" in shape:
        rx, ry = iw / 2, ih / 2
        cx, cy = ix + rx, iy + ry
        path_d = f"M {cx-rx},{cy} a {rx},{ry} 0 1,0 {2*rx},0 a {rx},{ry} 0 1,0 -{2*rx},0"
        
    else: # Default
        path_d = f"M {ix},{iy} h {iw} v {ih} h -{iw} z"

    svg_list.append((z_glass, f'<path d="{path_d}" fill="{g_fill}" stroke="#888" stroke-width="2" />'))

    # 5. Machining (Usinage)
    if s.get('vit_usi_enable'):
        # Trous
        nb_t = s.get('vit_nb_trous', 0)
        for i in range(nb_t):
             tx = s.get(f"v_t_x_{i}", 0)
             ty = s.get(f"v_t_y_{i}", 0)
             td = s.get(f"v_t_d_{i}", 10)
             ref = s.get(f"v_t_ref_{i}", "1")
             ref = str(ref) # Ensure string
             
             # Calculate Absolute Coords & Dimensions
             # Default 2 (Top Left)
             cx, cy = ix + tx, iy + ty
             
             if "1" in ref: # Bas Gauche
                 cx = ix + tx
                 cy = (iy + ih) - ty
                 # Dim X (Bottom)
                 add_smart_dim("bottom", tx, ix, iy+ih, cx, iy+ih, "orange", "X", None)
                 # Dim Y (Left)
                 add_smart_dim("left", ty, ix, iy+ih, ix, cy, "orange", "Y", None)
                 
             elif "3" in ref: # Haut Droite
                 cx = (ix + iw) - tx
                 cy = iy + ty
                 # Dim X (Top)
                 add_smart_dim("top", tx, ix+iw, iy, cx, iy, "orange", "X", None)
                 # Dim Y (Right)
                 add_smart_dim("right", ty, ix+iw, iy, ix+iw, cy, "orange", "Y", None)
                 
             elif "4" in ref: # Bas Droite
                 cx = (ix + iw) - tx
                 cy = (iy + ih) - ty
                 # Dim X (Bottom)
                 add_smart_dim("bottom", tx, ix+iw, iy+ih, cx, iy+ih, "orange", "X", None)
                 # Dim Y (Right)
                 add_smart_dim("right", ty, ix+iw, iy+ih, ix+iw, cy, "orange", "Y", None)
                 
             else: # 2 or Default (Haut Gauche)
                 cx = ix + tx
                 cy = iy + ty
                 # Dim X (Top)
                 add_smart_dim("top", tx, ix, iy, cx, iy, "orange", "X", None)
                 # Dim Y (Left)
                 add_smart_dim("left", ty, ix, iy, ix, cy, "orange", "Y", None)

             svg_list.append((z_pb, f'<circle cx="{cx}" cy="{cy}" r="{td/2}" fill="white" stroke="red" stroke-width="1" />'))
             # V16 Polish: Label Outside & Bigger (Font 20)
             svg_list.append((z_pb, f'<text x="{cx}" y="{cy - (td/2) - 15}" font-size="{font_dim}" font-weight="bold" fill="red" text-anchor="middle">Ø{td}</text>'))
        
        # Encoches
        nb_e = s.get('vit_nb_enc', 0)
        for i in range(nb_e):
             ex = s.get(f"v_e_x_{i}", 0)
             ey = s.get(f"v_e_y_{i}", 0)
             ew = s.get(f"v_e_w_{i}", 50)
             eh = s.get(f"v_e_h_{i}", 50)
             ref = s.get(f"v_e_ref_{i}", "1")
             ref = str(ref)

             # Calculate Absolute Coords (Top Left of Notch)
             nx, ny = ix + ex, iy + ey # Default
             
             if "1" in ref: # Bas Gauche (X from Left, Y from Bottom)
                 nx = ix + ex
                 ny = (iy + ih) - ey - eh
                 # Dim X (Bottom)
                 add_smart_dim("bottom", ex, ix, iy+ih, nx, iy+ih, "purple", "X", None)
                 add_smart_dim("bottom", ew, nx, iy+ih, nx+ew, iy+ih, "purple", "L", None)
                 # Dim Y (Left) - Target LEFT edge
                 add_smart_dim("left", ey, ix, iy+ih, ix, iy+ih-ey, "purple", "Y", None)
                 add_smart_dim("left", eh, ix, iy+ih-ey, ix, ny, "purple", "H", None)

             elif "3" in ref: # Haut Droite
                 nx = (ix + iw) - ex - ew
                 ny = iy + ey
                 # Dim X (Top)
                 add_smart_dim("top", ex, ix+iw, iy, ix+iw-ex, iy, "purple", "X", None)
                 add_smart_dim("top", ew, ix+iw-ex, iy, nx, iy, "purple", "L", None)
                 # Dim Y (Right)
                 add_smart_dim("right", ey, ix+iw, iy, ix+iw, ny, "purple", "Y", None)
                 add_smart_dim("right", eh, ix+iw, ny, ix+iw, ny+eh, "purple", "H", None)
                 
             elif "4" in ref: # Bas Droite
                 nx = (ix + iw) - ex - ew
                 ny = (iy + ih) - ey - eh
                 # Dim X (Bottom)
                 add_smart_dim("bottom", ex, ix+iw, iy+ih, ix+iw-ex, iy+ih, "purple", "X", None)
                 add_smart_dim("bottom", ew, ix+iw-ex, iy+ih, nx, iy+ih, "purple", "L", None)
                 # Dim Y (Right)
                 add_smart_dim("right", ey, ix+iw, iy+ih, ix+iw, iy+ih-ey, "purple", "Y", None)
                 add_smart_dim("right", eh, ix+iw, iy+ih-ey, ix+iw, ny, "purple", "H", None)
             
             else: # 2 (Haut Gauche)
                 nx = ix + ex
                 ny = iy + ey
                 # Dim X (Top)
                 add_smart_dim("top", ex, ix, iy, nx, iy, "purple", "X", None)
                 add_smart_dim("top", ew, nx, iy, nx+ew, iy, "purple", "L", None)
                 # Dim Y (Left)
                 add_smart_dim("left", ey, ix, iy, ix, ny, "purple", "Y", None)
                 add_smart_dim("left", eh, ix, ny, ix, ny+eh, "purple", "H", None)

             # V16 Polish: White Fill (Removed Glass)
             svg_list.append((z_pb, f'<rect x="{nx}" y="{ny}" width="{ew}" height="{eh}" fill="white" stroke="red" stroke-width="1" stroke-dasharray="4" />'))

        # Mickey 101 (With Side Logic)
        if s.get('vit_mickey_101'):
            mickey_w, mickey_h = 165, 46
            side = s.get('vit_mickey_side', 'Gauche')
            
            # Position Logic
            if side == "Gauche":
                 p_start = ix # Flush Left
                 p_end = ix + mickey_w # Extend Inwards
                 mx = ix + 65 # Axis
            else: # Droite
                 p_start = ix + iw - mickey_w # Flush Right
                 p_end = ix + iw
                 mx = ix + iw - 65 # Axis
            
            # Draw Function for Notch
            def draw_mickey(my, is_top):
                 sign = 1 if is_top else -1
                 
                 # Absolute Path to fix "Diagonal Cut" Bug
                 # Defined by 4 points: Start(Edge), Deep(Inside), End(Deep), End(Edge)
                 y_edge = my
                 y_deep = my + (sign * mickey_h)
                 
                 d_path = f"M {p_start},{y_edge} L {p_start},{y_deep} L {p_end},{y_deep} L {p_end},{y_edge} Z"

                 # Cutout (White with Red Border)
                 svg_list.append((z_pb, f'<path d="{d_path}" fill="white" stroke="red" stroke-width="2" />'))
                 
                 # Holes Layout (Symmetric 35mm from ends)
                 x_h1 = p_start + 35
                 x_h2 = p_start + 130 # 165 - 35
                 
                 # Axis X (Carré - 65mm from Edge)
                 if side == "Gauche":
                    x_axis = ix + 65
                 else:
                    x_axis = (ix + iw) - 65

                 hy = my + (sign * mickey_h * 0.5)
                 
                 # Draw Holes (Circles + Crosshair)
                 for hx in [x_h1, x_h2]:
                     svg_list.append((z_pb, f'<circle cx="{hx}" cy="{hy}" r="5" fill="white" stroke="red" stroke-width="1.5" />'))
                     # Crosshair
                     svg_list.append((z_pb, f'<line x1="{hx-3}" y1="{hy}" x2="{hx+3}" y2="{hy}" stroke="red" stroke-width="1" />'))
                     svg_list.append((z_pb, f'<line x1="{hx}" y1="{hy-3}" x2="{hx}" y2="{hy+3}" stroke="red" stroke-width="1" />'))

                 # Axe Carré (Vertical Center Line) - Extended
                 ay_out = my - (sign * 40)
                 ay_in = my + (sign * (mickey_h + 20))
                 svg_list.append((z_pb, f'<line x1="{x_axis}" y1="{ay_out}" x2="{x_axis}" y2="{ay_in}" stroke="red" stroke-width="1.5" stroke-dasharray="10,4,2,4" />'))
                 
                 # DIMENSIONS (Strictly OUTSIDE Glass & Spaced Out)
                 # Rule: Smallest First (Closest), Largest Last (Furthest)
                 
                 # 1. Axis Line (Smart Offset)
                 # 1. Axis Line (Smart Buckets)
                 if side == "Gauche":
                     # From ix to mx (Axis)
                     add_smart_dim("bottom", 65, ix, my-sign*20, mx, my-sign*20, "red", "Axe carré = ", center_pt)
                 else:
                     add_smart_dim("bottom", 65, ix+iw, my-sign*20, mx, my-sign*20, "red", "Axe carré = ", center_pt)
                 
                 # 2. Label Encoche (Fixed at 75 - Outside Notch)
                 svg_list.append((z_pb, f'<text x="{mx}" y="{my + sign*75}" font-size="20" font-weight="bold" fill="red" text-anchor="middle" dominant-baseline="middle" paint-order="stroke" stroke="white" stroke-width="3">Enc. 101</text>'))

                 # 3. Width Line (Smart Buckets)
                 add_smart_dim("bottom", mickey_w, p_start, my-sign*20, p_end, my-sign*20, "red", "", center_pt)

            # Draw Top AND Bottom
            draw_mickey(iy, True)
            draw_mickey(iy + ih, False)
             
    # 5. Petits Bois
    if s.get('vit_pb_enable'):
        nb_h = s.get('vit_pb_hor', 0)
        nb_v = s.get('vit_pb_vert', 0)
        thick = s.get('vit_pb_thick', 26)
        
        if nb_h > 0:
            step_h = ih / (nb_h + 1)
            for i in range(nb_h):
                py = iy + step_h * (i + 1) - (thick/2)
                svg_list.append((z_pb, f'<rect x="{ix}" y="{py}" width="{iw}" height="{thick}" fill="white" stroke="#ccc" />'))
                if i == 0:
                     h_gap = step_h
                     # Anchor to Inner Right but push OUTSIDE Outer Frame
                     dx_ref = x0 + w_mm + th_outer
                     # Dynamic Offset and Font Size (V79: Increase offset to be clearly outside)
                     draw_dimension_line(svg_list, dx_ref, iy, dx_ref, iy + h_gap, int(h_gap), "", font_dim * 4.0, "V", font_dim, z_dim)



        if nb_v > 0:
            step_v = iw / (nb_v + 1)
            for i in range(nb_v):
                px = ix + step_v * (i + 1) - (thick/2)
                svg_list.append((z_pb, f'<rect x="{px}" y="{iy}" width="{thick}" height="{ih}" fill="white" stroke="#ccc" />'))
                if i == 0:
                     w_gap = step_v
                     # Anchor to Inner Top but push OUTSIDE Outer Frame
                     draw_dimension_line(svg_list, x0+th_inner, y0-th_outer, x0+th_inner+w_gap, y0-th_outer, int(w_gap), "", -(font_dim * 2.5), "H", font_dim, z_dim)


    # 6. Global Dimensions (Black/Standard) - RESTORED
    # Axis Calculations - If glass_only, axis is just glass edge
    if glass_only:
        axis_left = x0
        axis_right = x0 + w_mm
        axis_top = y0
        axis_bottom = y0 + h_mm
    else:
        axis_left = x0 + (th_inner/2)
        axis_right = (x0 + w_mm) - (th_inner/2)
        axis_top = y0 + (th_inner/2)
        axis_bottom = (y0 + h_mm) - (th_inner/2)
    
    # Width (Global)
    # Width (Global)
    draw_dimension_line(svg_list, 
        axis_left, axis_bottom, 
        axis_right, axis_bottom, 
        int(w_mm), 
        "", font_dim * 3.5, "H", font_dim, z_dim, leader_fixed_start=axis_bottom)
    
    # Height (Global)
    draw_dimension_line(svg_list, 
        axis_left, axis_top, 
        axis_left, axis_bottom, 
        int(h_mm), 
        "", font_dim * 3.5, "V", font_dim, z_dim, leader_fixed_start=axis_left)
    
    # NO Cleanup of these dims. User wants them.

    # 6.5 Render Smart Dims
    # Process Buckets
    
    # Config: Base distance + Step
    # Config: Base distance + Step
    # Config: Base distance + Step
    # DYNAMIC SPACING
    base_dist = font_dim * 1.5
    step_dist = font_dim * 1.5
    
    # Helper to process a bucket
    def render_bucket(edge_name, bucket_list, sign_direction):
        if not bucket_list: return
        
        # 1. Unique Values & Sort
        # Force Float conversion for correct numerical sorting
        try:
            vals = []
            for b in bucket_list:
                try:
                    vals.append(float(b['val']))
                except:
                    pass
            unique_vals = sorted(list(set(vals)))
        except:
             unique_vals = sorted(list(set([b['val'] for b in bucket_list])))
        
        # 2. Assign Rank Map
        val_rank = {v: i for i, v in enumerate(unique_vals)}
        
        # 3. Draw
        for item in bucket_list:
            v_orig = item['val']
            # Try to match float key
            try:
                v = float(v_orig)
            except:
                v = v_orig
            
            rank = val_rank.get(v, len(unique_vals)) # Default to end if missing
            pts = item['pts']
            
            # NORMALIZE VECTORS for Consistent Normals
            # Horizontal: Left -> Right (Normal Down)
            # Vertical: Bottom -> Top (Normal Right)
            x1, y1, x2, y2 = pts
            
            # Check Vertical (approx equal X)
            if abs(x1 - x2) < 0.1:
                # Force Bottom -> Top (y1 > y2)
                if y1 < y2:
                    x1, y1, x2, y2 = x2, y2, x1, y1
            else:
                # Force Left -> Right (x1 < x2)
                if x1 > x2:
                    x1, y1, x2, y2 = x2, y2, x1, y1
            
            # Calculate Offset
            scalar_off = (base_dist + (rank * step_dist))
            final_off = scalar_off * sign_direction
            
            svg_list.append((z_dim, draw_dim(x1, y1, x2, y2, v, final_off, item['color'], item['label'], item['avoid'])))

    # Multipliers for Standardized Vectors [H: L->R (Normal Down)] [V: B->T (Normal Right)]
    render_bucket("bottom", dim_buckets["bottom"], 1)   # Down (Out)
    render_bucket("top", dim_buckets["top"], -1)        # Up (Out)
    render_bucket("left", dim_buckets["left"], -1)      # Left (Out)
    render_bucket("right", dim_buckets["right"], 1)     # Right (Out)

    # 7. Render
    svg_list.sort(key=lambda x: x[0])
    content = "".join([item[1] for item in svg_list])
    
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb_x} {vb_y} {vb_w} {vb_h}" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" style="background-color:white;">{content}</svg>'



def render_html_vitrage(s, svg_string, logo_b64):
    """HTML Export for Vitrage"""
    obs_html = ""
    if s.get('vit_obs'):
        obs_html = f"""
            <div class="section-block">
                <h3>Observations</h3>
                <div class="panel" style="white-space: pre-wrap;">{s.get('vit_obs')}</div>
            </div>
        """
    
    # V13 ROBUSTNESS: Unified Logic with Menuiserie
    # Use local helper to reconstruct string if components exist, else "-"
    def reconstruct_vit_string(d):
        res = d.get('vitrage_resume', '')
        # Force calc if empty, None, or stale
        if not res or res == "None" or "None" in str(res):
             vt_mode = d.get('vit_type_mode', 'Double Vitrage')
             
             if vt_mode == "Double Vitrage":
                 try:
                     ep_e = str(d.get('vit_ep_ext','4')).replace(' mm', '')
                     ep_i = str(d.get('vit_ep_int','4')).replace(' mm', '')
                     ep_a = str(d.get('vit_ep_air','16')).replace(' mm', '')
                     
                     c_e = str(d.get('vit_couche_ext','Aucune'))
                     c_i = str(d.get('vit_couche_int','Aucune'))
                     
                     sf_e = "FE" if "FE" in c_e else (" CS" if "Contrôle" in c_e else "")
                     sf_i = "FE" if "FE" in c_i else ""
                     
                     ty_e = str(d.get('vit_type_ext','Clair'))
                     st_e = f" {ty_e}" if ty_e != "Clair" else ""
                     
                     ty_i = str(d.get('vit_type_int','Clair'))
                     st_i = f" {ty_i}" if ty_i != "Clair" else ""
                     
                     gaz = str(d.get('vit_gaz','Argon')).upper()
                     inter = str(d.get('vit_intercalaire','Alu')).upper()
                     
                     res = f"Vit. {ep_e}{st_e}{sf_e} / {ep_a} / {ep_i}{st_i}{sf_i} - {inter} + GAZ {gaz}"
                 except Exception as e:
                     res = f"Erreur Calc ({str(e)})"
                     
             elif vt_mode == "Simple Vitrage":
                 ep_e = str(d.get('vit_ep_ext','4')).replace(' mm', '')
                 ty_e = str(d.get('vit_type_ext','Clair'))
                 res = f"Simple {ep_e} {ty_e}"
             else:
                 res = "Panneau Plein"
                 
        return str(res)

    vit_resume = reconstruct_vit_string(s)
    
    # V75 ROBUSTNESS: Use the same styles as Menuiserie
    css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
        body { font-family: 'Roboto', sans-serif; -webkit-print-color-adjust: exact; padding: 0; margin: 0; background-color: #fff; color: #333; }
        
        .page-container { 
            max-width: 210mm; 
            margin: 0 auto; 
            padding: 20px;
        }

        /* HEADER */
        .header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; border-bottom: 3px solid #2c3e50; padding-bottom: 15px; }
        .header-left img { max-height: 70px; width: auto; }
        .header-left .subtitle { color: #3498db; font-size: 14px; margin-top: 5px; font-weight: 400; }
        
        .header-right { text-align: right; padding-right: 5px; }
        .header-right .label { font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 2px; }
        .header-right .ref { font-size: 24px; font-weight: bold; color: #000; margin-bottom: 2px; line-height: 1; }
        .header-right .date { font-size: 11px; color: #666; }

        /* STACKED LAYOUT (Sections) */
        .section-block { margin-bottom: 25px; break-inside: avoid; }
        
        /* HEADINGS */
        h3 { 
            font-size: 15px; color: #2c3e50; margin: 0 0 12px 0; 
            border-left: 5px solid #3498db; padding-left: 10px; 
            line-height: 1.2; text-transform: uppercase; letter-spacing: 0.5px;
        }
        
        /* PANELS */
        .panel { background: #fdfdfd; padding: 15px; border: 1px solid #eee; border-radius: 4px; font-size: 11px; }
        .panel-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px dotted #ccc; }
        .panel-row:last-child { border-bottom: none; }
        .panel-row .lbl { font-weight: bold; color: #444; width: 40%; }
        .panel-row .val { font-weight: normal; color: #000; text-align: right; width: 60%; }
        
        /* ZONES TABLE (Full Width) */
        table { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 5px; }
        th { background: #cfd8dc; color: #2c3e50; padding: 6px; text-align: left; text-transform: uppercase; font-size: 10px; }
        td { border-bottom: 1px solid #eee; padding: 8px 12px; color: #333; line-height: 1.4; }
        tr:nth-child(even) { background-color: #f9f9f9; }

        /* BOTTOM SECTION (PLAN) */
        .visual-box {
            border: none; margin-top: 20px;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            position: relative;
            width: 100%; height: 600px; /* Reduced height for Vitrage to fit page */
            page-break-inside: avoid;
        }
        .visual-box svg { height: 100%; width: auto; max-width: 98%; }
        
        .footer { 
            position: fixed; bottom: 10mm; left: 0; right: 0;
            font-size: 9px; color: #999; text-align: center; 
        }

        @media print {
            @page { size: A4; margin: 12mm; }
            body { padding: 0; background: white; -webkit-print-color-adjust: exact; }
            .page-container { margin: 0; padding: 0; box-shadow: none; max-width: none; width: 100%; }
            .no-print { display: none; }
            h3 { break-after: avoid; }
        }
    </style>
    """
    
    logo_html = f'<img src="data:image/png;base64,{logo_b64}">' if logo_b64 else ""

    import datetime

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{css}</head>
    <body>
        <div class="page-container">
            <!-- HEADER -->
            <div class="header">
                <div class="header-left">
                    {logo_html}
                    <div class="subtitle">Fiche Vitrage</div>
                </div>
                <div class="header-right">
                    <div class="label">RÉFÉRENCE</div>
                    <div class="ref">{s.get('vit_ref', 'V-??')}</div>
                    <div class="date">{datetime.datetime.now().strftime('%d/%m/%Y')}</div>
                </div>
            </div>
            
            <div class="section-block">
                <h3>Caractéristiques</h3>
                <div class="panel">
                    <div class="panel-row"><span class="lbl">Quantité</span> <span class="val">{s.get('vit_qte', 1)}</span></div>
                    <div class="panel-row"><span class="lbl">Matériau</span> <span class="val">{s.get('vit_mat')}</span></div>
                    <div class="panel-row"><span class="lbl">Type Châssis</span> <span class="val">{s.get('vit_type_chassis')}</span></div>
                    <div class="panel-row"><span class="lbl">Dimensions</span> <span class="val">{s.get('vit_width')} x {s.get('vit_height')} mm</span></div>
                    <div class="panel-row"><span class="lbl">H. Bas</span> <span class="val">{s.get('vit_h_bas', 0)} mm</span></div>
                    <div class="panel-row"><span class="lbl">Type Côtes</span> <span class="val">{s.get('vit_dim_type')}</span></div>
                    <div class="panel-row"><span class="lbl">Verre</span> <span class="val">{vit_resume}</span></div>
                    <div class="panel-row"><span class="lbl">H. Bas Verre</span> <span class="val">{s.get('vit_h_bas')} mm</span></div>
                </div>
            </div>
            
            <div class="section-block">
                <h3>Plan Technique</h3>
                <div class="visual-box">
                    {svg_string}
                </div>
            </div>
            
            {obs_html}
            
            <div class="footer">
                Document généré automatiquement - Miroiterie Yerroise
            </div>
        </div>
    </body>
    </html>
    """

    return html


# V73: BASE DE DONNEES DES ANNEXES
ANNEXES_DB = {
    "Général": [
        "Glossaire FPEE.pdf",
        "2 Multiproduits FPEE - 2024.pdf",
        # "FPEE - Portails.pdf", # Supprimé car trop gros (>100Mo) et non uploadé
        "Doc Tech Depose Totale (FPEE).pdf",
        "FPEE - ALU _ PVC Portes Tertiaires_.pdf"
    ],
    "PVC": {
        "Catalogues": [
            "FPEE - PVC 70 - 76 Fenêtres et Portes Fenêtres.pdf",
            "FPEE - PVC NOVELIA RFP Fenêtres et Portes Fenêtres.pdf",
            "FPEE - PVC RFP Fenêtres et Portes Fenêtres.pdf"
        ],
        "Fiche technique": [
            "Doc tech PVC-A05 (FPEE)- 2023.pdf",
            "Doc tech BB-A03 (70mm).pdf"
        ],
        "Mise en oeuvre": [
            "Mise en oeuvre des menuiseries PVC.pdf"
        ]
    },
    "ALU": {
        "Catalogues": [
            "FPEE - ALUMINIUM Portes et Fenêtres.pdf",
            "FPEE - Portes.pdf"
        ],
        "Fiche techniques": [
            "Doc Tech Sensation 2023-A01 (FPEE).pdf"
        ],
        "Mise en oeuvre": [
            "Mise en oeuvre des menuiseries en Aluminium.pdf"
        ]
    }
}

def render_annexes():
    """Affiche la section Annexes en bas de page (Menuiserie uniquement)."""
    # Only for Menuiserie
    if st.session_state.get('mode_module', 'Menuiserie') != 'Menuiserie':
        return

    st.markdown("---")
    with st.expander("📂 Annexes (Documentation)", expanded=False):
        # Determine Material (Default PVC)
        mat = st.session_state.get('mat_type', 'PVC') 
        



        
        def render_doc_item(file_name, key_suffix, label=None):
            """Helper to render a row for a document"""
            p = os.path.join(current_dir, "assets", file_name)
            
            if not os.path.exists(p):
                 # DEBUG: List assets content to diagnose if file is really missing or path issue
                 try:
                     assets_path = os.path.join(current_dir, "assets")
                     if os.path.exists(assets_path):
                        available = os.listdir(assets_path)
                        # Truncate list if too long
                        if len(available) > 10: available = available[:10] + ["..."]
                        st.error(f"Fichier introuvable: {file_name} (Contenu du dossier assets: {available})")
                     else:
                        st.error(f"Dossier 'assets' introuvable au chemin : {assets_path}")
                 except Exception as e:
                     st.error(f"Erreur de lecture du dossier assets: {e}")
                 return

            # Layout: Button Download | Button View | Filename
            c_view, c_dl = st.columns([1, 1])
            
            clean_name = label if label else file_name.replace('.pdf','').replace('FPEE - ', '')
            
            # View Button Toggle Logic
            view_key = f"view_{key_suffix}_{file_name}"
            
            # We use a button to toggle session state for viewing
            # Note: We can't easily rely on st.button state across reruns for a "toggle" 
            # without session state management, but here standard button + session state is robust.
            if view_key not in st.session_state: st.session_state[view_key] = False
            
            # Row Container
            with st.container():
                # We want a row look. Columns for buttons.
                # Adjusted for tighter spacing: 5% for buttons, rest for text
                r1, r2, r3 = st.columns([0.06, 0.06, 0.88])
                
                with r1:
                    with open(p, "rb") as pdf_file:
                        st.download_button("📥", pdf_file, file_name=file_name, key=f"dl_{key_suffix}_{file_name}", help="Télécharger le PDF")
                
                with r2:
                    # Toggle View
                    label_icon = "👁️" if not st.session_state[view_key] else "🔒"
                    if st.button(label_icon, key=f"btn_view_{key_suffix}_{file_name}", help="Visualiser / Fermer"):
                        st.session_state[view_key] = not st.session_state[view_key]
                        st.rerun()
                
                with r3:
                     # Add small vertical padding to align with buttons
                     st.markdown(f"<div style='margin-top: 5px;'><b>{clean_name}</b></div>", unsafe_allow_html=True)
            
            # Viewer Container (If visible)
            if st.session_state[view_key]:
                with st.spinner(f"Chargement de {clean_name}..."):
                     try:
                         with open(p, "rb") as f:
                             base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                         
                         # V73: Revert to simple iframe as it worked locally.
                         # Height set to 1200px.
                         # JS Blob solution for Mobile/Secure Browsers
                         import streamlit.components.v1 as components
                         
                         # Ensure one-line base64
                         b64_clean = base64_pdf.replace('\n', '')
                         
                         btn_html = f'''
                         <!DOCTYPE html>
                         <html>
                         <head>
                         <style>
                             body {{ margin: 0; padding: 0; }}
                             button {{
                                 display: block;
                                 width: 100%;
                                 padding: 12px 0;
                                 background-color: #ff4b4b;
                                 color: white;
                                 border: none;
                                 cursor: pointer;
                                 text-align: center;
                                 border-radius: 8px;
                                 font-weight: bold;
                                 font-family: sans-serif;
                                 font-size: 16px;
                                 box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                             }}
                             button:hover {{ background-color: #ff2b2b; }}
                             button:active {{ transform: translateY(1px); }}
                         </style>
                         </head>
                         <body>
                             <button onclick="openPdf()">📱 OUVRIR LE PDF EN PLEIN ÉCRAN</button>
                             <script>
                                function openPdf() {{
                                    const b64 = "{b64_clean}";
                                    const bin = atob(b64);
                                    const len = bin.length;
                                    const arr = new Uint8Array(len);
                                    for (let i = 0; i < len; i++) {{
                                        arr[i] = bin.charCodeAt(i);
                                    }}
                                    const blob = new Blob([arr], {{type: "application/pdf"}});
                                    const url = URL.createObjectURL(blob);
                                    window.open(url, "_blank");
                                }}
                             </script>
                         </body>
                         </html>
                         '''
                         components.html(btn_html, height=60)
                         
                         pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="1200" type="application/pdf"></iframe>'
                         st.markdown(pdf_display, unsafe_allow_html=True)
                     except Exception as e:
                         st.error(f"Erreur d'affichage: {e}")

        # 1. Général
        with st.expander("1. Général", expanded=False):
            for f in ANNEXES_DB["Général"]:
                render_doc_item(f, "gen")
        
        # Get Material Data
        mat_data = ANNEXES_DB.get(mat, {})
        
        # 2. Catalogue Commercial
        with st.expander("2. Catalogue commercial", expanded=False):
             for f in mat_data.get("Catalogues", []):
                 render_doc_item(f, "cat")

        # 3. Fiche technique
        with st.expander("3. Fiche technique", expanded=False):
             ft_files = mat_data.get("Fiche technique", []) or mat_data.get("Fiche techniques", [])
             for f in ft_files:
                 render_doc_item(f, "ft")

        # 4. Mise en oeuvre
        with st.expander("4. Mise en oeuvre", expanded=False):
             for f in mat_data.get("Mise en oeuvre", []):
                 render_doc_item(f, "meo")

# --- MAIN LAYOUT V77 (Logo in Left Col, Visualisation Top Right) ---

# 1. Main Columns (Created FIRST to allow Visualization to start at top)
c_config, c_preview = st.columns([1, 1.4])

hab_config = None
current_mode = st.session_state.get('mode_module', 'Menuiserie')

# --- COLUMN LEFT: CONFIGURATION + LOGO + NAV ---
with c_config:
    # 1. Logo & Branding
    if 'LOGO_B64' in globals():
        try:
             # Robust Logic for Main UI Logo
             try:
                 decoded = base64.b64decode(LOGO_B64, validate=True)
             except:
                 b64 = LOGO_B64
                 b64 += "=" * ((4 - len(b64) % 4) % 4)
                 decoded = base64.b64decode(b64)
             
             st.image(decoded, width=300)
        except Exception as e:
             pass
    else:
         st.warning("Logo variable not found.")

    st.write("") # Spacer

    # 2. Top Navigation & Project Management
    render_top_navigation()
    
    st.markdown("---")
    
    # BOUTON RESET (RESTAURÉ)
    if st.button("❌ Réinitialiser", use_container_width=True, help="Remettre à zéro le formulaire"):
        reset_config()
        st.rerun() # Force rerun to clear form immediately
        
    if current_mode == 'Menuiserie':
        st.markdown("### 🛠 Options Menuiserie")
        render_menuiserie_form()
    elif current_mode == 'Volet Roulant':
        st.markdown("### 🧱 Options Volet Roulant")
        vr_config = render_volet_form()
    elif current_mode == 'Vitrage':
        st.markdown("### 🪟 Options Vitrage")
        render_vitrage_form()
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
            # V76 FIX: Constrained Visualization Container
            style_container = 'width:100%; height:70vh; max-height:800px; border:1px solid #ddd; background:white; display:flex; align-items:center; justify-content:center; overflow:hidden;'
            svg_display = svg_output.replace('<svg ', '<svg width="100%" height="100%" preserveAspectRatio="xMidYMid meet" ')
            st.markdown(f'<div style="{style_container}">{svg_display}</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Erreur SVG: {e}")
            import traceback
            st.code(traceback.format_exc())

        # 2. RÉCAPITULATIF SOUS LE DESSIN
        st.markdown("### 📋 Fiche Technique")
        st.markdown("---")
        
        

        # Bouton Impression & Téléchargement
        c_print, c_dl_html = st.columns(2)
        
        # Generator HTML once
        try:
             html_print = render_html_menuiserie(st.session_state, svg_output, LOGO_B64 if 'LOGO_B64' in globals() else None)
        except Exception as e:
             html_print = f"Erreur génération: {e}"
             st.error(f"Erreur interne: {e}")

        with c_print:
            if st.button("🖨️ Impression", use_container_width=True):
                 try:
                     import json
                     # V73 FIX: Robust serialization to avoid JS syntax errors
                     html_json = json.dumps(html_print)
                     from streamlit.components.v1 import html
                     html(f"<script>var w=window.open();w.document.write({html_json});w.document.close();setTimeout(function(){{w.print();}}, 1000);</script>", height=0)
                 except Exception as e:
                     st.error(f"Erreur impression: {e}")
        
        with c_dl_html:
            st.download_button(
                "💾 Télécharger Fiche (.html)",
                html_print,
                file_name=f"Fiche_{st.session_state.get('ref_id', 'Menuiserie')}.html",
                mime="text/html",
                use_container_width=True
            )

        # PREPARE ZONES DATA
        s = st.session_state
        w_d = s.get('width_dorm', 0)
        h_d = s.get('height_dorm', 0)

        config_display = flatten_tree(st.session_state.get('zone_tree'), 0,0,w_d,h_d)
        sorted_zones = sorted(config_display, key=lambda z: z['id'])

        # --- SECTION 1: INFORMATIONS GLOBALES ---
        c1, c2 = st.columns(2)
        w_rec = w_d + (2 * s.get('fin_val', 0))
        h_bot_add = s.get('width_appui', 0) if s.get('is_appui_rap', False) else (s.get('fin_bot', 0) if not s.get('same_bot', False) else s.get('fin_val', 0))
        h_rec = h_d + s.get('fin_val', 0) + h_bot_add
        
        with c1:
            st.markdown(f"**Repère** : {s.get('ref_id', 'F1')}")
            st.markdown(f"**Quantité** : {s.get('qte_val', 1)}")
            st.markdown(f"**Projet** : {s.get('proj_type', 'Rénovation')}")
            st.markdown(f"**Matériaux** : {s.get('mat_type', 'PVC')}")
            st.markdown(f"**Pose** : {s.get('pose_type', '-')}")
            st.markdown(f"**Dormant** : {s.get('frame_thig', 70)} mm")
            ail_txt = f"{s.get('fin_val',0)}mm (H/G/D)" if s.get('fin_val',0) > 0 else "Sans"
            st.markdown(f"**Ailettes** : {ail_txt}")
            
        with c2:
             st.markdown(f"**Appui** : {'OUI' if s.get('is_appui_rap') else 'NON'}")
             st.markdown(f"**Couleur** : {s.get('col_in','-')} / {s.get('col_ex','-')}")
             st.markdown(f"**Côtes** : {s.get('dim_type', 'Tableau')}")
             st.markdown(f"**Dos Dormant** : {w_d} x {h_d} mm")
             st.markdown(f"**Recouvrement** : {w_rec} x {h_rec} mm")
             st.markdown(f"**Allège** : {s.get('h_allege', 0)} mm")
             st.markdown(f"**Volet R.** : {'OUI' if s.get('vr_enable') else 'NON'}")

        # Add Observations
        if s.get('men_obs'):
            st.markdown("---")
            st.markdown(f"**Observations** : {s.get('men_obs')}")

        st.markdown("---")
        
        # --- SECTION 2: DETAILS PAR ZONE ---
        st.markdown("#### Détails par Zone")
        
        for i, z in enumerate(sorted_zones):
             parts = []
             parts.append(f"**{z['label']}** : {int(z['w'])} x {int(z['h'])} mm")
             parts.append(f"Config : {z['type']}")
             
             nb_h = z['params'].get('traverses', 0)
             if nb_h > 0:
                 ep_t = z['params'].get('epaisseur_traverse', 20)
                 parts.append(f"Trav. {nb_h}H (Ep.{ep_t}mm)")
                 if nb_h == 1 and z['params'].get('traverses_v', 0) == 0:
                      parts.append(f"Remp. {z['params'].get('remp_haut')}/{z['params'].get('remp_bas')}")
             else:
                 nb_v = z['params'].get('traverses_v', 0)
                 if nb_v > 0:
                      parts.append(f"PB {nb_v}V")
             
             remp_g = z['params'].get('remplissage_global', 'Vitrage')
             if remp_g == "Vitrage":
                  v_str = str(z['params'].get('vitrage_resume', '-')).replace('\n', ' ')
                  parts.append(f"Vit. {v_str}")
             else:
                  parts.append(f"Panneau")
                  
             g_pos = z['params'].get('pos_grille', 'Aucune')
             if g_pos != "Aucune":
                  parts.append(f"VMC {g_pos}")

             st.markdown(" • ".join(parts))

    elif current_mode == 'Volet Roulant':
        # 1. PLAN TECHNIQUE VOLET
        try:
            svg_output = generate_svg_volet()
            # V76 FIX: Constrained Visualization Container
            style_container = 'width:100%; height:70vh; max-height:800px; border:1px solid #ddd; background:white; display:flex; align-items:center; justify-content:center; overflow:hidden;'
            svg_display = svg_output.replace('<svg ', '<svg width="100%" height="100%" preserveAspectRatio="xMidYMid meet" ')
            st.markdown(f'<div style="{style_container}">{svg_display}</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Erreur SVG Volet: {e}")
        
        # 2. IMPRESSION VOLET
        st.markdown("### 📋 Fiche Volet")
        st.markdown("---")
        
        # UI SUMMARY (Style Menuiserie)
        s = st.session_state
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown(f"**Repère** : {s.get('ref_id', 'VR-01')}")
            st.markdown(f"**Quantité** : {s.get('vr_qte', 1)}")
            st.markdown(f"**Dimensions** : {s.get('vr_width')} x {s.get('vr_height')} mm")
            st.markdown(f"**Type** : {s.get('vr_type')}")
            st.markdown(f"**Coffre** : {s.get('vr_col_coffre')}")
            st.markdown(f"**Coulisses** : {s.get('vr_col_coulisses')}")

        with c2:
            st.markdown(f"**Tablier** : {s.get('vr_col_tablier')}")
            st.markdown(f"**Lame Finale** : {s.get('vr_col_lame_fin')}")
            if s.get('vr_type') == 'Motorisé':
                st.markdown(f"**Moteur** : {s.get('vr_motor')} ({s.get('vr_power')})")
                st.markdown(f"**Commande** : {s.get('vr_proto')}")
                st.markdown(f"**Sortie** : {s.get('vr_cable_side')} / {s.get('vr_cable_len')}")
            else:
                st.markdown(f"**Manivelle** : {s.get('vr_crank_side')} / {s.get('vr_crank_len')}mm")
            
            # Add Solar info if applicable
            if s.get('vr_proto') == "IO SOLAIRE":
                 st.markdown("**Option** : SOLAIRE")

        # Add Observations
        if s.get('vr_obs'):
            st.markdown("---")
            st.markdown(f"**Observations** : {s.get('vr_obs')}")

        st.markdown("---")
        if st.button("🖨️ Impression Volet", use_container_width=True):
            html_print = render_html_volet(st.session_state, svg_output, LOGO_B64 if 'LOGO_B64' in globals() else None)
            from streamlit.components.v1 import html
            html(f"<script>var w=window.open();w.document.write(`{html_print}`);w.document.close();w.print();</script>", height=0)
            
    elif current_mode == 'Vitrage':
        # 1. VISUALISATION
        try:
            svg_output = generate_svg_vitrage()
            # V76 FIX: Constrained Visualization Container
            style_container = 'width:100%; height:70vh; max-height:800px; border:1px solid #ddd; background:white; display:flex; align-items:center; justify-content:center; overflow:hidden;'
            svg_display = svg_output.replace('<svg ', '<svg width="100%" height="100%" preserveAspectRatio="xMidYMid meet" ')
            st.markdown(f'<div style="{style_container}">{svg_display}</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Erreur SVG Vitrage: {e}")
        
        # 2. FICHE SUMMARY
        st.markdown("### 📋 Fiche Vitrage")
        st.markdown("---")
        
        s = st.session_state
        c1, c2 = st.columns(2)
        with c1:
             st.markdown(f"**Repère** : {s.get('vit_ref')}")
             st.markdown(f"**Quantité** : {s.get('vit_qte')}")
             st.markdown(f"**Dimensions** : {s.get('vit_width')} x {s.get('vit_height')} mm")
             st.markdown(f"**H. Bas** : {s.get('vit_h_bas')} mm")
             
        with c2:
             st.markdown(f"**Matériau** : {s.get('vit_mat')}")
             st.markdown(f"**Châssis** : {s.get('vit_type_chassis')}")
             # V13 UI FIX: Use Robust Reconstruction (Inline)
             res_ui = s.get('vitrage_resume', '')
             if not res_ui or "None" in str(res_ui):
                 # Quick Reconstruct
                 try:
                     vt_mode = s.get('vit_type_mode', 'Double Vitrage')
                     if vt_mode == "Double Vitrage":
                         ep_e = str(s.get('vit_ep_ext','4')).replace(' mm', '')
                         ep_i = str(s.get('vit_ep_int','4')).replace(' mm', '')
                         ep_a = str(s.get('vit_ep_air','16')).replace(' mm', '')
                         c_e, c_i = str(s.get('vit_couche_ext','Aucune')), str(s.get('vit_couche_int','Aucune'))
                         sf_e = "FE" if "FE" in c_e else (" CS" if "CS" in c_e else "")
                         sf_i = "FE" if "FE" in c_i else ""
                         ty_e = str(s.get('vit_type_ext','Clair'))
                         st_e = f" {ty_e}" if ty_e != "Clair" else ""
                         ty_i = str(s.get('vit_type_int','Clair'))
                         st_i = f" {ty_i}" if ty_i != "Clair" else ""
                         gaz = str(s.get('vit_gaz','Argon')).upper()

                         inter = str(s.get('vit_intercalaire','Alu')).upper()
                         res_ui = f"Vit. {ep_e}{st_e}{sf_e} / {ep_a} / {ep_i}{st_i}{sf_i} - {inter} + GAZ {gaz}"
                     elif vt_mode == "Simple Vitrage":
                         res_ui = f"Simple {s.get('vit_ep_ext','4')} {s.get('vit_type_ext','Clair')}"
                     else:
                         res_ui = "Panneau Plein"
                 except:
                     res_ui = s.get('vit_resume', '-') # Fallback
             
             st.markdown(f"**Verre** : {res_ui}")
             if s.get('vit_pb_enable'):
                 st.markdown(f"**Petits bois** : {s.get('vit_pb_hor')}H x {s.get('vit_pb_vert')}V")

        if s.get('vit_obs'):
            st.markdown("---")
            st.markdown(f"**Observations** : {s.get('vit_obs')}")
            
        st.markdown("---")
        if st.button("🖨️ Impression Vitrage", use_container_width=True):
            html_print = render_html_vitrage(st.session_state, svg_output, LOGO_B64 if 'LOGO_B64' in globals() else None)
            from streamlit.components.v1 import html
            html(f"<script>var w=window.open();w.document.write(`{html_print}`);w.document.close();w.print();</script>", height=0)

    else:
        # HABILLAGE PREVIEW
        if hab_config:
            render_habillage_main_ui(hab_config)
        else:
            st.info("Configuration Habillage non initialisée.")
            
# --- ANNEXES SECTION ---
render_annexes()



# END OF CODE V73.5 (VALIDATED)
