#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# AUDIOPHONICS - RASPDAC MINI - Gestion de l'écran OLED
# Gestion de la page "MENU" piloté par la télécommande Infra-Rouge
# Fichier : raspdac_oled_screen_menu.py
# 15 Mai 2019      : Creation
# 02 Juin 2019     : Gestion du driver ES9038Q2M + ajout Menu Télécommande
# ----------------------------------------------------------------------------
# Ce fichier est utilisé par le script principal raspdac_oled_main.py
# Ce fichier doit être installé dans le même répertoire que :
#   -> raspdac_oled_main.py (script principal)
#   -> raspdac_oled_request_mpd (gestion des requêtes avec le serveur MPD)
#   -> raspdac_oled_request_os (gestion des requêtes avec l'OS Linux)
#   -> raspdac_oled_screen_display.py (affichage sur l'écran)
#   -> raspdac_oled_screen_frames.py (définition des trames des pages)
#   -> fonts : répertoire des polices de caractères utilisées pour l'affichage
# ----------------------------------------------------------------------------
import time
from raspdac_oled_request_os import shell_command

# -------------------------------------------------------------------------------------------------------------------------------
# Champs adressables par le pilote ALSA pour la carte son du Raspdac Mini (Audiophonics ESS9038Q2M)
controls_list = ['MUTE', 'FILTER', 'INPUT']

# Mots clefs pour la commande shell de configuration du pilote ALSA
shell_controls_list = [
    'Digital',                  # mot clef pour mettre en 'mute'        -> exemple : amixer sset -c 0 'Digital' 'mute'
    'FIR Filter Type',          # mot clef pour sélectionner un filtre  -> exemple : amixer sset -c 0 'FIR Filter Type' 'brick wall'
    'I2S/SPDIF Select' ]        # mot clef pour sélectionner une entrée -> exemple : amixer sset -c 0 'I2S/SPDIF Select' 'I2S'

# liste des items possibles pour le champ 'MUTE'
mute_list = [
    'unmute',
    'mute' ]

# liste des items possibles pour le champ 'FILTER'
filter_list = [
    'brick wall',
    'corrected minimum phase fast',
    'minimum phase slow',
    'minimum phase fast',
    'linear phase slow',
    'linear phase fast',
    'apodizing fast' ]

# liste des items possibles pour le champ 'INPUT'
input_list = [
    'I2S',
    'SPDIF' ]

# Commentaires affichés dans la page 'MENU' selon le champ et l'item sélectionnés
comments_list = { 
    'MUTE' : [
        '0 : set mute to OFF',
        '1 : set mute to ON' ],
    'FILTER' : [
        '0 : brick wall',
        '1 : corrected minimum phase fast',
        '2 : minimum phase slow',
        '3 : minimum phase fast',
        '4 : linear phase slow',
        '5 : linear phase fast',
        '6 : apodizing fast' ],
    'INPUT' : [
        '0 : set input to I2S',
        '1 : set input to SPDIF' ]
    }

# -------------------------------------------------------------------------------------------------------------------------------
# Classe de gestion de la page MENU
class PageMenu() :
    # initialisation
    def __init__(self) :   
        # Dictionnaire contenant les informations nécessaires à la télécommande pour la gestion de la page 'MENU'
        self.info = dict()
        self.info = {
            'status' : 'OFF',                           # Page Menu non active
            'selected_control' : 0,                     # "control" sélectionné = 0 pour 'MUTE'  (1 : 'FILTER' , 2 : 'INPUT')
            'controls_number'  : len(controls_list),    # Nombre de "controls" = 3 ('MUTE', 'FILTER' et 'INPUT')
            'selected_item' : 0,                        # Si "control" = 'MUTE'   => 0 : 'unmute' , 1 : 'mute'
                                                        # Si "control" = 'INPUT'  => 0 : 'I2S' , 1 : 'SPDIF'
                                                        # Si "control" = 'FILTER' => 0 à 6 selon le filtre FIR sélectionné
            'items_number' : [len(mute_list), len(filter_list), len(input_list)],
            'active_item'  : [0, 0, 0],                 # 'MUTE' : 0 pour 'unmute', 'FILTER' : 0 pour 'Brick Wall', 'INPUT' : 0 pour 'I2S' 
            'controls_list' : shell_controls_list,      # Mots clefs pour la commande shell de configuration du pilote ALSA
            'items_list' : [mute_list, filter_list, input_list]
            }

    # Mise à jour du dictionnaire 'self.info'
    # -> Dictionnaire utile à la télécommande pour la gestion de la page 'MENU'
    # -> Mis à jour à partir des informations issues du pilote ALSA ('mixer_config')
    def update_menu_info(self, mixer_config) :
        self.info['active_item'][0] = mixer_config['MUTE']['index_Item0']
        self.info['active_item'][1] = mixer_config['FILTER']['index_Item0']
        self.info['active_item'][2] = mixer_config['INPUT']['index_Item0']
        return self.info

    # Construction du dictionnaire 'menu_screen'
    # -> Dictionnaire utile pour l'affichage de la page 'MENU'
    def update_menu_screen(self) :
        control_str = controls_list[self.info['selected_control']]
        item = self.info['selected_item']
        menu_screen = dict()
        menu_screen = {
            'state' : self.info['status'],
            'menu_control' : control_str,
            'menu_item' : str(item),
            'flag_active_item' : ( self.info['selected_item'] == self.info['active_item'][self.info['selected_control']] ),
            'menu_txt' : comments_list[control_str][item]
            }
        return menu_screen

 
