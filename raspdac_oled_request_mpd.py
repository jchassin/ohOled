#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# AUDIOPHONICS - RASPDAC MINI - Gestion de l'écran OLED
# Classe de gestion du serveur MPD
# Fichier : raspdac_oled_request_mpd.py
# 15 Mai 2019      : Creation
# 02 Juin 2019     : Gestion du driver ES9038Q2M + ajout Menu Télécommande
# ----------------------------------------------------------------------------
# Ce fichier est utilisé par le script principal raspdac_oled_main.py
# Ce fichier doit être installé dans le même répertoire que :
#   -> raspdac_oled_main.py (script principal)
#   -> raspdac_oled_request_os (gestion des requêtes avec l'OS Linux)
#   -> raspdac_oled_screen_menu.py (gestion du MENU activé par télécommande)
#   -> raspdac_oled_screen_telecommand.py (gestion de la télécommande)
#   -> raspdac_oled_screen_display.py (affichage sur l'écran)
#   -> raspdac_oled_screen_frames.py (définition des trames des pages)
#   -> fonts : répertoire des polices de caractères utilisées pour l'affichage
# ----------------------------------------------------------------------------
'''
    Ce fichier contient la classe et les méthodes permettant de :
    -> se connecter au serveur musical MPD
    -> d'envoyer des commandes (requêtes) au serveur
    -> de récupérer les réponses du serveur
    
    Deux requêtes sont utilisées dans le cadre du RASPDAC-MINI :
    -> la requête 'status\n' qui permet d'obtenir des informations sur l'état du player
    -> la requête 'currentsong\n'  qui permet de récupérer des informations sur la piste en cours
    
    Il est à noter que selon le contexte (état 'stop' ou 'play'), le serveur MPD renvoit plus ou moins de données

    Les méthodes de ce fichier, permettent de récupérer l'ensemble des champs dans des dictionnaires
    Les données de ces dictionnaires seront ainsi disponibles pour être éventuellement affichées
'''
import socket                   # Gestion des connexions réseau

# ----------------------------------------------------------------------------
# Dictionnaire des champs renvoyés par le serveur MPD en réponse à une commande 'status\n'
# A noter que les 9 premiers champs ('volume' à 'state') sont systématiquement retournés en réponse
# Alors que les 8 champs suivants ('songid' à 'nextsongid') ne sont pas retournés quand l'état 'state' du player vaut 'stop'
# La réponse du serveur est une chaîne de caractères :
#   -> avec un couple (champ : valeur) par ligne (fin de ligne marquée par '\n')
#   -> la fin de la réponse est indiquée par la ligne 'OK'
mpd_status_ref = dict()
mpd_status_ref = {
    'volume': '0',              # -1 si contrôle désactivé, entre 0 et 100 si contrôle software, 100 si contrôle hardware
    'repeat': '0',              # à 1 si le mode 'Repeat' est actif : rejeu continu de la file ("queue")
    'random': '0',              # à 1 si le mode 'Random' est actif : sélection aléatoire des titres de la file ("queue")
    'single': '0',              # à 1 si le mode 'Single' est actif : player ne joue que le titre sélectionné
    'consume': '0',             # ?
    'playlist': '0',            # S'incrémente chaque fois qu'on charge une file ("queue")
    'playlistlength': '0',      # Nombre de pistes dans la file
    'mixrampdb': '0.000000',    # ?
    'state': 'stop',            # état du player : vaut 'stop' ou 'play' ou 'pause'
    'song': '0',                # Indicateur de la position de la piste dans la playlist (part de 0)
    'songid': '0',              # Indicateur de la position de la piste dans la playlist (part de 1)
    'time': '0:0',              # Contient 2 informations => 'elapsed:duration' => à la fois le temps écoulé (elapsed) et la durée du titre (duration) en secondes enières
    'elapsed': '0.000',         # Temps écoulé sur le titre en cours (en secondes flottantes avec une précision à la milliseconde)
    'bitrate': '0',             # Bitrate instantané exprimé en kbps (kbits/s)
    'duration': '0.000',        # Durée du titre (en secondes flottantes avec une précision à la milliseconde)
    'audio': '0:0:0',           # Informations audio sur le titre en cours (fréquence des échantillons, nombre de bits par échantillon, nombre de canaux)
    'nextsong': '0',            # Information sur la prochaine chanson de la file
    'nextsongid': '0'           # Information sur la prochaine chanson de la file
   }
   
