#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# AUDIOPHONICS - RASPDAC MINI - Gestion de l'écran OLED
# Définition des trames des pages à afficher sur l'écran OLED
# Fichier : raspdac_oled_screen_frames.py
# 15 Mai 2019      : Creation
# 02 Juin 2019     : Gestion du driver ES9038Q2M + ajout Menu Télécommande
# ----------------------------------------------------------------------------
# Ce fichier python est importé par raspdac_oled_screen_display.py
# Ce fichier est nécessaire au script principal : raspdac_oled_main.py
# Ce fichier doit être installé dans le même répertoire que :
#   -> raspdac_oled_main.py (script principal)
#   -> raspdac_oled_request_mpd (gestion des requêtes avec le serveur MPD)
#   -> raspdac_oled_request_os (gestion des requêtes avec l'OS Linux)
#   -> raspdac_oled_screen_menu.py (gestion du MENU activé par télécommande)
#   -> raspdac_oled_screen_telecommand.py (gestion de la télécommande)
#   -> raspdac_oled_screen_display.py (affichage sur l'écran)
#   -> fonts : répertoire des polices de caractères utilisées pour l'affichage
# ----------------------------------------------------------------------------
'''
    Ce module définit la trame d'affichage de chaque page.
    Ces trames sont stockées dans un dictionnaire (frames[])

    Le script principal (raspdac_oled_main.py) séquence l'affichage
    de différentes pages du RASPDAC-MINI :
    -> Page INIT : affichage du fabriquant au démarrage
    -> Page IP : affichage de l'adresse IP (WiFi ou Filaire)
    -> Page SPDIF : affichage "SPDIF" si l'entrée "SPDIF" est sélectionnée
    Quand l'entrée I2S est sélectionnée, il y a alternance entre :
    -> Page I2S-PLAY1 : Affichage Artiste + Album 
    -> Page I2S-PLAY2 : Affichage Titre + Freq. Echantillonnage
    Les pages ci-dessus peuvent être détournées temporairement
    -> Page VOLUME : affichage du volume quand il est modifié
    -> Page SAVER : affichage après une période d'inactivité
    L'appui de la touche 'MENU' de la télécommande infrarouge permet
    d'activer une page 'MENU' :
    -> Page MENU : permet de configurer le pilote ALSA

    Chacune de ces pages est bâtie à partir d'une trame définie dans ce fichier
    Chaque trame est constitué d'objets (au minimum 1).
    On distingue les objets suivant plusieurs types :
    -> objet de type 'icon' : icône à afficher
    -> objet de type 'text' : chaîne ou caractère ou nombre à afficher
    -> objet de type 'scrolling' : chaîne à afficher avec scrolling
    -> objet de type 'rectangle' : cadre rectangulaire
    -> objet de type 'volume_bar' : rectangle dynamique (barre de volume)
    -> objet de type 'elapsed_bar' : rectangle dynamique (temps écoulé)
    
    Chaque objet est identifié par une clef dont le nom est laissé libre
    mais qui doit donner si possible une indication sur la fonction de l'objet
    
    Enfin chaque objet est constitué de paramètres utiles à l'affichage de l'objet
    et utilisés par le module raspdac_oled_pages.py qui est lui même appelé par le
    script principal.
    
    Un paramètre particulier "connector" permet de connecter un objet au
    dictionnaire des informations et données dynamiques (par exemple les données
    issues de l'interrogation du serveur MPD.
    
    Le paramètre "justify_xy" permet de justifier les objets de type 'text',
    les objets de type 'icon' et les objets de type 'scrolling'
    -> justification en x qui vaut 'L' pour Left, 'C' pour Center ou 'R' pour Right
    -> justification en y qui vaut 'H' pour High, 'C' pour Center ou 'B' pour Bottom
'''
# Définition d'un dictionnaire des trames des pages
frames = dict()