# ----------------------------------------------------------------------------
# Gestion du mixer ALSA
# -> permet de gérer le pilote de la carte DAC (ES-9038-Q2M)
# -> sauvegarde des états du pilote dans le dictionnaire 'self.config'
class AlsaMixer() :
    def __init__(self) :
        self.config = {
            'MUTE' :    { 'Control' : shell_controls_list[0],   'Items' : mute_list,    'Item0' : '',   'index_Item0' : 0,  'Items_number' : len(mute_list) },
            'FILTER' :  { 'Control' : shell_controls_list[1],   'Items' : filter_list,  'Item0' : '',   'index_Item0' : 0,  'Items_number' : len(filter_list) },
            'INPUT' :   { 'Control' : shell_controls_list[2],   'Items' : input_list,   'Item0' : '',   'index_Item0' : 0,  'Items_number' : len(input_list) }
            }
        # Initialisation du control 'MUTE' (nécessaire pour contourner bug AlsaMixer)
        cmd = "amixer sset -c 0 '{control}' '{value}'".format(control='Digital',value='unmute')
        shell_command(cmd)
        
        # Lecture et sauvegarde de la configuration du pilote ALSA (pour la carte ES9038Q2M)
        self.time_mixer = float(time.time())
        self.getconfig()

    # Interrogation par commande shell du pilote ALSA pour récupérer les informations du driver de la carte ES9038Q2M
    def getconfig(self, period=0) :
        time_now = float(time.time())
        if (time_now - self.time_mixer >= period) :
            cmd = "amixer -c 0"
            response = shell_command(cmd)
            lines = response.split('\n')

            # récupération de l'entrée ('INPUT')
            input = lines[3].split("'")[1]
            self.config['INPUT']['Item0'] = input
            self.config['INPUT']['index_Item0'] = self.config['INPUT']['Items'].index(input)

            # récupération de l'état du 'mute' ('MUTE')
            words = lines[8].split("[")
            sound = words[3][:-1]
            if sound == 'on' :              # sortie son activée
                mute_status = 'unmute'
            else :                          # sortie son désactivée
                mute_status = 'mute'
            self.config['MUTE']['Item0'] = mute_status
            self.config['MUTE']['index_Item0'] = self.config['MUTE']['Items'].index(mute_status)

            # récupération du filtre FIR ('FILTER')
            filter = lines[12].split("'")[1]
            self.config['FILTER']['Item0'] = filter
            self.config['FILTER']['index_Item0'] = self.config['FILTER']['Items'].index(filter)

            self.time_mixer = time_now

            # delta = float(time.time()) - time_now
            # print("getmixer : ",delta)
            
        return self.config

    # Méthode permettant de récupérer un paramètre du pilote ALSA sans passer par une commande Shell
    # -> utile pour optimiser le temps d'éxécution
    # -> interrogation du dictionnaire 'self.config' pour récupérer la valeur active (Item0) d'un champ donné (mixer_control)
    # -> 'mixer_control' à choisir parmi 'MUTE' ou 'INPUT' ou 'FILTER'
    def getcontrol(self, mixer_control) :
        active_value = self.config[mixer_control]['Item0']
        # active_index = self.config[mixer_control]['Items'].index(active_value)
        return active_value

    '''
    ANNEXES (pour info) :
    # Commande en ligne du shell : interrogation du driver de la carte audio pour récupérer l'entrée active
    cmd = "amixer sget -c 0 'I2S/SPDIF Select' | grep Item0: | awk -F\"'\" '{print $2}'"
    
    # Commande en ligne du shell : interrogation du driver de la carte audio pour récupérer l'état du champ "MUTE"
    cmd = "amixer sget -c 0 'Digital' | grep Mono: | awk -F[ '{print $4}' | cut -d ']' -f1"
    
    # Commande en ligne du shell : interrogation du driver de la carte audio pour récupérer le filtre FIR actif
    cmd = "amixer sget -c 0 'FIR Filter Type' | grep Item0: | awk -F\"'\" '{print $2}'"
    '''