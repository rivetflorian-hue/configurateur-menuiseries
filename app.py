import streamlit as st
import math

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="FenêtrePro V3 Fabrication", layout="wide")

# --- CONSTANTES VISUELLES ---
VISUAL_DORMANT_THICKNESS = 25  # Épaisseur visuelle du cadre extérieur (Ouvrant)
VISUAL_FIXED_THICKNESS = 70    # Épaisseur visuelle du cadre extérieur (Fixe)
VISUAL_SASH_THICKNESS = 55     # Épaisseur visuelle de l'ouvrant
COLOR_FRAME = "#FFFFFF"        # Blanc
COLOR_GLASS = "#d6eaff"        # Bleu vitrage
COLOR_FIN = "#D3D3D3"          # Gris Ailettes

# --- FONCTIONS UTILITAIRES DE DESSIN ---

def draw_rect(svg_content, x, y, w, h, fill, stroke="black", stroke_width=1, z_index=1):
    """Ajoute un rectangle au contenu SVG."""
    rect = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" />'
    svg_content.append((z_index, rect))

def draw_text(svg_content, x, y, text, font_size=12, fill="black", weight="normal", anchor="middle", z_index=10, stroke="none"):
    """Ajoute du texte au contenu SVG."""
    style = ""
    if stroke != "none":
        style = f'stroke="{stroke}" stroke-width="0.5" paint-order="stroke" stroke-linejoin="round"'
    
    txt = f'<text x="{x}" y="{y}" font-family="Arial" font-size="{font_size}" fill="{fill}" {style} font-weight="{weight}" text-anchor="{anchor}" dominant-baseline="middle">{text}</text>'
    svg_content.append((z_index, txt))

def draw_arrow(svg_content, x1, y1, x2, y2, stroke="black", stroke_width=1, z_index=5):
    """Dessine une flèche simple."""
    # Ligne
    line = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{stroke_width}" />'
    svg_content.append((z_index, line))
    
    # Pointe (Triangle)
    angle = math.atan2(y2 - y1, x2 - x1)
    arrow_len = 10
    angle1 = angle + math.pi / 6
    angle2 = angle - math.pi / 6
    
    x_arrow1 = x2 - arrow_len * math.cos(angle1)
    y_arrow1 = y2 - arrow_len * math.sin(angle1)
    x_arrow2 = x2 - arrow_len * math.cos(angle2)
    y_arrow2 = y2 - arrow_len * math.sin(angle2)
    
    arrow_head = f'<polygon points="{x2},{y2} {x_arrow1},{y_arrow1} {x_arrow2},{y_arrow2}" fill="{stroke}" />'
    svg_content.append((z_index, arrow_head))

def draw_dimension_line(svg_content, x1, y1, x2, y2, value, offset=50, orientation="H", font_size=16, z_index=8):
    """Dessine une ligne de cote technique."""
    tick_size = 5
    
    if orientation == "H":
        # Pour une cote H, on force y1 et y2 à être sur la ligne de cote pour éviter les diagonales
        y_line = y1 + offset # Le point de référence + l'offset
        
        # Ligne principale
        draw_rect(svg_content, x1, y_line, x2-x1, 1, "black", "black", 0, z_index)
        
        # Traits de rappel (Ticks) verticaux
        # Départ du point mesuré (y1) jusqu'à la ligne de cote (y_line)
        svg_content.append((z_index, f'<line x1="{x1}" y1="{y1}" x2="{x1}" y2="{y_line + tick_size}" stroke="black" stroke-width="0.5" stroke-dasharray="2,2" />'))
        svg_content.append((z_index, f'<line x1="{x2}" y1="{y2}" x2="{x2}" y2="{y_line + tick_size}" stroke="black" stroke-width="0.5" stroke-dasharray="2,2" />'))
        
        # Texte
        draw_text(svg_content, (x1 + x2) / 2, y_line - 10, str(int(value)), font_size=font_size, weight="bold", z_index=z_index)
        
    elif orientation == "V":
        # Pour une cote V, on force x1 et x2
        x_line = x1 - offset
        
        # Ligne principale
        draw_rect(svg_content, x_line, y1, 1, y2-y1, "black", "black", 0, z_index)
        
        # Traits de rappel
        svg_content.append((z_index, f'<line x1="{x1}" y1="{y1}" x2="{x_line - tick_size}" y2="{y1}" stroke="black" stroke-width="0.5" stroke-dasharray="2,2" />'))
        svg_content.append((z_index, f'<line x1="{x2}" y1="{y2}" x2="{x_line - tick_size}" y2="{y2}" stroke="black" stroke-width="0.5" stroke-dasharray="2,2" />'))
        
        # Texte (Rotation -90deg)
        txt_x = x_line - 10
        txt_y = (y1 + y2) / 2
        txt = f'<text x="{txt_x}" y="{txt_y}" font-family="Arial" font-size="{font_size}" fill="black" font-weight="bold" text-anchor="middle" dominant-baseline="middle" transform="rotate(-90, {txt_x}, {txt_y})">{int(value)}</text>'
        svg_content.append((z_index, txt))

