"""
scripts/geocoder.py

Module réutilisable de géocodage. Utilisable par :
  - scripts/enrich_coordinates.py (batch)
  - le dashboard admin (à la création d'une destination)
  - tout autre service

Usage :
    from scripts.geocoder import resolve_coordinates
    lat, lng, source = resolve_coordinates("Musée Maritime", "Bonanjo")
    # → (4.047, 9.6935, "photon") ou (4.047, 9.6935, "fallback") ou (None, None, "failed")
"""
import time
import requests

PHOTON_URL = "https://photon.komoot.io/api/"
USER_AGENT = "GlobeTrotterCapstone/1.0"

QUARTIER_COORDS = {
    "akwa": (4.0483, 9.7043),
    "bonanjo": (4.0470, 9.6935),
    "bonapriso": (4.0322, 9.7021),
    "bonamoussadi": (4.0836, 9.7312),
    "bonaberi": (4.0700, 9.6800),
    "deido": (4.0600, 9.7000),
    "bali": (4.0200, 9.7100),
    "new bell": (4.0400, 9.7200),
    "bepanda": (4.0550, 9.7300),
    "logbessou": (4.0800, 9.7500),
    "kotto": (4.0450, 9.7150),
    "tokoto": (4.0550, 9.7100),
    "japoma": (4.0950, 9.7750),
    "youpwe": (4.0300, 9.7200),
    "makepe": (4.0700, 9.7400),
    "bassa": (4.0333, 9.7500),
    "douala": (4.0511, 9.7679),
}


def _photon_search(query):
    try:
        r = requests.get(
            PHOTON_URL,
            params={"q": query, "limit": 1, "lang": "fr"},
            headers={"User-Agent": USER_AGENT},
            timeout=8,
        )
        if r.status_code == 200:
            features = r.json().get("features", [])
            if features:
                lon, lat = features[0]["geometry"]["coordinates"]
                return float(lat), float(lon)
    except Exception:
        pass
    return None, None


def resolve_coordinates(name, quartier=""):
    """
    Résout les coordonnées d'un lieu en 3 niveaux.
    Retourne (lat, lng, source).
    """
    # Niveau 2a : nom + quartier
    if name and quartier:
        lat, lng = _photon_search(f"{name}, {quartier}, Douala, Cameroun")
        if lat:
            return lat, lng, "photon"

    # Niveau 2b : nom seul
    if name:
        lat, lng = _photon_search(f"{name}, Douala, Cameroun")
        if lat:
            return lat, lng, "photon"

    # Niveau 2c : quartier seul
    if quartier:
        lat, lng = _photon_search(f"{quartier}, Douala, Cameroun")
        if lat:
            return lat, lng, "photon_quartier"

    # Niveau 3 : fallback local
    if quartier:
        key = quartier.lower().strip()
        if key in QUARTIER_COORDS:
            return (*QUARTIER_COORDS[key], "fallback")
        for k, v in QUARTIER_COORDS.items():
            if k in key or key in k:
                return (*v, "fallback")

    return None, None, "failed"