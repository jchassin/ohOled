#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# AUDIOPHONICS - RASPDAC MINI - Gestion de l'écran OLED
# Script principal pour la distribution RuneAudio
# Fichier : raspdac_oled_main.py
# 15 Mai 2019      : Creation
# 02 Juin 2019     : Gestion du driver ES9038Q2M + ajout Menu Télécommande
# ----------------------------------------------------------------------------
# Ce script doit être installé dans le même répertoire que :
#   -> raspdac_oled_request_mpd (gestion des requêtes avec le serveur MPD)
#   -> raspdac_oled_request_os (requêtes avec l'OS Linux et le pilote ALSA)
#   -> raspdac_oled_screen_menu.py (gestion du MENU activé par télécommande)
#   -> raspdac_oled_screen_telecommand.py (gestion de la télécommande)
#   -> raspdac_oled_screen_display.py (affichage sur l'écran)
#   -> raspdac_oled_screen_frames.py (définition des trames des pages)
#   -> fonts : répertoire des polices de caractères utilisées pour l'affichage
# ----------------------------------------------------------------------------
"""
    Script de gestion de l'ecran OLED pour le Raspdac Mini
    ------------------------------------------------------
    
    Schéma général :
    
    <---------------------- RASPDAC MINI ------------------------------>
    
    <-------- RASPBERRY Pi 3B+ --------->          <- CARTE -> < ECRAN >
                                                       DAC

                 !=========!   !--------!   !---!     !---!     !---!
                 !         !   !        !   ! c !     !   !     ! E !
                 ! Script  !   !   OS   !   ! o ! SPI !   !     ! C !
                 ! Python  !<->!  LINUX !-->! n !---->!-->!---->! R !
                 !         !   !        !   ! n !     ! C !     ! A !
                 !         !   !        !   ! e !     ! A !     ! N !
                 !=========!   !--------!   ! c !     ! R !     !---!
                     /|\          /|\       ! t !     ! T !   
                      |            |        ! e !     ! E !
                     \|/          \|/       ! u !     !   !
    !-------!    !---------!   !--------!   ! r !     ! D !
    !       !    ! Serveur !   !        !   !   !     ! A !
    ! RUNE  !    !   MPD   !   ! Pilote !   ! G ! I2S ! C !    Sorties
    ! AUDIO !<-->!  Music  !-->!  ALSA  !-->! P !---->!   !----> RCA
    !       !    !  Player !   !        !   ! I !     !   !  Analogiques
    !       !    !  Daemon !   !        !   ! O !  |->!   !
    !-------!    !---------!   !--------!   !---!  |  !---!
                                                   |
                                                   |---< Entrée SPDIF

    Ce script gère l'affichage sur l'écran OLED du produit Raspdac Mini.
    Il a été développé pour s'interfacer avec RuneAudio.

    Le fonctionnement est basé sur les principes suivants :
    -> pas de communication directe entre le script et RuneAudio
    -> Le script interroge le serveur musical (MPD) pour obtenir des
       informations sur le morceau joué :
            -> titre du morceau, titre de l'album, nom de l'artiste
            -> durée totale et temps écoulé pour ce morceau
            -> Format Audio (PCM ou DSD)
            -> fréquence d'échantillonnage, nbre de bits par échantillon
            -> niveau du volume
    -> Le script interroge le pilote ALSA pour 
            -> déterminer l'entrée audio utilisée par la carte DAC
               (entrée I2S ou entrée SPDIF)
       L'interrogation du pilote ALSA se fait avec une ligne de commande
       via le système d'exploitation (OS : Operating System)
    -> Le script récupère l'adresse IP locale (filaire ou wifi)
       du Raspdac Mini en interrogeant l'OS
    -> L'affichage des informations se fait sur plusieurs pages qui
       sont appelées selon le contexte :
            -> Page INIT : affichage du fabriquant au démarrage
            -> Page IP : affichage de l'adresse IP (WiFi ou Filaire)
            -> Page SPDIF : affichage "SPDIF" lorsque l'entrée
                            externe "SPDIF" est sélectionnée
            Quand l'entrée I2S est sélectionnée, alternance entre :
            -> Page I2S-PLAY1 : Affichage Artiste + Album 
            -> Page I2S-PLAY2 : Affichage Titre + Freq. Echantillonnage
    -> Les pages ci-dessus peuvent être détournées temporairement
            -> Page VOLUME : affichage du volume quand il est modifié
            -> Page SAVER : affichage après une période d'inactivité
    -> L'appui de la touche 'MENU' de la télécommande infrarouge permet
       d'activer une page 'MENU' permettant de configurer le pilote ALSA
"""
# ============================================================================
# IMPORT (Librairies / classes / Fonctions utilisées par ce script)
# ============================================================================
import sys
import os
import time
from datetime import datetime