# --- INTERFACE SIDEBAR ---
st.sidebar.title("🛠️ Configuration")

# 1. IDENTIFICATION
st.sidebar.subheader("Identification")
col_id1, col_id2 = st.sidebar.columns(2)
repere_client = col_id1.text_input("Repère", value="F1")
quantite = col_id2.number_input("Quantité", min_value=1, value=1)

# 2. DIMENSIONS
st.sidebar.subheader("Dimensions Fabrication")
col1, col2 = st.sidebar.columns(2)
largeur_saisie = col1.number_input("Largeur (mm)", min_value=300, value=1200, step=10)
hauteur_saisie = col2.number_input("Hauteur Totale (mm)", min_value=300, value=1400, step=10)
hauteur_allege = st.sidebar.number_input("Hauteur d'allège (mm)", value=900, step=10)

# 3. STRUCTURE
st.sidebar.subheader("Structure & Type")
type_ouverture = st.sidebar.selectbox("Type d'ouverture", ["Fixe", "1 Vantail", "2 Vantaux", "Coulissant"])

vr_actif = False
vr_hauteur_coffre = 0
vr_option = st.sidebar.toggle("Option Volet Roulant (Bloc-Baie)", value=False)
if vr_option:
    vr_actif = True
    vr_hauteur_coffre = st.sidebar.number_input("Hauteur Coffre (mm)", value=185, step=5)

# Calcul Hauteur Dormant (Blanc)
hauteur_fab = hauteur_saisie - (vr_hauteur_coffre if vr_actif else 0)

# 4. CONFIGURATION DÉTAILLÉE
st.sidebar.markdown("---")
st.sidebar.write("### ⚙️ Détails & Options")

leaves = [] # Liste des zones
options_globales_list = [] # Pour le récap

# -- DEFINITION DES ZONES (LEAVES) --
if type_ouverture == "Fixe":
    leaves.append({"type": "Fixe", "width_ratio": 1.0})
elif type_ouverture == "1 Vantail":
    sens = st.sidebar.selectbox("Sens", ["Tirant Droit", "Tirant Gauche", "Oscillo-battant"])
    leaves.append({"type": "Ouvrant", "sens": sens, "width_ratio": 1.0})
elif type_ouverture == "2 Vantaux":
    sens = st.sidebar.selectbox("Sens d'ouverture", ["Tirant Droit (Principal Droite)", "Tirant Gauche (Principal Gauche)"])
    is_principal_right = "Principal Droite" in sens
    # Gauche
    leaves.append({"type": "Ouvrant", "principal": not is_principal_right, "sens": "G", "width_ratio": 0.5})
    # Droite
    leaves.append({"type": "Ouvrant", "principal": is_principal_right, "sens": "D", "width_ratio": 0.5})
elif type_ouverture == "Coulissant":
    sens = st.sidebar.selectbox("Sens (Vantail Principal)", ["Principal Gauche", "Principal Droite"])
    is_principal_left = "Principal Gauche" in sens
    # Gauche
    leaves.append({"type": "Coulissant", "principal": is_principal_left, "side": "G", "width_ratio": 0.5})
    # Droite
    leaves.append({"type": "Coulissant", "principal": not is_principal_left, "side": "D", "width_ratio": 0.5})

# -- BOUCLE DE CONFIGURATION PAR ZONE --
has_ventilation = st.sidebar.checkbox("Grille d'aération")
pos_ventilation_leaf = "Aucune"
if has_ventilation:
    if vr_actif and st.sidebar.radio("Type Pose Grille", ["Sur Menuiserie", "Sur Coffre VR"]) == "Sur Coffre VR":
        pos_ventilation_leaf = "Coffre"
    else:
        # Sur Menuiserie
        if len(leaves) > 1:
            choix_grille = st.sidebar.radio("Sur quel vantail ?", ["Vtl Principal", "Vtl Secondaire", "Les Deux"], horizontal=True)
            if choix_grille == "Les Deux": pos_ventilation_leaf = "Tous"
            elif choix_grille == "Vtl Principal": pos_ventilation_leaf = "Principal"
            else: pos_ventilation_leaf = "Secondaire"
        else:
            pos_ventilation_leaf = "Tous"