# Dictionnaire des champs renvoyés par le serveur MPD en réponse à une commande 'currentsong\n'
mpd_currentsong_ref = dict()
mpd_currentsong_ref = {
    'file': 'no file',          # Chemin d'accès au fichier du titre en cours
    'Last-Modified': 'empty',   # Date de la dernière modification sur le fichier
    'Title': 'no title',        # Nom du titre en cours
    'Artist': 'no artist',      # Nom de l'artiste pour le titre en cours
    'Album': 'no album',        # Nom de l'album du titre en cours
    'Name': 'no name',          # Nom du stream (cas par exemple radios) 
    'Track': '0',               # Numéro du titre sur l'album
    'Genre': 'no genre',        # Genre du titre
    'Time': '0',                # Durée du titre en cours (en secondes entières)
    'duration': '0.000',        # Durée du titre en cours (en secondes flottantes avec une précision à la milliseconde)
    'Pos': '0',                 # Indicateur de la position de la piste dans la playlist (part de 0) 
    'Id': '0'                   # Indicateur de la position de la piste dans la playlist (part de 1)
    }

# ----------------------------------------------------------------------------
# Classe d'accès et d'interrogation du Serveur Musical MPD
class MpdServer() :
    # Initialisation
    def __init__(self) :
        self.host = 'localhost'         # Serveur Musical MPD intégré au Raspdac Midi (donc 'localhost')
        self.port = 6600                # Port pour accéder au serveur MPD : paramètre 'port' défini dans le fichier /etc/mpd.conf
        self.bufsize = 4096             # Taille du buffer audio : paramètre 'audio_buffer_size' défini dans le fichier /etc/mpd.conf
        
        self.socket = socket.socket(    # Construction du socket
            socket.AF_INET,             # famille d'adresses de type Internet
            socket.SOCK_STREAM )        # type du socket = TCP

        self.socket_status = 'OK'       # status du socket au serveur MPD
    
    # Connexion au serveur MPD
    def connect(self) :
        try :
            self.socket.connect((self.host, self.port))
            response = self.socket.recv(self.bufsize).decode("Utf8")
            self.socket_status = 'OK'
            return response
        except socket.error as e :
            # print('MpdServer.connect - socket error')
            # print(e)
            self.socket_status = 'KO'
            return ''
    
    # Requête 'status' au serveur MPD
    def getstatus(self) :
        command = 'status\n'
        return self.mpd_command(command)

    # Requête 'currentsong' au serveur MPD
    def getcurrentsong(self) :
        command = 'currentsong\n'
        return self.mpd_command(command)

    # Traitement de la réponse à la requête
    def mpd_command(self, command) :
        # la réponse du serveur MPD est une chaîne de caractères (voir commentaires en début de fichier)
        answer = self.request(command)

        # Extraction des champs de la réponse et sauvegarde dans un dictionnaire
        dict_answer = dict()
        lines = answer.split('\n')
        i=0
        while lines[i] != 'OK' and i < len(lines)-1 :       # La 2ième condition protège contre les réponses incomplètes (reset du player)
            fields = lines[i].split(':',1);                 # 1 seul découpage au premier ":" rencontré sur la ligne
            dict_answer[fields[0]] = fields[1].lstrip()     # supprimer les espaces à gauche et sauvegarder dans le dictionnaire
            i += 1

        # Remplissage du dictionnaire avec les champs manquants
        if command == 'status\n' :
            for key, value in mpd_status_ref.items() :
                dict_answer[key] = dict_answer.get(key, value)
        else :
            for key, value in mpd_currentsong_ref.items() :
                dict_answer[key] = dict_answer.get(key, value)
        
        return dict_answer

    # Envoi de la Requête à destination du serveur MPD
    def request(self, command) :
        try :
            self.socket.send(command.encode("Utf8"))
            response = self.socket.recv(self.bufsize).decode("Utf8")
            self.socket_status = 'OK'
            return response
        except socket.error as e:
            # print('MpdServer.request - socket error')
            # print(e)
            self.socket_status = 'KO'
            return ''