# Trame de la page 'INIT'
frames['INIT'] = {
    "manufacturer" : {
        "type" : 'text',
        "value" : 'Network player',
        "font_name" : 'arial.ttf', "font_size" : 19,
        "justify_xy" : 'CH', "x" : 64, "y" : 0
        },
    "version_raspdac" : {
        "type" : 'text',
        #"value" : 'Raspdac Mini v0.2',
        "value" : 'Raspdac Mini',
        "font_name" : 'arial.ttf', "font_size" : 12,
        "justify_xy" : 'CC', "x" : 64, "y" : 40
        },
    "version_rune" : {
        "type" : 'text',
        "value" : 'Linn Openhome',
        "font_name" : 'arial.ttf', "font_size" : 12,
        "justify_xy" : 'CB', "x" : 64, "y" : 63
        }
    }

# Trame de la page 'IP'
frames['IP'] = {
    "time" : {
        "type" : 'text',
        #"connector" : ( 'info' , 'hms' ),
        "connector" : ( 'info' , 'hms'),
        "font_name" : 'arial.ttf', "font_size" : 32,
        "justify_xy" : 'CH', "x" : 64, "y" : 0,
        },
    "ip_icon" : {
        "type" : 'icon',
        "connector" : ( 'icons' , 'ip_type' ),
        "font_name" : 'fontawesome-webfont.ttf', "font_size" : 14,
        "justify_xy" : 'LB', "x" : 1, "y" : 46
        },
    "ip" : {
        "type" : 'text',
        "connector" : ( 'info' , 'ip' ),
        "font_name" : 'msyh.ttf', "font_size" : 15,
        "justify_xy" : 'LB', "x" : 25, "y" : 48
        },
    "volume_icon" : {
        "type" : 'icon',
        "connector" : ( 'icons' , 'speaker' ),
        "font_name" : 'fontawesome-webfont.ttf', "font_size" : 14,
        "justify_xy" : 'LB', "x" : 2, "y" : 61
        },
    "volume_value" : {
        "type" : 'text',
        "connector" : ( 'mpd_status' , 'volume' ),
        "font_name" : 'msyh.ttf', "font_size" : 15,
        "justify_xy" : 'LB', "x" : 25, "y" : 63
        }
    }

# Trame de la page 'MENU'
frames['MENU'] = {
    "item_title" : {
        "type" : 'text',
        "connector" : ( 'menu' , 'menu_control' ),
        "font_name" : 'msyh.ttf', "font_size" : 18,
        "justify_xy" : 'LC', "x" : 10, "y" : 10
        },
    "item_id" : {
        "type" : 'text',
        "connector" : ( 'menu' , 'menu_item' ),
        "font_name" : 'msyh.ttf', "font_size" : 18,
        "justify_xy" : 'CC', "x" : 105, "y" : 10
        },
    "id_frame" : {
        "type" : 'rectangle',
        "connector" : ( 'menu' , 'flag_active_item' ),
        "xmin" : 97, "ymin" : 0,
        "xmax" : 113, "ymax" : 20,
        },
    "item_comment" : {
        "type" : 'scrolling',
        "connector" : ( 'menu' , 'menu_txt' ),
        "font_name" : 'msyh.ttf', "font_size" : 12,
        "justify_xy" : 'CC', "x" : 64, "y" : 35,
        },
    "cancel_item" : {
        "type" : 'text',
        "value" : 'MENU=EXIT',
        "font_name" : 'msyh.ttf', "font_size" : 9,
        "justify_xy" : 'CB', "x" : 32, "y" : 63,
        },
    "apply_item" : {
        "type" : 'text',
        "value" : 'OK=APPLY',
        "font_name" : 'msyh.ttf', "font_size" : 9,
        "justify_xy" : 'CB', "x" : 96, "y" : 63
        },
    "previous_item_icon" : {
        "type" : 'icon',
        "connector" : ( 'icons' , 'up' ),
        "font_name" : 'fontawesome-webfont.ttf', "font_size" : 15,
        "justify_xy" : 'LC', "x" : 0, "y" : 5
        },
    "next_item_icon" : {
        "type" : 'icon',
        "connector" : ( 'icons' , 'down' ),
        "font_name" : 'fontawesome-webfont.ttf', "font_size" : 15,
        "justify_xy" : 'LC', "x" : 0, "y" : 15
        },
    "previous_value_icon" : {
        "type" : 'icon',
        "connector" : ( 'icons' , 'left' ),
        "font_name" : 'fontawesome-webfont.ttf', "font_size" : 15,
        "justify_xy" : 'CC', "x" : 92, "y" : 10
        },
    "next_value_icon" : {
        "type" : 'icon',
        "connector" : ( 'icons' , 'right' ),
        "font_name" : 'fontawesome-webfont.ttf', "font_size" : 15,
        "justify_xy" : 'CC', "x" : 117, "y" : 10
        },
    }