# Options Quincaillerie par Zone
options_quinc_str = []
st.sidebar.subheader("Options & Accessoires")
with st.sidebar.expander("Configurer les Options (Ferme-porte...)", expanded=True):
    opts = st.multiselect("Sélectionner", ["Ferme Porte", "Butée aimantée", "Crémone pompier", "Barre anti-panique", "Pushbar", "Seuil PMR", "Oscillo-battant (Inclus)"])
    autre = st.text_input("Autre option")
    if opts: options_quinc_str.extend(opts)
    if autre: options_quinc_str.append(autre)

# Ailettes
st.sidebar.subheader("Ailettes de Rénovation")
ailette_config = st.sidebar.selectbox("Configuration", ["Standard 60mm (3 côtés)", "Sur mesure"])
if ailette_config == "Sur mesure":
    a_haut = st.sidebar.number_input("Haut", value=60)
    a_gauche = st.sidebar.number_input("Gauche", value=60)
    a_droite = st.sidebar.number_input("Droite", value=60)
    a_bas = st.sidebar.number_input("Bas", value=0)
else:
    a_haut, a_gauche, a_droite, a_bas = 60, 60, 60, 0

notes = st.text_area("Notes Libres / Informations Complémentaires")

# --- MOTEUR DE DESSIN ---
def generate_svg():
    svg_elements = [] 
    
    # Marges
    margin_top = 150 + (vr_hauteur_coffre if vr_actif else 0)
    margin_bottom = 300
    margin_left = 250
    margin_right = 100
    
    # 1. FOND GRIS (AILETTES) - Z=0
    # Le fond gris dépasse du cadre blanc
    x_ail = -a_gauche
    y_ail = -a_haut - (vr_hauteur_coffre if vr_actif else 0)
    w_ail = largeur_saisie + a_gauche + a_droite
    h_ail = hauteur_fab + a_haut + a_bas + (vr_hauteur_coffre if vr_actif else 0)
    
    draw_rect(svg_elements, x_ail, y_ail, w_ail, h_ail, COLOR_FIN, "none", 0, 0)
    
    # 2. COFFRE VR - Z=1
    if vr_actif:
        draw_rect(svg_elements, 0, -vr_hauteur_coffre, largeur_saisie, vr_hauteur_coffre, "#E0E0E0", "black", 1, 1)
        # Texte VR (Z=20 pour être sûr)
        draw_text(svg_elements, largeur_saisie/2, -vr_hauteur_coffre/2, f"COFFRE VR {int(vr_hauteur_coffre)}", 14, "white", "bold", z_index=20, stroke="black")

    # 3. DORMANT (CADRE BLANC) - Z=2
    # On dessine un cadre unique pour le dormant pour éviter les bugs d'affichage
    draw_rect(svg_elements, 0, 0, largeur_saisie, hauteur_fab, COLOR_FRAME, "black", 2, 2)
    
    # 4. OUVRANTS (SASHES) - Z=3 et +
    current_x = 0
    
    # Gestion Z-Index Coulissant (Principal devant)
    sorted_leaves_indices = range(len(leaves))
    if type_ouverture == "Coulissant":
        # On veut dessiner le secondaire (derrière) EN PREMIER, et le principal (devant) EN DERNIER
        # Si leaf 0 est principal -> ordre [1, 0]
        # Si leaf 1 est principal -> ordre [0, 1]
        is_0_principal = leaves[0].get("principal", False)
        if is_0_principal: sorted_leaves_indices = [1, 0]
        else: sorted_leaves_indices = [0, 1]

    # Mais attention, current_x doit avancer dans l'ordre 0, 1.
    # Donc on calcule d'abord les positions, puis on dessine dans l'ordre de Z-index.
    leaf_positions = []
    for leaf in leaves:
        w_zone = largeur_saisie * leaf.get("width_ratio", 1.0)
        leaf_positions.append({"x": current_x, "w": w_zone, "leaf": leaf})
        current_x += w_zone

    # Boucle de dessin (selon ordre z-index)
    for i in sorted_leaves_indices:
        pos = leaf_positions[i]
        leaf = pos["leaf"]
        x_zone, w_zone = pos["x"], pos["w"]
        
        # FIXE
        if leaf["type"] == "Fixe":
            # Cadre large visuel (70mm)
            th = VISUAL_FIXED_THICKNESS
            draw_rect(svg_elements, x_zone + th, th, w_zone - 2*th, hauteur_fab - 2*th, COLOR_GLASS, "black", 1, 3)
            draw_text(svg_elements, x_zone + w_zone/2, hauteur_fab/2, "F", 40, "#335c85", "bold", z_index=5)

        # OUVRANT (Frappe)
        elif leaf["type"] == "Ouvrant":
            d_th = VISUAL_DORMANT_THICKNESS
            s_th = VISUAL_SASH_THICKNESS
            # Sash
            sx = x_zone + d_th
            sy = d_th
            sw = w_zone - 2*d_th
            sh = hauteur_fab - 2*d_th
            
            draw_rect(svg_elements, sx, sy, sw, sh, COLOR_FRAME, "black", 1, 4)
            # Vitrage
            gx = sx + s_th
            gy = sy + s_th
            gw = sw - 2*s_th
            gh = sh - 2*s_th
            draw_rect(svg_elements, gx, gy, gw, gh, COLOR_GLASS, "black", 1, 5)
            
            # Symbole Sens
            if leaf.get("sens") == "D" or leaf.get("sens") == "Tirant Droit":
                # Triangle pointe à gauche (charnières droite)
                svg_elements.append((6, f'<polygon points="{sx},{sy} {sx+sw},{sy+sh/2} {sx},{sy+sh}" fill="none" stroke="black" stroke-width="1" />'))
            elif leaf.get("sens") == "G" or leaf.get("sens") == "Tirant Gauche":
                # Triangle pointe à droite (charnières gauche)
                svg_elements.append((6, f'<polygon points="{sx+sw},{sy} {sx},{sy+sh/2} {sx+sw},{sy+sh}" fill="none" stroke="black" stroke-width="1" />'))
            
            # Grille Aération
            has_this_grille = False
            if pos_ventilation_leaf == "Tous": has_this_grille = True
            elif pos_ventilation_leaf == "Principal" and leaf.get("principal"): has_this_grille = True
            elif pos_ventilation_leaf == "Secondaire" and not leaf.get("principal"): has_this_grille = True
            
            if has_this_grille:
                # Sur traverse haute ouvrant
                g_w = min(250, sw - 20)
                g_x = sx + (sw - g_w)/2
                g_y = sy + (s_th/2) - 5
                draw_rect(svg_elements, g_x, g_y, g_w, 10, "#eeeeee", "black", 1, 7)
                # Petits traits grille
                for k in range(1, 10):
                    lx = g_x + (g_w/10)*k
                    svg_elements.append((7, f'<line x1="{lx}" y1="{g_y}" x2="{lx}" y2="{g_y+10}" stroke="black" stroke-width="0.5" />'))

        # COULISSANT
        elif leaf["type"] == "Coulissant":
            overlap = 50
            # Calcul largeur vantail pour chevauchement
            # Largeur totale zone = w_zone (ici 50% du total)
            # Mais en réalité chaque vantail fait 50% + overlap/2
            # Pour simplifier visuellement :
            sash_w = w_zone + (overlap / 2)
            
            # Position X dépend du côté
            if leaf["side"] == "G":
                sx = x_zone # Collé à gauche
            else:
                sx = x_zone - (overlap / 2) # Décalé vers la gauche pour chevaucher
            
            sy = VISUAL_DORMANT_THICKNESS
            sh = hauteur_fab - 2*VISUAL_DORMANT_THICKNESS
            
            # Z-Index: Si principal, on le met plus haut (8), sinon (4)
            z_lvl = 8 if leaf["principal"] else 4
            
            # Dessin Sash
            draw_rect(svg_elements, sx, sy, sash_w, sh, COLOR_FRAME, "black", 1, z_lvl)
            # Dessin Vitre
            v_th = VISUAL_SASH_THICKNESS
            draw_rect(svg_elements, sx+v_th, sy+v_th, sash_w-2*v_th, sh-2*v_th, COLOR_GLASS, "black", 1, z_lvl+1)
            
            # Flèche
            arrow_y = sy + sh/2
            if leaf["side"] == "G": # Flèche vers droite
                draw_arrow(svg_elements, sx+v_th+20, arrow_y, sx+sash_w-v_th-20, arrow_y, "black", 2, z_lvl+2)
            else: # Flèche vers gauche
                draw_arrow(svg_elements, sx+sash_w-v_th-20, arrow_y, sx+v_th+20, arrow_y, "black", 2, z_lvl+2)

            # Grille Aération (Coulissant)
            has_this_grille = False
            if pos_ventilation_leaf == "Tous": has_this_grille = True
            elif pos_ventilation_leaf == "Principal" and leaf.get("principal"): has_this_grille = True
            elif pos_ventilation_leaf == "Secondaire" and not leaf.get("principal"): has_this_grille = True

            if has_this_grille:
                g_w = min(200, sash_w - 40)
                g_x = sx + (sash_w - g_w)/2
                g_y = sy + (v_th/2) - 5
                draw_rect(svg_elements, g_x, g_y, g_w, 10, "#eeeeee", "black", 1, z_lvl+3)


    # 5. COTES EXTÉRIEURES (HORS BOUCLE -> UNIQUES)
    # Ligne Fabrication (Largeur)
    y_cote_fab = hauteur_fab + 50
    draw_dimension_line(svg_elements, 0, 0, largeur_saisie, 0, largeur_saisie, offset=hauteur_fab+50, orientation="H", z_index=9)
    
    # Ligne Totale (Largeur)
    y_cote_tot = hauteur_fab + 100 + (a_bas if not vr_actif else 0) # Esthétique
    lt_tot = largeur_saisie + a_gauche + a_droite
    draw_dimension_line(svg_elements, -a_gauche, 0, largeur_saisie+a_droite, 0, lt_tot, offset=hauteur_fab+120, orientation="H", z_index=9)

    # Ligne Fabrication (Hauteur)
    draw_dimension_line(svg_elements, 0, 0, 0, hauteur_fab, hauteur_fab, offset=50, orientation="V", z_index=9)
    
    # Ligne Totale (Hauteur)
    ht_tot = hauteur_fab + a_haut + a_bas + (vr_hauteur_coffre if vr_actif else 0)
    y_start_tot = -vr_hauteur_coffre - a_haut if vr_actif else -a_haut
    y_end_tot = hauteur_fab + a_bas
    draw_dimension_line(svg_elements, 0, y_start_tot, 0, y_end_tot, ht_tot, offset=120, orientation="V", z_index=9)

    # 6. REPÈRE CENTRAL
    cx = largeur_saisie / 2
    cy = hauteur_fab / 2
    svg_elements.append((20, f'<circle cx="{cx}" cy="{cy}" r="30" fill="white" stroke="black" stroke-width="1" />'))
    draw_text(svg_elements, cx, cy, repere_client, 20, "black", "bold", z_index=21)

    # CONSTRUCTION DU SVG FINAL
    svg_elements.sort(key=lambda x: x[0]) # Tri par z-index
    svg_content = "".join([el[1] for el in svg_elements])
    
    view_x = -a_gauche - 150
    view_y = (-vr_hauteur_coffre - a_haut - 100) if vr_actif else (-a_haut - 100)
    view_w = largeur_saisie + a_gauche + a_droite + 300
    view_h = hauteur_fab + a_haut + a_bas + (vr_hauteur_coffre if vr_actif else 0) + 300
    
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_x} {view_y} {view_w} {view_h}" style="background-color: white;">{svg_content}</svg>'