# ----------------------------------------------------------------------------
# Processing des champs à afficher dans les pages 'I2S-PLAY1' et 'I2S-PLAY2'
# Ces champs sont élaborés à partir des dictionnaires 'mpd_status' et 'mpd_song' renvoyés par le serveur MPD.
# On distingue les champs suivants :
# -> 'i2s_play1_l1' : 1ère ligne (L1) de la page 'I2S-PLAY1'
# -> 'i2s_play1_l2' : 2ème ligne (L2) de la page 'I2S-PLAY1'
# -> 'i2s_play2_l1' : 1ère ligne (L1) de la page 'I2S-PLAY2'
# -> 'i2s_play2_l2' : 2ème ligne (L2) de la page 'I2S-PLAY2'
# -> 'elapsed_MS'   : temps écoulé sur le titre en cours, formaté en 'min:sec'
#
# La valeur des 4 premiers champs dépend du contexte :
#                !----------------------!----------------------!----------------------!
#                ! Cas du titre musical ! Cas du titre musical ! Cas de la web radio  !
#                !    (avec infos)      !    (sans info)       !                      !
# !--------------!----------------------!----------------------!----------------------!
# !              !  Nom de l'artiste    !  Nom de l'artiste    !    Nom de la radio   !
# ! i2s_play1_l1 !  mpd_song['Artist']  !     extrait de       !    mpd_song['Name']  !
# !              !                      !   mpd_song['file']   ! ou mpd_song['Title'] !
# !--------------!----------------------!----------------------!----------------------!
# !              !  Nom de l'album      !  Nom de l'album      !  Emission en cours   !
# ! i2s_play1_l2 !  mpd_song['Album']   !     extrait de       !    mpd_song['Title'] !
# !              !                      !   mpd_song['file']   !        ou ''         !
# !--------------!----------------------!----------------------!----------------------!
# !              !  Nom du titre        !  Nom du titre        ! URL de la web radio  !
# ! i2s_play2_l1 !  mpd_song['Title']   !     extrait de       !    mpd_song['file']  !
# !              !                      !   mpd_song['file']   !                      !
# !--------------!----------------------!----------------------!----------------------!
# ! i2s_play2_l2 ! info audio sur titre ! info audio sur titre !  info sur le flux    !
# !              !  format / fréquence  !  format / fréquence  !  rythme en kbits/s   !
# !--------------!----------------------!----------------------!----------------------!
def mpd_data_processing(mpd_status, mpd_song) :

    # Test de l'activité du player
    if mpd_status['state'] != 'stop' and mpd_status['audio'] != '0:0:0' :
        # Cas du player actif
        if mpd_song['Artist'] != 'no artist' :
            # Cas général du titre musical (où les champs 'Artist', 'Album' et 'Title' sont donnés)
            i2s_play1_l1 = mpd_song['Artist']           # Artiste
            i2s_play1_l2 = mpd_song['Album']            # Album
            i2s_play2_l1 = mpd_song['Title']            # Titre
        elif mpd_song['Name'] != 'no name' :
            # Cas général des web radios (où le champ 'Name' donne le nom de la radio)
            i2s_play1_l1 = mpd_song['Name'].upper()     # Nom de la radio
            if mpd_song['Title'] != 'no title' :
                i2s_play1_l2 = mpd_song['Title']        # Si présente, info sur l'émission (ou le morceau) en cours
            else :
                i2s_play1_l2 = ''                       # Sinon, on n'affiche rien pour l'émission ou le titre en cours
            i2s_play2_l1 = mpd_song['file']             # URL du flux radio
        elif mpd_song['Title'] != 'no title' :
            # Cas particulier de certaines web radios (où seul le champ 'Title' est donné)
            i2s_play1_l1 = mpd_song['Title'].upper()    # Nom de la radio
            i2s_play1_l2 = ''                           # Rien n'est affiché pour l'émission ou le titre en cours
            i2s_play2_l1 = mpd_song['file']             # URL du flux radio
        else :
            # Cas du titre musical sans information
            champs = mpd_song['file'].split('/')
            i2s_play1_l1 = champs[-3]       # Artiste
            i2s_play1_l2 = champs[-2]       # Album
            i2s_play2_l1 = champs[-1]       # Titre

        # processing du champ audio
        i2s_play2_l2 = mpd_audio_processing(mpd_status['audio'], mpd_status['bitrate'], mpd_status['duration'])

        # Processing du temps écoulé sur un titre (elapsed)
        # -> conversion du champ en 'min:sec' et en secondes entières
        # -> conversion en 'hour:min:sec' si le temps écoulé est supérieur à 1h
        elapsed_calc = float(mpd_status['elapsed'])
        hour = '{:02d}'.format(int(elapsed_calc/3600)%24)
        min = '{:02d}'.format(int(elapsed_calc%3600/60))
        sec = '{:02d}'.format(int(elapsed_calc%60))
        elapsed_MS = min + ":" + sec
        if elapsed_calc >= 3600.0 : elapsed_MS = hour + ":" + elapsed_MS
        elapsed_sec = int(elapsed_calc)

        # Processing de la durée d'un titre (duration)
        # -> conversion du champ en 'min:sec' et en secondes entières
        duration_calc = float(mpd_status['duration'])
        min = '{:02d}'.format(int(duration_calc/60))
        sec = '{:02d}'.format(int(duration_calc%60))
        duration_MS = min + ":" + sec
        duration_sec = int(duration_calc)

    else :
        # Cas du player non actif (aucun titre en cours)
        i2s_play1_l1 = 'empty'
        i2s_play1_l2 = 'empty'
        i2s_play2_l1 = 'empty'
        i2s_play2_l2 = 'empty'
        elapsed_sec = '0'
        elapsed_MS = '00:00'
        duration_sec = '0'
        duration_MS = '00:00'

    # Stockage des résultats dans un dictionnaire avant renvoi
    response = {
        'i2s_play1_l1' : i2s_play1_l1,
        'i2s_play1_l2' : i2s_play1_l2,
        'i2s_play2_l1' : i2s_play2_l1,
        'i2s_play2_l2' : i2s_play2_l2,
        'elapsed_sec' : elapsed_sec, 'elapsed_MS' : elapsed_MS,
        'duration_sec' : duration_sec, 'duration_MS' : duration_MS
        }

    return response

