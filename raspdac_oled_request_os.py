#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# AUDIOPHONICS - RASPDAC MINI - Gestion de l'écran OLED
# Fonctions d'interrogation en ligne de commande (shell) du système LINUX
# Fichier : raspdac_oled_request_os.py
# 15 Mai 2019      : Creation
# 02 Juin 2019     : Gestion du driver ES9038Q2M + ajout Menu Télécommande
# ----------------------------------------------------------------------------
# Ce fichier est utilisé par le script principal raspdac_oled_main.py
# Ce fichier doit être installé dans le même répertoire que :
#   -> raspdac_oled_main.py (script principal)
#   -> raspdac_oled_request_mpd (gestion des requêtes avec le serveur MPD)
#   -> raspdac_oled_screen_menu.py (gestion du MENU activé par télécommande)
#   -> raspdac_oled_screen_telecommand.py (gestion de la télécommande)
#   -> raspdac_oled_screen_display.py (affichage sur l'écran)
#   -> raspdac_oled_screen_frames.py (définition des trames des pages)
#   -> fonts : répertoire des polices de caractères utilisées pour l'affichage
# ----------------------------------------------------------------------------
import time
from subprocess import Popen, PIPE


# ----------------------------------------------------------------------------
# Commande en ligne Shell
def shell_command(cmd) :
    result = Popen(cmd, stdout=PIPE, shell=True)
    output = result.communicate()[0].decode("Utf8")
    output = output[:-1]       # suppression du saut de ligne en fin de chaîne
    return output


# ----------------------------------------------------------------------------
# Récupération de l'adresse IP du Raspdac Mini
# Et détermination si le lien est Filaire ou en WiFi
class RaspdacIP() :
    def __init__(self) :
        self.time_ip = float(time.time())
        self.ip_adr, self.ip_type = self.get_ip()

    def get_ip(self, period=0) :
        time_now = float(time.time())
        if (time_now - self.time_ip >= period) :

            # Commande en ligne du shell pour récupérer l'adresse filaire IP
            cmd = "ifconfig eth0 | awk '/inet / {print $2}' | cut -d ':' -f2"
            ip1 = shell_command(cmd)
            
            # Commande en ligne du shell pour récupérer l'adresse WiFi
            cmd = "ifconfig wlan0 | awk '/inet / {print $2}' | cut -d ':' -f2"
            ip2 = shell_command(cmd)

            if ip1 != '' :          # cas d'une connexion filaire
                ip_adr = ip1
                ip_type = 'link'
            elif ip2 != '' :        # cas d'une connexion wifi
                ip_adr = ip2
                ip_type = 'wifi'
            else :                  # pas de connexion
                ip_adr = '127.0.0.1'    # Marqueur d'une absence de connexion
                ip_type = 'broken'

            self.ip_adr = ip_adr
            self.ip_type = ip_type
            self.time_ip = time_now

            # delta = float(time.time()) - time_now
            # print("get_ip : ",delta)

        return self.ip_adr, self.ip_type