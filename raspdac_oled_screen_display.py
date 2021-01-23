#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# AUDIOPHONICS - RASPDAC MINI - Gestion de l'écran OLED
# Classe pour la gestion de l'affichage sur l'écran OLED
# Fichier : raspdac_oled_request_mpd.py
# 15 Mai 2019      : Creation
# 02 Juin 2019     : Gestion du driver ES9038Q2M + ajout Menu Télécommande
# ----------------------------------------------------------------------------
# Ce fichier est utilisé par le script principal raspdac_oled_main.py
# Ce fichier doit être installé dans le même répertoire que :
#   -> raspdac_oled_main.py (script principal)
#   -> raspdac_oled_request_mpd (gestion des requêtes avec le serveur MPD)
#   -> raspdac_oled_request_os (gestion des requêtes avec l'OS Linux)
#   -> raspdac_oled_screen_menu.py (gestion du MENU activé par télécommande)
#   -> raspdac_oled_screen_telecommand.py (gestion de la télécommande)
#   -> raspdac_oled_screen_frames.py (définition des trames des pages)
#   -> fonts : répertoire des polices de caractères utilisées pour l'affichage
# ----------------------------------------------------------------------------
# ============================================================================
# IMPORT (Librairies / classes / Fonctions utilisées par ce script)
# ============================================================================
from __future__ import unicode_literals     # nécessaire pour Python 2
import os

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

import RPi.GPIO as GPIO                     # Gestion du port GPIO du Raspberry Pi
from luma.core.interface.serial import spi  # Gestion des bus série de type I2C et SPI

from luma.core.render import canvas         # Gestion de l'affichage sur un écran (canvas)
from luma.oled.device import ssd1306        # Gestion de l'écran OLED SSD1309 (compatible SSD1306)

from random import randint                  # Génération de nombre entier aléatoire

from raspdac_oled_screen_frames import frames

# Caractères spéciaux pour l'affichage d'icônes avec la police "awesome" 
# ----------------------------------------------------------------------------
icons = dict()
icons['speaker'] = "\uf028"        # code Hexa 0xF028 => icône Haut-Parleur (pour le volume)
icons['wifi']    = "\uf1eb"        # code Hexa 0xF1EB => icône Wifi
icons['link']    = "\uf0e8"        # code Hexa 0xF0E8 => icône pour réseau local filaire de type LAN (Local Area Network)
icons['broken']  = "\uf127"        # code Hexa 0xF0E8 => icône pour absence de réseau local
icons['clock']   = "\uf017"        # code Hexa 0xF017 => icône horloge (clock)
# icons['play']    = "\uf001"        # code Hexa 0xF001 => icône musical de 2 croches reliées (en mode play)
icons['play']    = "\uf04b"        # code Hexa 0xF001 => icône correspondant au symbole de l'état "play" d'un player de musique
icons['pause']   = "\uf04c"        # code Hexa 0xF04C => icône correspondant au symbole de l'état "pause" d'un player de musique
icons['stop']    = "\uf04d"        # code Hexa 0xF04C => icône correspondant au symbole de l'état "stop" d'un player de musique
icons['up']      = "\uf0d8"        # code Hexa OxF0D8 => icône flèche "UP" de la télécommande
icons['down']    = "\uf0d7"        # code Hexa OxF0D7 => icône flèche "DOWN" de la télécommande
icons['left']    = "\uf0d9"        # code Hexa OxF0D9 => icône flèche "LEFT" de la télécommande
icons['right']   = "\uf0da"        # code Hexa OxF0DA => icône flèche "RIGHT" de la télécommande

# vitesse de scrolling exprimée en pixels par seconde
scrolling_speed = 30


