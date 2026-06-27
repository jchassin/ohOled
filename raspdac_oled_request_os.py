#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fonctions d’interrogation du système Linux pour ohOled.

Version modernisée pour Debian Trixie : évite ifconfig/net-tools,
limite l’usage de shell=True et retourne des chaînes propres.
"""
import shlex
import subprocess
import time
from typing import Iterable, Sequence


def shell_command(cmd: str | Sequence[str], timeout: float = 5.0) -> str:
    """Exécute une commande et retourne stdout sans saut de ligne final.

    Les appels historiques passaient une chaîne shell. On les conserve pour
    compatibilité, mais les nouvelles commandes peuvent passer une liste.
    """
    if isinstance(cmd, str):
        args = cmd
        use_shell = True
    else:
        args = list(cmd)
        use_shell = False
    try:
        result = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=use_shell,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.rstrip("\n")


def _ipv4_for_interface(interface: str) -> str:
    """Retourne l’adresse IPv4 d’une interface via la commande ip(8)."""
    output = shell_command(["/usr/sbin/ip", "-4", "-o", "addr", "show", "dev", interface])
    if not output:
        output = shell_command(["/bin/ip", "-4", "-o", "addr", "show", "dev", interface])
    for line in output.splitlines():
        parts = line.split()
        if "inet" in parts:
            try:
                return parts[parts.index("inet") + 1].split("/", 1)[0]
            except (ValueError, IndexError):
                continue
    return ""


class RaspdacIP:
    def __init__(self):
        self.time_ip = 0.0
        self.ip_adr = "127.0.0.1"
        self.ip_type = "broken"
        self.get_ip()

    def get_ip(self, period: float = 0):
        time_now = time.monotonic()
        if time_now - self.time_ip >= period:
            ip1 = _ipv4_for_interface("eth0")
            ip2 = _ipv4_for_interface("wlan0")

            if ip1:
                self.ip_adr = ip1
                self.ip_type = "link"
            elif ip2:
                self.ip_adr = ip2
                self.ip_type = "wifi"
            else:
                self.ip_adr = "127.0.0.1"
                self.ip_type = "broken"
            self.time_ip = time_now

        return self.ip_adr, self.ip_type
