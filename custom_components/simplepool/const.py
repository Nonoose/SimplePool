"""Constantes de l'intégration SimplePool."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "simplepool"
VERSION: Final = "0.1.4"  # garder synchronisé avec manifest.json

CONF_PUMP: Final = "pump_entity"
CONF_WATER: Final = "water_temp_entity"
CONF_AIR: Final = "air_temp_entity"

# Modes (switch)
MODE_PROGRAMMATION: Final = "programmation"
MODE_HORS_GEL: Final = "hors_gel"
MODE_BOOST: Final = "boost"

# Plages (select)
PLAGE_1_DEBUT: Final = "plage_1_debut"
PLAGE_1_DUREE: Final = "plage_1_duree"
PLAGE_2_DEBUT: Final = "plage_2_debut"
PLAGE_2_DUREE: Final = "plage_2_duree"

# Réglages (number)
NUM_VOLUME: Final = "volume"
NUM_DEBIT: Final = "debit_pompe"
NUM_BOOST_DUREE: Final = "boost_duree"
NUM_SEUIL_GEL: Final = "seuil_hors_gel"

HEURES: Final = [f"{h:02d}h{m:02d}" for h in range(24) for m in (0, 30)]
DUREES: Final = [f"{h}h{m:02d}" for h in range(13) for m in (0, 30) if not (h == 12 and m == 30)]

DEFAULT_PLAGES: Final = {
    PLAGE_1_DEBUT: "08h00",
    PLAGE_1_DUREE: "0h00",
    PLAGE_2_DEBUT: "14h00",
    PLAGE_2_DUREE: "0h00",
}

# clé: (nom, icône, min, max, pas, unité, défaut)
NUMBERS: Final = {
    NUM_VOLUME: ("Volume", "mdi:pool", 5, 150, 1, "m³", 40),
    NUM_DEBIT: ("Débit pompe", "mdi:pump", 1, 40, 0.5, "m³/h", 10),
    NUM_BOOST_DUREE: ("Durée Boost", "mdi:rocket-launch", 0.5, 12, 0.5, "h", 4),
    NUM_SEUIL_GEL: ("Seuil hors gel", "mdi:snowflake-thermometer", 0, 5, 0.5, "°C", 1),
}

SIGNAL_UPDATE: Final = f"{DOMAIN}_update"

# Carte Lovelace embarquée
CARD_FILENAME: Final = "simplepool-card.js"
CARD_URL: Final = f"/{DOMAIN}/{CARD_FILENAME}"
