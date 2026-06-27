#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# AUDIOPHONICS - RASPDAC MINI - Gestion de l'écran OLED
# Gestion de la télécommande Infra-Rouge
# Fichier : raspdac_oled_telecommand.py
# 15 Mai 2019      : Creation
# 02 Juin 2019     : Gestion du driver ES9038Q2M + ajout Menu Télécommande
# ----------------------------------------------------------------------------
# Ce fichier est utilisé par le script principal raspdac_oled_main.py
# Ce fichier doit être installé dans le même répertoire que :
#   -> raspdac_oled_main.py (script principal)
#   -> raspdac_oled_request_mpd (gestion des requêtes avec le serveur MPD)
#   -> raspdac_oled_request_os (requêtes avec l'OS Linux et le pilote ALSA)
#   -> raspdac_oled_screen_menu.py (gestion du MENU activé par télécommande)
#   -> raspdac_oled_screen_display.py (affichage sur l'écran)
#   -> raspdac_oled_screen_frames.py (définition des trames des pages)
#   -> fonts : répertoire des polices de caractères utilisées pour l'affichage
# ----------------------------------------------------------------------------
import socket
import time
from raspdac_oled_request_os import shell_command
SOCKPATHS = ("/var/run/lirc/lircd", "/run/lirc/lircd")

# ----------------------------------------------------------------------------
# Gestion de la télécommande infrarouge
class InfraRedTelecommand() :
    # Initialisations
    def __init__(self) :   
        self.bufsize = 128                  # Taille du buffer de réception
        self.socket = None
        for sockpath in SOCKPATHS:
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.connect(sockpath)
                sock.setblocking(False)
            except OSError:
                try:
                    sock.close()
                except Exception:
                    pass
                continue
            self.socket = sock
            break
        self.key_time = float(time.time())  # mémorisation de l'instant de l'appui d'une touche
        self.key_quick_gap = 0.3            # intervalle de temps entre deux touches caractérisant des apppuis rapides

    # Récupération du code de touche (lorsqu'une touche est activée sur la télécommande)
    def get_key(self):
        if self.socket is None:
            return 'NO_KEY', 'LOW'
        try :
            data = self.socket.recv(self.bufsize).decode("Utf8", errors="replace")
            parts = data.split()
            if len(parts) < 3:
                return 'NO_KEY', 'LOW'
            key = parts[2]
            key_trigger = float(time.time())
            delta = key_trigger - self.key_time
            if (delta < self.key_quick_gap) :
                speed = 'HIGH'
            else : 
                speed = 'LOW'
            self.key_time = key_trigger
            return key, speed
        except OSError as e:           # pas de touche activée sur la télécommande
            return 'NO_KEY', 'LOW'

    # Action déclenchée lorsqu'une touche est activée sur la télécommande
    def action(self, key='NO_KEY', speed='LOW', menu={} ):
        cmd = ""
        # Cas où la page 'MENU' est active
        # Ici la page 'MENU' est affichée à l'écran
        # Et la télécommande permet d'afficher, de sélectionner et de modifier les paramètres du pilote ALSA
        if menu['status'] == 'ON' :
            if key == 'KEY_MENU' :          # Désactivation de la page 'MENU'
                menu['status']='OFF'
            elif key == 'KEY_DOWN' :          # Passage au "control" suivant ('MUTE' -> 'FILTER' -> 'INPUT' -> 'MUTE' -> ...)
                menu['selected_control'] += 1
                if menu['selected_control'] >= menu['controls_number'] :
                    menu['selected_control'] = 0
                menu['selected_item'] = menu['active_item'][menu['selected_control']]
            elif key == 'KEY_UP' :        # Passage au "control" précedent ('MUTE' -> 'INPUT' -> 'FILTER' -> 'MUTE' -> ...)
                if menu['selected_control'] == 0 :
                    menu['selected_control'] = menu['controls_number']
                menu['selected_control'] -= 1
                menu['selected_item'] = menu['active_item'][menu['selected_control']]
            elif key == 'KEY_LEFT' :        # Passage à l'item précédent du "control" courant
                if menu['selected_item'] == 0 :
                    menu['selected_item'] = menu['items_number'][menu['selected_control']]
                menu['selected_item'] -= 1
            elif key == 'KEY_RIGHT' :       # Passage à l'item suivant du "control" courant
                menu['selected_item'] += 1
                if menu['selected_item'] >= menu['items_number'][menu['selected_control']] : 
                    menu['selected_item']=0
            elif key == 'KEY_ENTER' :       # Validation de l'item du "control" courant et configuration du pilote ALSA
                menu['active_item'][menu['selected_control']] = menu['selected_item']
                control = menu['controls_list'][menu['selected_control']]
                value = menu['items_list'][menu['selected_control']][menu['selected_item']]
                # Commande à envoyer au pilote ALSA pour valider l'item
                cmd = ['amixer', 'sset', '-c', '0', control, value]
            else :
                pass
        # Cas où la page 'MENU' est non activée
        # Ici la télécommande permet de piloter le serveur de Media MPD (réglage du volume, sélection des plages)
        else :
            if key == "KEY_MENU" :
                menu['status']='ON'
                cmd = ""
            elif key == 'KEY_UP' :          # Augmentation du volume
                if speed == 'HIGH' :
                    cmd = "/var/www/vol.sh up 2"
                else:
                    cmd = "/var/www/vol.sh up 1"
            elif key == 'KEY_DOWN' :        # Réduction du volume
                if speed == 'HIGH' :
                    cmd = "/var/www/vol.sh dn 2"
                else:
                    cmd = "/var/www/vol.sh dn 1"
            elif key == 'KEY_LEFT' :        # Passage au titre précédent
                cmd = "/usr/bin/mpc prev"
            elif key == 'KEY_RIGHT' :       # Passage au titre suivant
                cmd = '/usr/bin/mpc next'
            elif key == 'KEY_ENTER' :       # Arrêt du player
                cmd = "/usr/bin/mpc stop"
            elif key == "KEY_PLAY" :        # Bascule entre "play" et "pause"
                cmd = "/usr/bin/mpc toggle"
            else :
                pass
                
        # envoi de commande Shell
        if cmd != "" : shell_command(cmd)
        return menu

