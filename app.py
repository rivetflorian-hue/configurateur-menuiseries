import streamlit as st
import math

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

# --- 1. FONCTIONS DE DESSIN ---

def draw_rect(svg, x, y, w, h, fill, stroke="black", sw=1, z_index=1):
    svg.append((z_index, f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" />'))

def draw_text(svg, x, y, text, font_size=12, fill="black", weight="normal", anchor="middle", z_index=10, rotation=0):
    transform = f'transform="rotate({rotation}, {x}, {y})"' if rotation != 0 else ""
    svg.append((z_index, f'<text x="{x}" y="{y}" font-family="Arial" font-size="{font_size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}" dominant-baseline="middle" {transform}>{text}</text>'))

def draw_dimension_line(svg_content, x1, y1, x2, y2, value, text_prefix="", offset=50, orientation="H", font_size=24, z_index=8):
    tick_size = 10
    display_text = f"{text_prefix}{int(value)}"
    
    if orientation == "H":
        y_line = y1 + offset 
        draw_rect(svg_content, x1, y_line, x2-x1, 2, "black", "black", 0, z_index)
        svg_content.append((z_index, f'<line x1="{x1}" y1="{y1}" x2="{x1}" y2="{y_line + tick_size}" stroke="black" stroke-width="1" stroke-dasharray="4,4" />'))
        svg_content.append((z_index, f'<line x1="{x2}" y1="{y2}" x2="{x2}" y2="{y_line + tick_size}" stroke="black" stroke-width="1" stroke-dasharray="4,4" />'))
        draw_text(svg_content, (x1 + x2) / 2, y_line - 15, display_text, font_size=font_size, weight="bold", z_index=z_index)
    elif orientation == "V":
        x_line = x1 - offset
        draw_rect(svg_content, x_line, y1, 2, y2-y1, "black", "black", 0, z_index)
        svg_content.append((z_index, f'<line x1="{x1}" y1="{y1}" x2="{x_line - tick_size}" y2="{y1}" stroke="black" stroke-width="1" stroke-dasharray="4,4" />'))
        svg_content.append((z_index, f'<line x1="{x2}" y1="{y2}" x2="{x_line - tick_size}" y2="{y2}" stroke="black" stroke-width="1" stroke-dasharray="4,4" />'))
        
        txt_x = x_line - 15
        txt_y = (y1 + y2) / 2
        draw_text(svg_content, txt_x, txt_y, display_text, font_size=font_size, fill="black", weight="bold", anchor="middle", z_index=z_index, rotation=-90)

# --- FONCTION DESSIN CONTENU ZONE ---
def draw_sash_content(svg, x, y, w, h, type_ouv, params, config_global, z_base=10):
    c_frame = config_global['color_frame']
    vis_ouvrant = 55 
    
    # Helper interne pour dessiner un "bloc vitré/panneau"
    def draw_leaf_interior(lx, ly, lw, lh):
        nb_trav = params.get('traverses', 0)
        
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
                draw_rect(svg, lx, y_trav_end, lw, h_rect_bas, col_b, "black", 1, z_base+1)
            # Haut
            h_rect_haut = y_trav_start - ly
            if h_rect_haut > 0:
                col_h = "#F0F0F0" if params.get('remp_haut') == "Panneau" else config_global['color_glass']
                draw_rect(svg, lx, ly, lw, h_rect_haut, col_h, "black", 1, z_base+1)
            
            draw_rect(svg, lx, y_trav_start, lw, ep_trav, c_frame, "black", 1, z_base+2)
            
        else:
            remp_glob = params.get('remplissage_global', 'Vitrage')
            col_g = "#F0F0F0" if remp_glob == "Panneau" else config_global['color_glass']
            draw_rect(svg, lx, ly, lw, lh, col_g, "black", 1, z_base+1)
            
            if nb_trav > 1:
                section_h = lh / (nb_trav + 1)
                for k in range(1, nb_trav + 1):
                    ty = ly + (section_h * k) - 10 
                    draw_rect(svg, lx, ty, lw, 20, c_frame, "black", 1, z_base+2)

    # --- TYPES OUVRANTS ---
    if type_ouv == "Fixe":
        draw_rect(svg, x, y, w, h, c_frame, "black", 1, z_base) 
        draw_leaf_interior(x, y, w, h)
        draw_text(svg, x+w/2, y+h/2, "F", font_size=40, fill="#335c85", weight="bold", z_index=z_base+5)
        
    elif type_ouv == "1 Vantail":
        ox, oy, ow, oh = x, y, w, h
        draw_rect(svg, ox, oy, ow, oh, c_frame, "black", 1, z_base)
        draw_leaf_interior(ox+vis_ouvrant, oy+vis_ouvrant, ow-2*vis_ouvrant, oh-2*vis_ouvrant)
        
        sens = params.get('sens', 'TG')
        mid_y = oy + oh/2
        if sens == 'TD': p = f"{ox+ow},{oy} {ox},{mid_y} {ox+ow},{oy+oh}"
        else: p = f"{ox},{oy} {ox+ow},{mid_y} {ox},{oy+oh}"
        svg.append((z_base+6, f'<polygon points="{p}" fill="none" stroke="black" stroke-width="1" />'))
        
        if params.get('ob', False):
            p_ob = f"{ox},{oy+oh} {ox+ow},{oy+oh} {ox+ow/2},{oy}"
            svg.append((z_base+6, f'<polygon points="{p_ob}" fill="none" stroke="black" stroke-width="1" />'))
            draw_text(svg, ox+ow/2, oy+oh-30, "OB", font_size=20, fill="black", weight="bold", z_index=z_base+7)

    elif type_ouv == "2 Vantaux":
        w_vtl = w / 2
        # Cadres
        draw_rect(svg, x, y, w_vtl, h, c_frame, "black", 1, z_base) 
        draw_rect(svg, x+w_vtl, y, w_vtl, h, c_frame, "black", 1, z_base) 
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
        if params.get('ob', False):
            ox, oy, ow, oh = (x+w_vtl, y, w_vtl, h) if is_princ_right else (x, y, w_vtl, h)
            p_ob = f"{ox},{oy+oh} {ox+ow},{oy+oh} {ox+ow/2},{oy}"
            svg.append((z_base+6, f'<polygon points="{p_ob}" fill="none" stroke="black" stroke-width="1" />'))
            draw_text(svg, ox+ow/2, oy+oh-30, "OB", font_size=20, fill="black", weight="bold", z_index=z_base+7)

    elif type_ouv == "Soufflet":
         draw_rect(svg, x, y, w, h, c_frame, "black", 1, z_base)
         draw_leaf_interior(x+vis_ouvrant, y+vis_ouvrant, w-2*vis_ouvrant, h-2*vis_ouvrant)
         p_ob = f"{x},{y+h} {x+w},{y+h} {x+w/2},{y}"
         svg.append((z_base+6, f'<polygon points="{p_ob}" fill="none" stroke="black" stroke-width="1" />'))
         draw_text(svg, x+w/2, y+h-30, "OB", font_size=20, fill="black", weight="bold", z_index=z_base+7)
         
    elif type_ouv == "Coulissant":
        w_vtl = w/2 + 25 
        draw_rect(svg, x, y, w_vtl, h, c_frame, "black", 1, z_base)
        draw_leaf_interior(x+vis_ouvrant, y+vis_ouvrant, w_vtl-2*vis_ouvrant, h-2*vis_ouvrant)
        
        draw_rect(svg, x+w/2-25, y, w_vtl, h, c_frame, "black", 1, z_base)
        draw_leaf_interior(x+w/2-25+vis_ouvrant, y+vis_ouvrant, w_vtl-2*vis_ouvrant, h-2*vis_ouvrant)
        
        ay = y+h/2
        svg.append((z_base+6, f'<line x1="{x+50}" y1="{ay}" x2="{x+w_vtl-50}" y2="{ay}" stroke="black" stroke-width="2" />'))
        svg.append((z_base+6, f'<line x1="{x+w-50}" y1="{ay}" x2="{x+w/2+25}" y2="{ay}" stroke="black" stroke-width="2" />'))

    # GRILLE D'AÉRATION
    pos_grille = params.get('pos_grille', 'Aucune')
    if pos_grille != "Aucune":
        gx, gy = 0, 0
        if type_ouv == "2 Vantaux":
            is_princ_right = (params.get('principal', 'D') == 'D')
            if pos_grille == "Vtl Principal":
                if is_princ_right: gx = x + w/2 + (w/2 - 250)/2
                else: gx = x + (w/2 - 250)/2
            elif pos_grille == "Vtl Secondaire":
                if is_princ_right: gx = x + (w/2 - 250)/2
                else: gx = x + w/2 + (w/2 - 250)/2
            else: gx = x + (w/2 - 250)/2
        elif type_ouv == "Coulissant": gx = x + (w/2 - 250)/2
        else: gx = x + (w - 250)/2
            
        gy = y + (vis_ouvrant - 12) / 2
        if type_ouv == "Fixe": gy = y + 10 

        draw_rect(svg, gx, gy, 250, 12, "#eeeeee", "black", 1, z_base+8)
        for k in range(1, 10):
            lx = gx + (250/10)*k
            svg.append((z_base+8, f'<line x1="{lx}" y1="{gy}" x2="{lx}" y2="{gy+12}" stroke="black" stroke-width="0.5" />'))


# --- 2. INTERFACE SIDEBAR ---
st.sidebar.title("🛠️ Configuration")

# --- SECTION 1 : IDENTIFICATION ---
with st.sidebar.expander("1. Identification", expanded=False):
    c1, c2 = st.columns(2)
    rep = c1.text_input("Repère", "F1")
    qte = c2.number_input("Qté", 1, 100, 1)

# --- SECTION 2 : MATERIAU ---
with st.sidebar.expander("2. Matériau & Ailettes", expanded=False):
    mat = st.radio("Matériau", ["PVC", "ALU"], horizontal=True)

    if mat == "PVC":
        liste_ailettes_std = [0, 30, 40, 60]
        liste_couleurs = ["Blanc (9016)", "Plaxé Chêne", "Plaxé Gris 7016", "Beige"]
    else: 
        liste_ailettes_std = [0, 20, 35, 60, 65]
        liste_couleurs = ["Blanc (9016)", "Gris 7016 Texturé", "Noir 2100 Sablé", "Anodisé Argent"]

    ep_dormant = st.number_input("Épaisseur Dormant (mm)", 50, 200, 70, step=10, help="Largeur visible du profilé")

    st.write("---")
    ail_val = st.selectbox(f"Ailettes H/G/D ({mat})", liste_ailettes_std, index=len(liste_ailettes_std)-1)
    bas_identique = st.checkbox("Seuil (Bas) identique ?", False)
    ail_bas = ail_val if bas_identique else st.selectbox(f"Seuil / Bas ({mat})", liste_ailettes_std, index=0)

    st.write("---")
    col_int = st.selectbox("Couleur Int", liste_couleurs)
    col_ext = st.selectbox("Couleur Ext", liste_couleurs)

# --- SECTION 3 : DIMENSIONS ---
with st.sidebar.expander("3. Dimensions & VR", expanded=True):
    c3, c4 = st.columns(2)
    l_dos_dormant = c3.number_input("Largeur Dos Dormant (mm)", 300, 5000, 1200, 10)
    h_dos_dormant = c4.number_input("Hauteur Totale (Dos Dormant)", 300, 5000, 1400, 10, help="Hauteur totale incluant le coffre")

    vr_opt = st.toggle("Volet Roulant", False)
    h_vr = 0
    vr_grille = False
    if vr_opt:
        h_vr = st.number_input("Hauteur Coffre", 0, 500, 185, 5)
        vr_grille = st.checkbox("Grille d'aération sur Coffre ?")
        h_menuiserie = h_dos_dormant - h_vr
        st.markdown(f"""<div class="metric-box">🧮 H. Menuiserie : {int(h_menuiserie)} mm</div>""", unsafe_allow_html=True)
    else:
        h_menuiserie = h_dos_dormant

# --- SECTION 4 : STRUCTURE & FINITIONS ---
with st.sidebar.expander("4. Structure & Finitions", expanded=True):
    mode_structure = st.radio("Mode Structure", ["Simple (1 Zone)", "Divisée (2 Zones)"], horizontal=True)

    color_map = {"Blanc": "#FFFFFF", "Gris": "#383E42", "Noir": "#1F1F1F", "Chêne": "#C19A6B"}
    hex_col = "#FFFFFF"
    for k, v in color_map.items():
        if k in col_int: hex_col = v

    cfg_global = {
        'color_frame': hex_col,
        'color_glass': "#d6eaff"
    }

    zones_config = [] 
    TYPES_OUVRANTS = ["Fixe", "1 Vantail", "2 Vantaux", "Coulissant", "Soufflet"]
    VITRAGES_INT = ["4mm", "33.2 (Sécurité)", "44.2 (Effraction)", "44.2 Silence"]
    VITRAGES_EXT = ["4mm", "6mm", "SP10 (Anti-effraction)", "Granité"]

    def config_zone_ui(label, key_prefix):
        st.markdown(f"**{label}**")
        c_type, c_opt = st.columns([1, 1])
        t = c_type.selectbox("Type", TYPES_OUVRANTS, key=f"{key_prefix}_t")
        p = {}
        
        if "Vantail" in t: p['sens'] = c_opt.radio("Sens", ["TG", "TD"], horizontal=True, key=f"{key_prefix}_s")
        if "2 Vantaux" in t: p['principal'] = c_opt.radio("Principal", ["G", "D"], horizontal=True, key=f"{key_prefix}_p")
        if "Vant" in t or "Soufflet" in t: p['ob'] = c_opt.checkbox("OB", False, key=f"{key_prefix}_o")
        
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
            p['pos_grille'] = st.selectbox("Position Grille", opts_grille, key=f"{key_prefix}_pg")
            
        return t, p

    if mode_structure == "Simple (1 Zone)":
        t1, p1 = config_zone_ui("Configuration Unique", "z1")
        zones_config.append({'type': t1, 'params': p1, 'x': 0, 'y': 0, 'w': l_dos_dormant, 'h': h_menuiserie})

    else:
        c_div1, c_div2 = st.columns(2)
        sens_coupe = c_div1.selectbox("Type Division", ["Horizontale (-)", "Verticale (|)"])
        
        if sens_coupe == "Horizontale (-)":
            h_basse = c_div2.number_input("Hauteur Zone Basse (mm)", 0, int(h_menuiserie), int(h_menuiserie/2))
            h_haute = h_menuiserie - h_basse 
            st.divider()
            t_bas, p_bas = config_zone_ui("ZONE BASSE", "zb")
            st.divider()
            t_haut, p_haut = config_zone_ui("ZONE HAUTE", "zh")
            zones_config.append({'type': t_haut, 'params': p_haut, 'x': 0, 'y': 0, 'w': l_dos_dormant, 'h': h_haute})
            zones_config.append({'type': t_bas, 'params': p_bas, 'x': 0, 'y': h_haute, 'w': l_dos_dormant, 'h': h_basse})

        else: # Verticale
            w_gauche = c_div2.number_input("Largeur Zone Gauche (mm)", 0, int(l_dos_dormant), int(l_dos_dormant/2))
            w_droite = l_dos_dormant - w_gauche
            st.divider()
            t_g, p_g = config_zone_ui("ZONE GAUCHE", "zg")
            st.divider()
            t_d, p_d = config_zone_ui("ZONE DROITE", "zd")
            zones_config.append({'type': t_g, 'params': p_g, 'x': 0, 'y': 0, 'w': w_gauche, 'h': h_menuiserie})
            zones_config.append({'type': t_d, 'params': p_d, 'x': w_gauche, 'y': 0, 'w': w_droite, 'h': h_menuiserie})

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
    draw_rect(svg, bx, by, bw, bh, col_fin, "none", 0, 0)
    
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

    for z in zones_config:
        draw_sash_content(svg, z['x']+th_dorm, z['y']+th_dorm, z['w']-2*th_dorm, z['h']-2*th_dorm, z['type'], z['params'], cfg_global, z_base=4)

    # COTATION 
    font_dim = 26
    draw_dimension_line(svg, 0, 0, l_dos_dormant, 0, l_dos_dormant, "", h_menuiserie+50, "H", font_dim, 9)
    l_ht = l_dos_dormant + 2*ail_val
    draw_dimension_line(svg, -ail_val, 0, l_dos_dormant+ail_val, 0, l_ht, "", h_menuiserie+120, "H", font_dim, 9)
    draw_dimension_line(svg, 0, 0, 0, h_menuiserie, h_menuiserie, "", 50, "V", font_dim, 9)
    y_start_dd = -h_vr if vr_opt else 0
    draw_dimension_line(svg, 0, y_start_dd, 0, h_menuiserie, h_dos_dormant, "", 130, "V", font_dim, 9)
    y_start_ht = -ht_haut
    y_end_ht = h_menuiserie + ht_bas
    h_visuel_total = abs(y_end_ht - y_start_ht)
    draw_dimension_line(svg, 0, y_start_ht, 0, y_end_ht, h_visuel_total, "", 210, "V", font_dim, 9)

    m = 250
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-ail_val-m} {-ht_haut-m} {l_dos_dormant+2*ail_val+2*m} {h_menuiserie+ht_haut+ht_bas+2*m}" style="background-color:white;">{"".join([el[1] for el in sorted(svg, key=lambda x:x[0])])}</svg>'


# --- RENDU FINAL (NOUVELLE MISE EN PAGE V72) ---

# 1. TITRE ET DESSIN CENTRÉS
st.markdown("<h2 class='centered-header'>Plan Technique</h2>", unsafe_allow_html=True)
c_spacer1, c_draw, c_spacer2 = st.columns([1, 3, 1])
with c_draw:
    st.markdown(generate_svg_v73(), unsafe_allow_html=True)

st.markdown("---")

# 2. RÉCAPITULATIF EN DESSOUS (Sur 2 colonnes)
st.markdown("<h3 class='centered-header'>Récapitulatif - Bon de Commande</h3>", unsafe_allow_html=True)

c_table, c_details = st.columns([1, 1])

with c_table:
    st.subheader("Informations Générales")
    desc_structure = f"{mode_structure}"
    if mode_structure != "Simple (1 Zone)":
        desc_structure += f" ({sens_coupe})"
    
    vr_txt = "Non"
    if vr_opt:
        vr_txt = f"Coffre {h_vr}mm"
        if vr_grille: vr_txt += " + Grille sur Coffre"
    
    data = {
        "Repère": rep,
        "Quantité": qte,
        "Dim. Dos Dormant": f"{l_dos_dormant} x {h_dos_dormant} mm",
        "Matériau": f"{mat} (Dormant {ep_dormant}mm)",
        "Couleur": f"Int: {col_int} / Ext: {col_ext}",
        "Structure": desc_structure,
        "VR": vr_txt,
        "Ailettes": f"H:{ail_val}/G:{ail_val}/D:{ail_val}/B:{ail_bas}"
    }
    st.table(data)

with c_details:
    st.subheader("Détail des Zones")
    for i, z in enumerate(zones_config):
        t = z['type']
        p = z['params']
        st.markdown(f"#### Zone {i+1} : {t}")
        
        details = []
        if 'sens' in p: details.append(f"Sens : {p['sens']}")
        if 'principal' in p: details.append(f"Principal : {p['principal']}")
        if p.get('ob'): details.append("Oscillo-battant : Oui")
        
        if 'traverses' in p and p['traverses'] == 1:
             details.append(f"Soubassement : {p['remp_bas']} (Bas) / {p['remp_haut']} (Haut)")
             if p.get('pos_traverse') == 'Sur mesure (du bas)':
                  details.append(f"Hauteur Traverse : {p['h_traverse_custom']}mm (axe depuis bas vitrage)")
        elif 'remplissage_global' in p:
             details.append(f"Remplissage : {p['remplissage_global']}")
             
        v_ext = p.get('vitrage_ext', '-')
        v_int = p.get('vitrage_int', '-')
        details.append(f"Vitrage : Ext {v_ext} / Int {v_int}")
            
        if p.get('pos_grille', 'Aucune') != 'Aucune': details.append(f"Grille Aération : Oui ({p['pos_grille']})")
        
        for d in details:
            st.write(f"- {d}")
        st.write("---")