# --- AFFICHAGE PRINCIPAL ---
col_graph, col_data = st.columns([2, 1])

with col_graph:
    st.subheader("Plan Technique")
    svg_html = generate_svg()
    st.markdown(svg_html, unsafe_allow_html=True)
    
    # Bouton Téléchargement (Faux bouton HTML pour l'exemple, Streamlit natif ne télécharge pas le SVG facilement sans hack, 
    # mais pour l'instant on affiche juste)
    st.download_button("Télécharger le fichier SVG", svg_html, file_name=f"{repere_client}.svg", mime="image/svg+xml")

with col_data:
    st.subheader("Récapitulatif - Bon de Commande")
    
    # Construction des options string
    options_finales = ", ".join(options_quinc_str) if options_quinc_str else "-"
    
    # Construction Données
    data = {
        "Caractéristique": [
            "Repère", 
            "Quantité", 
            "Type d'ouvrant", 
            "Dimensions (Dos de Dormant)", 
            "Hauteur Allège", 
            "Ailettes de Recouvrement", 
            "Aération", 
            "Volet Roulant", 
            "Options & Accessoires",
            "Notes"
        ],
        "Valeur": [
            repere_client,
            str(quantite),
            f"{type_ouverture} - {leaves[0].get('sens', '') if len(leaves)>0 else ''}",
            f"{largeur_saisie} x {hauteur_fab} mm (Hors VR)",
            f"{hauteur_allege} mm",
            f"H:{a_haut}/G:{a_gauche}/D:{a_droite}/B:{a_bas}",
            f"Oui ({pos_ventilation_leaf})" if has_ventilation else "Non",
            f"Coffre {vr_hauteur_coffre}mm" if vr_actif else "Sans VR",
            options_finales,
            notes
        ]
    }
    st.table(data)