# Classe de gestion de l'affichage sur l'écran OLED
# ----------------------------------------------------------------------------
class OledScreen() :
    def __init__(self) :
        # Dimensions de l'écran
        self.oled_width    = 128
        self.oled_height    = 64
        # Configuration Bus série SPI entre le Raspberry Pi et l'écran OLED
        serial = spi(port=0, device=0, gpio_DC=27, gpio_RST=24)
        
        # Ecran OLED piloté par le port série SPI
        # Rotation logicielle de 180° de l'écran (monté à l'envers dans le Raspdac Mini)
        self.device = ssd1306(serial, rotate=2)
        
        # Chargement des trames de pages et Construction des polices de caractères
        self.dynamic_pages = fill_frames_with_builded_fonts(frames)

    def affichage_page(self, page, connectors, reset_scrolling, loop_period) :
        # Analyse de chaque object de la page
        for key, object in self.dynamic_pages[page].items() :
            # Récupération (s'il y a lieu) du connecteur de l'objet
            if object.get('connector') != None :
                object = get_connector(object, connectors)
                
            # Justication de l'objet de type texte ou de type icône
            if  (object['type'] == 'text' or object['type'] == 'scrolling' or object['type'] == 'icon' or object['type'] == 'saver') :
                object = justify_fields(object)

            # Traitement de l'objet 'barre de volume'
            if object['type'] == 'volume_bar' :
                object = process_volume_bar(object)

            # Traitement de l'objet 'barre de temps écoulé'
            if object['type'] == 'elapsed_bar' :
                object = process_elapsed_bar(object)

            # Traitement de l'objet 'scrolling' (champ défilant)
            if object['type'] == 'scrolling' :
                object = process_scrolling(object, reset_scrolling, self.oled_width, loop_period)

            # Traitement de l'objet 'saver' (point balayant l'écran)
            if object['type'] == 'saver' :
                object = process_screen_saver(object, reset_scrolling, self.oled_width, self.oled_height)


        # Affichage à l'écran de la page
        with canvas(self.device) as draw :
            # Affichage objet par objet
            for key, object in self.dynamic_pages[page].items() :
                if object['type'] == 'icon' or object['type'] == 'text' or object['type'] == 'saver':
                    draw.text( (object['xj'], object['yj']), text=object['value'], font=object['font'], fill='white' )
                elif object['type'] == 'scrolling' :
                    draw.text( (object['xj'], object['yj']), text=object['value_scroll'], font=object['font'], fill='white' )
                elif object['type'] == 'rectangle' :
                    # Pour le rectangle, il faut tracer des lignes plutôt qu'un rectangle pour eviter d'écraser l'intérieur
                    # => remplacer draw.rectangle( ((object['xmin'], object['ymin']), (object['xmax'], object['ymax'])), outline=1, fill=0 )
                    points = (
                        (object['xmin'], object['ymin']),
                        (object['xmin'], object['ymax']),
                        (object['xmax'], object['ymax']),
                        (object['xmax'], object['ymin']),
                        (object['xmin'], object['ymin']),
                        )
                    if 'value' in object :
                        if object['value'] == True : draw.line( points, fill=1, width=1 )
                    else :
                        draw.line( points, fill=1, width=1 )
                        
                elif object['type'] == 'elapsed_bar' or object['type'] == 'volume_bar' :
                    draw.rectangle( ((object['x1'], object['y1']), (object['x2'], object['y2'])), outline=0, fill=1 )
                else : pass

# -------------------------------------------------------------------------------------------------------------------------------
# Construction d'une fonte
def make_font(name, size):
    # La variable font_path contient le chemin d'accès aux polices contenues dans le répertoire 'fonts'
    # Sachant que le répertoire 'fonts' se trouve dans le même répertoire que le script principal (__file__)
    font_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'fonts', name))
    return ImageFont.truetype(font_path, size)

# Construction des fontes utilisées par les différentes pages de l'écran OLED
def fill_frames_with_builded_fonts(frames) :
    # Boucle sur les trames des pages
    for key1, frame in frames.items() :
        # Boucle sur les objets de chaque trame
        for key2, object in frame.items() :
            if ( object.get('font_name') != None and object.get('font_name') != None) :
                    object['font'] = make_font(object['font_name'],object['font_size'])
            else :
                pass
    return frames