from raspdac_oled_request_os import RaspdacIP

from raspdac_oled_request_mpd import MpdServer
from raspdac_oled_request_mpd import mpd_data_processing

from raspdac_oled_screen_menu import PageMenu
from raspdac_oled_screen_menu import AlsaMixer

from raspdac_oled_telecommand import InfraRedTelecommand

from raspdac_oled_screen_display import OledScreen
from raspdac_oled_screen_display import icons

# ============================================================================
# INITIALISATIONS
# ============================================================================

# Valeurs des périodes d'affichage (en secondes entières)
page_duration = dict()
page_duration['INIT'] = 10      # Durée d'affichage de la page 'INIT' à la mise sous tension
page_duration['IP-INIT'] = 10   # Durée d'affichage de la page 'IP' à la mise sous tension
page_duration['I2S-PLAY1'] = 15 # Durée d'affichage la page 'I2S-PLAY1' avant de basculer sur la page 'I2S-PLAY2'
page_duration['I2S-PLAY2'] = 10 # Durée d'affichage la page 'I2S-PLAY2' avant de basculer sur la page 'I2S-PLAY1'
page_duration['VOLUME'] = 4     # Durée d'affichage de la page 'VOLUME' en cas de changement du volume
page_inactivity = 240           # Durée d'inactivité avant de basculer sur la page 'SAVER'

# Rythme d'interrogation (en secondes)
IP_PERIOD = 5                   # Rythme d'interrogation (en secondes) pour récupérer l'adresse IP du Raspdac Mini
MIXER_PERIOD = 1                # Rythme d'interrogation (en secondes) du pilote ALSA 
                                # -> permet de récupérer l'entrée sélectionnée (I2S ou SPDIF), le status du "Mute" et le Filtre FIR sélectionné

# Classe pour la machine d'état du séquenceur de la boucle principale
class StateMachine() :
    # Initialisation de la machine d'état
    def __init__(self) :
        self.state = 'INIT'             # Etat du sequenceur (INIT ou IP ou SPDIF ou I2S-PLAY ou SAVER ou MENU)
        self.timestate = 0              # Datation du changement d'état
        self.page2display = 'INIT'      # Page à afficher
        self.refresh = True             # flag indiquant s'il y a lieu de rafraîchir la page

    # Initialisation d'un état du séquenceur
    def set(self, state='INIT', time=0, page2display='', refresh=True, resetscrolling=True) :
        self.state = state
        self.timestate = time
        if (page2display != '') : self.page2display = page2display
        else : self.page2display = state
        self.refresh = refresh
        self.resetscrolling = resetscrolling
        return

    # Maintien de l'état du séquenceur
    def hold(self, refresh=False, resetscrolling=False) : 
        self.refresh = refresh
        self.resetscrolling = resetscrolling
        return

# Classe pour asservir la durée de la boucle principale à 0.2s (soit 5 passages dans la boucle par seconde)
class LoopPeriod() :
    def __init__(self) :
        self.loop_time = float(time.time())
        self.loop_period_target = 0.2       # Durée cible exprimée en seconde pour 1 passage dans la boucle principale

    # Prise du temps en début de boucle
    def begin(self) :
        self.loop_time = float(time.time())
    
    # Asservissement en fin de boucle
    def adjust(self) :
        loop_end = float(time.time())
        loop_period = (loop_end - self.loop_time)
        loop_sleep = self.loop_period_target - loop_period
        # print("loop_sleep =",loop_sleep)
        if loop_sleep < 0.0 :
            loop_sleep = 0.0
        time.sleep(loop_sleep)