# Trame de la page 'VOLUME'    
frames['VOLUME'] = {
    "volume_icon" : {
        "type" : 'icon',
        "connector" : ( 'icons' , 'speaker' ),
        "font_name" : 'fontawesome-webfont.ttf', "font_size" : 24,
        "justify_xy" : 'LC', "x" : 0, "y" : 32
        },
    "volume_value" : {
        "type" : 'text',
        "connector" : ( 'mpd_status' , 'volume' ),
        "font_name" : 'msyh.ttf', "font_size" : 50,
        "justify_xy" : 'CC', "x" : 68, "y" : 32
        },
    "volume_frame" : {
        "type" : 'rectangle',
        "xmin" : 120, "ymin" : 62,
        "xmax" : 127, "ymax" : 0
        },
    "volume_bar" : {
        "type" : 'volume_bar',
        "connector" : ( 'mpd_status' , 'volume' ),
        "value_min" : 0, "value_max" : 100,
        "xmin" : 122, "ymin" : 60,
        "xmax" : 125, "ymax" : 2
        }
    }

# Trame de la page 'SPDIF'
frames['SPDIF'] = {
    "input" : {
        "type" : 'text',
        "value" : 'SPDIF',
        "font_name" : 'msyh.ttf', "font_size" : 24,
        "justify_xy" : 'CH', "x" : 60, "y" : 0
        },
    "volume_icon" : {
        "type" : 'icon',
        "connector" : ( 'icons' , 'speaker' ),
        "font_name" : 'fontawesome-webfont.ttf', "font_size" : 18,
        "justify_xy" : 'LC', "x" : 25, "y" : 50
        },
    "volume_value" : {
        "type" : 'text',
        "connector" : ( 'mpd_status' , 'volume' ),
        "font_name" : 'msyh.ttf', "font_size" : 24,
        "justify_xy" : 'CC', "x" : 70, "y" : 50
        },
    "volume_frame" : {
        "type" : 'rectangle',
        "xmin" : 120, "ymin" : 62,
        "xmax" : 127, "ymax" : 0
        },
    "volume_bar" : {
        "type" : 'volume_bar',
        "connector" : ( 'mpd_status' , 'volume' ),
        "value_min" : 0, "value_max" : 100,
        "xmin" : 122, "ymin" : 60,
        "xmax" : 125, "ymax" : 2
        }
    }

# Trame de la page 'SAVER'
frames['SAVER'] = {
    "saver" : {
        "type" : 'saver',
        "value" : '.',
        "font_name" : 'msyh.ttf', "font_size" : 15,
        "justify_xy" : 'CC', "x" : 64, "y" : 32
        }
    }

