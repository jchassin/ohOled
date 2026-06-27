# ohOled — version modernisée Debian Trixie

Pilotage de l’écran OLED du Raspdac Mini / Audiophonics.

## Installation recommandée sur Debian Trixie / Raspberry Pi OS récent

```bash
sudo apt update
sudo apt install -y python3 python3-luma.oled python3-pil python3-rpi.gpio \
  python3-lgpio lirc mpc alsa-utils iproute2

sudo install -d /opt/ohOled
sudo cp -a . /opt/ohOled/
sudo cp ohOled.service /etc/systemd/system/ohOled.service
sudo systemctl daemon-reload
sudo systemctl enable --now ohOled.service
```

Ajoutez l’utilisateur du service aux groupes matériel si nécessaire :

```bash
sudo usermod -a -G i2c,spi,gpio $USER
```

## Changements de modernisation

- Shebangs passés à `python3`.
- Suppression des caches `__pycache__` et du dossier `.git` dans l’archive livrée.
- Remplacement de `ifconfig` par `ip -4 addr` (`iproute2`, standard sur Trixie).
- Compatibilité Pillow récent : remplacement de `getsize/getoffset` par `getbbox`.
- Parsing MPD rendu plus robuste, suppression des `print()` de debug.
- Parsing ALSA rendu moins dépendant des numéros de lignes de `amixer -c 0`.
- Service systemd rendu générique pour `/opt/ohOled`, logs dans le journal.
- LIRC accepte `/var/run/lirc/lircd` et `/run/lirc/lircd` et ne bloque pas si la télécommande est absente.

## Test rapide

```bash
python3 -m compileall .
systemctl status ohOled.service
journalctl -u ohOled.service -f
```

Debian Trixie empaquette `python3-luma.oled` en version 3.10.0-1, donc l’installation via `apt` reste cohérente avec la distribution.
