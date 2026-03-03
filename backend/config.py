# GTFS CSV folder (relative to backend or absolute path)
# Point to the csvs folder (parent project or backend/csvs)
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
# Fallback order: ../csvs (parent of metrom-nerede), metrom-nerede/csvs, backend/csvs
GTFS_CSV_DIR = BASE_DIR.parent.parent / "csvs"
if not GTFS_CSV_DIR.exists():
    GTFS_CSV_DIR = BASE_DIR.parent / "csvs"
if not GTFS_CSV_DIR.exists():
    GTFS_CSV_DIR = BASE_DIR / "csvs"

# Route type: 0=tram, 1=metro/subway, 6=teleferik, 7=funicular, 9=bus
# We only expose: metro (1), tram (0), marmaray (1, agency 4)
METRO_SHORT_NAMES = {"M1A", "M1B", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9"}
TRAM_SHORT_NAMES = {"T1", "T3", "T4", "T5"}
MARMARAY_SHORT_NAMES = {"Marmaray", "Marmaray1", "Marmaray2"}

# Signature stop names to infer trip->route when trips.csv is missing (one per route)
# Must match stop_name in Duraklar.csv (partial match)
SIGNATURE_STOPS = {
    "M1A": "ATATÜRK HAVALIMANI",
    "M1B": "KİRAZLI",
    "M2": "HACIOSMAN",
    "M3": "OLİMPİYAT",
    "M4": "TAVŞANTEPE",
    "M5": "ÇEKMEKÖY",
    "M6": "HİSARÜSTÜ",
    "M7": "MAHMUTBEY METRO",
    "M8": "DUDULLU",
    "M9": "BAHARIYE",
    "T1": "KABATAŞ",
    "T3": "MODA",
    "T4": "MESCİD-İ SELAM",
    "T5": "CİBALI",
    "Marmaray": "GEBZE",
    "Marmaray1": "SÖĞÜTLÜÇEŞME",
    "Marmaray2": "BAHÇEŞEHİR",
}