# Trame de la page 'I2S-PLAY1'
frames['I2S-PLAY1'] = {
    "artist" : {
        "type" : 'scrolling',
        "connector" : ( 'mpd_calc' , 'i2s_play1_l1' ),
        "font_name" : 'msyh.ttf', "font_size" : 18,
        "justify_xy" : 'CH', "x" : 64, "y" : 0
        },
    "album" : {
        "type" : 'scrolling',
        "connector" : ( 'mpd_calc' , 'i2s_play1_l2' ),
        "font_name" : 'msyh.ttf', "font_size" : 18,
        "justify_xy" : 'CH', "x" : 64, "y" : 20
        },
    "volume_icon" : {
        "type" : 'icon',
        "connector" : ( 'icons' , 'speaker' ),
        "font_name" : 'fontawesome-webfont.ttf', "font_size" : 14,
        "justify_xy" : 'LB', "x" : 85, "y" : 62
        },
    "volume_value" : {
        "type" : 'text',
        "connector" : ( 'mpd_status' , 'volume' ),
        "font_name" : 'msyh.ttf', "font_size" : 15,
        "justify_xy" : 'CB', "x" : 112, "y" : 63
        },
    "elapsed_bar" : {
        "type" : 'elapsed_bar',
        "connector" : ( 'mpd_status' , 'time' ),
        "value" : 0, "value_min" : 0, "value_max" : 100,
        "xmin" : 0, "ymin" : 45,
        "xmax" : 127, "ymax" : 47
        },
    "elapsed_value" : {
        "type" : 'text',
        "connector" : ( 'mpd_calc' , 'elapsed_MS' ),
        "font_name" : 'msyh.ttf', "font_size" : 15,
        "justify_xy" : 'LB', "x" : 15, "y" : 63
        },
    "player_icon" : {
        "type" : 'icon',
        "connector" : ( 'icons' , 'player_state' ),
        "font_name" : 'fontawesome-webfont.ttf', "font_size" : 12,
        "justify_xy" : 'LC', "x" : 0, "y" : 55
        }
    }

# Trame de la page 'I2S-PLAY2'    
frames['I2S-PLAY2'] = {
    "title" : {
        "type" : 'scrolling',
        "connector" : ( 'mpd_calc' , 'i2s_play2_l1' ),
        "font_name" : 'msyh.ttf', "font_size" : 18,
        "justify_xy" : 'CH', "x" : 64, "y" : 0
        },
    "audio" : {
        "type" : 'text',
        "connector" : ( 'mpd_calc' , 'i2s_play2_l2' ),
        "font_name" : 'msyh.ttf', "font_size" : 10,
        "justify_xy" : 'CC', "x" : 64, "y" : 32
        },
    "volume_icon" : {
        "type" : 'icon',
        "connector" : ( 'icons' , 'speaker' ),
        "font_name" : 'fontawesome-webfont.ttf', "font_size" : 14,
        "justify_xy" : 'LB', "x" : 85, "y" : 62
        },
    "volume_value" : {
        "type" : 'text',
        "connector" : ( 'mpd_status' , 'volume' ),
        "font_name" : 'msyh.ttf', "font_size" : 15,
        "justify_xy" : 'CB', "x" : 112, "y" : 63
        },
    "elapsed_bar" : {
        "type" : 'elapsed_bar',
        "connector" : ( 'mpd_status' , 'time' ),
        "value" : 0, "value_min" : 0, "value_max" : 100,
        "xmin" : 0, "ymin" : 45,
        "xmax" : 127, "ymax" : 47
        },       
    "elapsed_value" : {
        "type" : 'text',
        "connector" : ( 'mpd_calc' , 'elapsed_MS' ),
        "font_name" : 'msyh.ttf', "font_size" : 15,
        "justify_xy" : 'LB', "x" : 15, "y" : 63
        },
    "player_icon" : {
        "type" : 'icon',
        "connector" : ( 'icons' , 'player_state' ),
        "font_name" : 'fontawesome-webfont.ttf', "font_size" : 12,
        "justify_xy" : 'LC', "x" : 0, "y" : 55
        }
    }