# ----------------------------------------------------------------------------
# Processing du champ audio ('i2s_play2_l2')
# Ce champ audio est affiché en 2ème ligne de la page 'I2S-PLAY2'
# Ce champ donne des informations sur le flux audio selon le contexte:
# -> cas d'une web radio : le champ audio donne le rythme binaire en kbits/s
# -> cas d'un titre musical : le champ audio renvoie :
#       - le format (PCM ou DSD)
#       - la fréquence des échantillons
#       - le nombre de bits par échantillon (dans le cas du format PCM)
def mpd_audio_processing(champ_audio, champ_bitrate, champ_duration) :

    if champ_duration == '0.000' :
        # Cas d'un flux à durée non définie (cas des web radios)
        # La valeur du rythme binaire est alors renvoyée
        info_audio = 'stream / {freq} kbps'.format(freq=champ_bitrate)

    else :
        # cas d'un titre d'une durée finie (cas d'un morceau musical)
        # Le format (PCM ou DSD), la fréquence des échantillons et le nombre de bits par échantillons sont alors renvoyés
        audio = champ_audio.split(':')
        if len(audio) > 2:
            # cas d'un format PCM (exemple : 44100:16:2)
            info_format = "PCM"
            frequence = float(audio[0])/1000            # extraction de la fréquence et conversion en kbits/s
            if audio[0][-2] != '0' : precision = 2      # on ne garde que les chiffres non nuls après la virgule
            elif audio[0][-3] != '0' : precision = 1
            else : precision = 0
            info_freq = '{:.{prec}f}'.format(frequence, prec=precision)
            info_bit = audio[1]                         # extraction du nombre de bits par échantillon
            info_canaux = audio[2]                      # extraction du nombre de canaux audio
            info_audio = 'PCM / {freq} kHz / {bits} bits'.format(freq=info_freq, bits=info_bit)
        
        else :
            # cas d'un format DSD (exemple : dsd256:2)
            info_format = audio[0].upper()              # extraction du type de DSD : DSD64, DSD128, DSD256, DSD512 ou DSD1024
            info_freq = champ_bitrate                   # extraction du bit rate en kbits/s
            info_bit = 1                                # 1 bit par échantillon
            info_canaux = audio[1]                      # extraction du nombre de canaux audio
            info_audio = '{format} / {freq} kbps'.format(format=info_format, freq=info_freq)

    return info_audio