# ============================================================================
# PROGRAMME PRINCIPAL
# ============================================================================
try:

    # Initialisations au boot du Raspdac Mini
    screen = OledScreen()                   # initialisation de l'écran OLED du Raspdac Mini
    loop_period = LoopPeriod()              # initialisation du contrôle de la durée de la boucle principale
    raspdac = RaspdacIP()                   # initialisation de l'adresse IP du Raspdac Mini
    mixer = AlsaMixer()                     # initialisation du mixer ALSA
    menu = PageMenu()                       # initialisation du menu activé par la télécommande IR
    telecommand = InfraRedTelecommand()     # initialisation télécommande infra-rouge
    mixer_config = dict()                   # Dictionnaire contenant les paramètres issus du mixer ALSA
    menu_screen = dict()                    # Dictionnaire contenant les paramètres affichés dans la page 'MENU'
    mpd_server_link = 'KO'                  # initialisation de l'indicateur de l'état de la connexion avec le serveur MPD
    dac_input = mixer.getcontrol('INPUT')   # lecture de l'entrée sélectionnée sur la carte DAC
    first_loop = True                       # indicateur de premier passage dans la boucle principale

    # Boucle principale parcourue toutes les 0.2 secondes
    # (tant qu'il n'y a pas d'erreur !)
    while True:
        loop_period.begin()                 # Prise de temps en début de boucle (utile pour asservir la durée de la boucle principale)

        # A) RECUPERATION DES INFORMATIONS A AFFICHER
        #---------------------------------------------------------------------
        # Informations Temps, Heure
        time_sec = int(time.time())                             # Récupération du temps (en secondes)
        hms = "{time:%H:%M:%S}".format(time=datetime.now())     # Récupération de l'heure au format [HH:MM:SS]

        # Récupération de l'adresse IP et du type de connexion (Filaire ou Wifi) du Raspdac-Mini
        ip_adr , ip_type = raspdac.get_ip(period=IP_PERIOD)     # Interrogation à une période définie par "IP_PERIOD" (en secondes)
        
        # Gestion de la télécommande
        key, speed = telecommand.get_key()                      # Récupération touche (si appui)
        if (key != 'NO_KEY') :
            menu.info = telecommand.action(key=key, speed=speed, menu=menu.info)

        # Interrogation du mixer ALSA pour récupérer les informations de la carte DAC :
        # -> entrée sélectionnée (I2S ou SPDIF), état du "Mute" (actif ou inactif), Filtre sélectionné
        if (menu.info['status'] == 'ON' and key == 'KEY_ENTER') :
            mixer_config = mixer.getconfig()                    # Interrogation forcée suite à modification via la télécommande
        else :
            mixer_config = mixer.getconfig(period=MIXER_PERIOD) # Interrogation à une période définie par "MIXER_PERIOD" (en secondes)
               
        # Mise à jour des informations nécessaires à la page MENU
        menu.update_menu_info(mixer_config)                     # informations nécessaires pour la gestion de la télécommande
        menu_screen = menu.update_menu_screen()                 # informations nécessaires pour l'affichage de la page 'MENU'

        # Récupération de l'entrée de la carte DAC (I2S ou SPDIF)
        dac_input_old = dac_input
        dac_input = mixer.getcontrol('INPUT')
        
        # Création / Vérification de l'état du socket avec le serveur MPD    
        # -> à la mise sous tension (first loop)
        # -> ou lorsque RuneAudio réinitialise le serveur MPD ("broken pipe")
        while (mpd_server_link == 'KO') :
            mpd = MpdServer()           # Création d'un socket client    
            mpd.connect()               # Activation de la connexion
            mpd_server_link = mpd.socket_status
            if (first_loop != True) : time.sleep(2)
                    
        # Informations renvoyées par le serveur MPD
        mpd_status = mpd.getstatus()    # sauvegarde de la réponse à une requête 'status'
       


        mpd_song = mpd.getcurrentsong() # sauvegarde de la réponse à une requête 'currentsong'

        # Traitement (formatage) des données pour l'affichage
        icons['ip_type'] = icons[ip_type]                       # icône dynamique en fonction du type d'accès (filaire ou WiFi)
        icons['player_state'] = icons[mpd_status['state']]      # icône dynamqiue en fonction de l'état du player ('stop', 'play' ou 'pause')
        mpd_calc = mpd_data_processing(mpd_status, mpd_song)    # Formatage des champs à afficher dans les pages 'I2S-PLAY1' et 'I2S-PLAY2'
        

        # Regroupement des informations dans un dictionnaire de connecteurs (champs accessibles pour l'affichage)
        os_info = { 'hms' : hms,  'ip' : ip_adr }
        connectors = { 'icons': icons , 'info' : os_info , 'menu' : menu_screen, 'mpd_status' : mpd_status, 'mpd_song' : mpd_song, 'mpd_calc' : mpd_calc }

        
        # B) SEQUENCEUR DE SELECTION DES PAGES A AFFICHER
        #---------------------------------------------------------------------

        # La page 'INIT'
        # -> maintenue pendant quelques seconde avant de passer à la page 'IP'
        if (first_loop) : 
            sequencer = StateMachine()
            sequencer.set(state='INIT',time=time_sec)
        elif (sequencer.state == 'INIT' and (time_sec - sequencer.timestate) < page_duration['INIT']) :
            sequencer.hold()

        # La page 'IP' de démarrage
        # -> maintenue pendant quelques secondes avant de passer à la suite
        elif (sequencer.state == 'INIT') :
            sequencer.set(state='IP-INIT', page2display='IP', time=time_sec)
        elif (sequencer.state == 'IP-INIT' and (time_sec - sequencer.timestate) < page_duration['IP-INIT']) :
            sequencer.hold( refresh=(time_sec != time_sec_old) )    # rafraîchissement de la page toutes les secondes

        # La page 'VOLUME'
        # -> activée si le volume est modifié et reste affichée quelques secondes
        elif (mpd_status['volume'] != current_volume) :
            sequencer.set(state='VOLUME',time=time_sec)
        elif (sequencer.state == 'VOLUME' and (time_sec - sequencer.timestate) < page_duration['VOLUME']) :
            sequencer.hold()
  
        # La page 'SAVER'
        # -> activée au bout d'une période d'inactivité
        # -> maintenue tant que les entrées I2S et SPDIF ne sont pas commutées
        # -> et tant que le player est à l'arrêt, si l'entrée I2S est active
        elif (time_sec - sequencer.timestate >= page_inactivity) and (dac_input == dac_input_old) and \
             ( (dac_input != 'I2S') or (mpd_status['state'] == 'stop') ) :    
            if (sequencer.state != 'SAVER') :
                sequencer.set(state='SAVER', time=sequencer.timestate)  # on conserve la datation du changement d'état précédent
            else :
                sequencer.hold( refresh=(time_sec != time_sec_old) )    # rafraîchissement de la page toutes les secondes

        # La page 'MENU'
        # -> activée /désactivée lorsqu'on appuie sur la touche 'MENU' de la télécommande Infra-Rouge
        elif (menu_screen['state'] == 'ON') :
            if (sequencer.state != 'MENU') :
                sequencer.set(state='MENU',time=time_sec)
            else :
                sequencer.timestate = time_sec      # empêche l'activation de la page 'SAVER' quand on est dans la page 'MENU'
                sequencer.hold(refresh=True)

        # La page 'SPDIF'
        # -> maintenue tant que la carte DAC est sur l'entrée 'SPDIF'
        elif (dac_input == 'SPDIF') :
            if (sequencer.state != 'SPDIF') :
                sequencer.set(state='SPDIF',time=time_sec)
            else :
                sequencer.hold()

        # La page 'IP'
        # -> maintenue tant que l'entrée de la carte DAC est sur I2S et que le player est à l'arrêt
        elif (mpd_status['state'] == 'stop') and (time_sec - sequencer.timestate < page_inactivity) :
            if (sequencer.state != 'IP') :
                sequencer.set(state='IP',time=time_sec)
            else :
                sequencer.hold( refresh=(time_sec != time_sec_old) )

        
        # Les pages 'I2S-PLAY'
        # -> maintenues tant que la carte DAC est sur l'entrée 'I2S' et que le player n'est pas à l'arrêt
        elif (time_sec - sequencer.timestate < page_inactivity) or (sequencer.state == 'SAVER' and mpd_status['state'] != 'stop') :
            if (sequencer.state != 'I2S-PLAY') :
                sequencer.set(state='I2S-PLAY', time=time_sec, page2display='I2S-PLAY1')
                time_page_toggle = time_sec
            else :    
                if mpd_status['state'] != 'stop' : sequencer.timestate = time_sec
                # Sélection en alternance des pages 'I2S-PLAY1' et 'I2S-PLAY2'
                cycle = page_duration['I2S-PLAY1'] + page_duration['I2S-PLAY2']
                play1_period = ( (time_sec - time_page_toggle) % cycle < page_duration['I2S-PLAY1'] )
                if (play1_period == True) :
                    sequencer.resetscrolling = (sequencer.page2display != 'I2S-PLAY1')
                    sequencer.page2display = 'I2S-PLAY1'
                else :
                    sequencer.resetscrolling = (sequencer.page2display != 'I2S-PLAY2')
                    sequencer.page2display = 'I2S-PLAY2'
                # Rafraîchissement continu des pages 'I2S-PLAY'
                sequencer.refresh = True
        else :
            pass

        # Sortie du séquenceur
        current_volume = mpd_status['volume']
        time_sec_old = time_sec
        first_loop = False

        # D) AFFICHAGE DE LA PAGE
        #---------------------------------------------------------------------
        if sequencer.refresh == True :
            screen.affichage_page(sequencer.page2display, connectors, sequencer.resetscrolling, loop_period.loop_period_target)

        # Fin de l'itération
        current_volume = mpd_status['volume']       # mémorisation de la valeur du volume

        first_loop = False
        mpd_server_link = mpd.socket_status

        connectors.clear()                          # RAZ du dictionnaire des connecteurs
        loop_period.adjust()

# Sortie de la boucle principale en cas d'erreur            
except Exception as e:
    raise
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print('Exception - Main Module')
    print(exc_type, fname, exc_tb.tb_lineno)