# -------------------------------------------------------------------------------------------------------------------------------

# Récupération du connecteur d'un objet et mise à jour de la valeur de l'objet
def get_connector(object , connectors) :
    group_data = object['connector'][0]
    id_data = object['connector'][1]
    object['value'] = connectors[group_data][id_data]
    return object

# Traitement de justification d'un objet de type texte ou icône
def justify_fields(object) :
    jx = object['justify_xy'][0]        # justification en x qui vaut 'L' pour Left, 'C' pour Center ou 'R' pour Right
    jy = object['justify_xy'][1]        # justification en y qui vaut 'H' pour High, 'C' pour Center ou 'B' pour Bottom
    x_in = object['x']
    y_in = object['y']
    width , height = object['font'].getsize(object['value'])
    offset_x, offset_y = object['font'].getoffset(object['value'])
    t=int(jx == 'R') ; u=int(jx == 'C') ; v=int(jy =='B') ; w=int(jy == 'C')
    dx = width * (2*t+1*u) ; dy = height * (2*v + 1*w)
    x_out = x_in - int(dx/2) - offset_x/2
    y_out = y_in - int(dy/2) - offset_y/2
    object.update( { "xj" : x_out, "yj" : y_out } )
    return object

# Traitement de l'objet barre de volume
def process_volume_bar(object) :
    dv = float(int(object['value'])-object['value_min'])
    dv_max = float(object['value_max']-object['value_min'])
    dy_max = float(object['ymax']-object['ymin'])
    yval = object['ymin'] + int(dv*dy_max/dv_max)
    object.update( { "x1" : object['xmin'], "y1" : object['ymin'], "x2" : object['xmax'], "y2" : yval } )
    return object

# Traitement de l'objet barre de temps écoulé
def process_elapsed_bar(object) :
    elapsed , duration = object['value'].split(':')
    if (duration != '0') :
        dx_max = float(object['xmax']-object['xmin'])
        duration = float(duration)
        elapsed = float(elapsed)
        xval = object['xmin'] + int(elapsed*dx_max/duration)
    else : xval = object['xmin']
    object.update( { "x1" : object['xmin'], "y1" : object['ymin'], "x2" : xval, "y2" : object['ymax'] } )
    return object

# Traitement de l'affichage défilant pour les champs dépassant la largeur de l'écran
def process_scrolling(object, reset_scrolling, oled_width, loop_period) :
    text = object['value']
    width, height = object['font'].getsize(text)
    if ('scrolling_xmin' in object) and ('scrolling_xmax' in object) :
        scrolling_width = object['scrolling_xmax'] - object['scrolling_xmin']
    else :
        scrolling_width = oled_width
        object.update( { "scrolling_xmin" : 0, 'scrolling_xmax' : oled_width - 1 } )
        
    if width > scrolling_width :
        string = text + ' - '
        width_period, height_period = object['font'].getsize(string)
        string += text
        if reset_scrolling == True :
            xscroll = object['scrolling_xmin']
        else :
            xscroll = object['xscroll'] - int(scrolling_speed*loop_period)
            if xscroll <= -width_period : xscroll = object['scrolling_xmin']
        object['xscroll']=xscroll
        object['xj'] = xscroll
        object['value_scroll']=string
    else :
        object['xscroll'] = object['scrolling_xmin']
        object['value_scroll'] = object['value']
    return object    

# Traitement de l'affichage de l'objet 'saver' (point balayant l'écran)
def process_screen_saver(object, reset_scrolling, oled_width, oled_height) :
    width , height = object['font'].getsize(object['value'])
    if reset_scrolling != True :
        object['xj'] = randint(0, oled_width - width)
        object['yj'] = randint(0, oled_height - height)
    return object    
        
