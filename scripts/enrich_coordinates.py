"""
scripts/enrich_coordinates.py

Enrichit data/destinations.json avec les coordonnées GPS manquantes.

Protections :
  - Bounding box Douala : rejette tout ce qui est hors zone
  - Détection des doublons : offset les lieux qui tombent au même endroit
  - Fallback quartier : utilise le centre du quartier en dernier recours
"""
import json
import math
import os
import sys
import time

import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINATIONS_FILE = os.path.join(BASE_DIR, "data", "destinations.json")
BACKUP_FILE = DESTINATIONS_FILE + ".backup"

PHOTON_URL = "https://photon.komoot.io/api/"
USER_AGENT = "GlobeTrotterCapstone/1.0"
DELAY = 0.5

# --- Bounding box Douala (lat_min, lon_min, lat_max, lon_max) ---
# Douala : environ 3.9 - 4.2 lat / 9.6 - 9.9 lon
DOUALA_BBOX = {
    "min_lat": 3.9,
    "max_lat": 4.25,
    "min_lon": 9.55,
    "max_lon": 9.95,
}

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


def is_in_douala(lat, lng):
    """Vérifie que les coordonnées sont dans la zone de Douala."""
    if lat is None or lng is None:
        return False
    return (
        DOUALA_BBOX["min_lat"] <= lat <= DOUALA_BBOX["max_lat"]
        and DOUALA_BBOX["min_lon"] <= lng <= DOUALA_BBOX["max_lon"]
    )


def photon_search(query):
    """Requête Photon avec bbox Douala pour restreindre la zone."""
    try:
        # Photon supporte bbox via le paramètre "bbox=minLon,minLat,maxLon,maxLat"
        bbox = f"{DOUALA_BBOX['min_lon']},{DOUALA_BBOX['min_lat']},{DOUALA_BBOX['max_lon']},{DOUALA_BBOX['max_lat']}"
        r = requests.get(
            PHOTON_URL,
            params={"q": query, "limit": 3, "lang": "fr", "bbox": bbox},
            headers={"User-Agent": USER_AGENT},
            timeout=8,
        )
        if r.status_code == 200:
            features = r.json().get("features", [])
            # Prendre le premier résultat DANS Douala
            for feat in features:
                lon, lat = feat["geometry"]["coordinates"]
                lat, lon = float(lat), float(lon)
                if is_in_douala(lat, lon):
                    return lat, lon
    except Exception as e:
        print(f"      ⚠️ Erreur Photon : {e}")
    return None, None


def geocode_precise(name, quartier, category=""):
    """Essaie plusieurs variantes pour trouver la position EXACTE."""
    variants = [
        (f"{name}, {quartier}, Douala, Cameroun", "photon_exact"),
        (f"{name} {quartier} Douala", "photon_exact"),
        (f"{name}, Douala, Cameroun", "photon_nom_ville"),
        (f"{name} Douala", "photon_nom_ville"),
    ]
    if category:
        variants.append((f"{name} {category} Douala", "photon_categorie"))

    for query, source in variants:
        lat, lng = photon_search(query)
        if lat and lng:
            # Vérifier que ce n'est PAS le centre du quartier
            if quartier:
                qkey = quartier.lower().strip()
                if qkey in QUARTIER_COORDS:
                    q_lat, q_lng = QUARTIER_COORDS[qkey]
                    if abs(lat - q_lat) < 0.0005 and abs(lng - q_lng) < 0.0005:
                        # C'est le centre du quartier, on continue
                        continue
            return lat, lng, source
        time.sleep(DELAY)

    return None, None, None


def offset_from_quartier(quartier, index_in_quartier=0):
    """Centre du quartier + offset circulaire pour distinguer les lieux."""
    base = QUARTIER_COORDS.get(quartier.lower().strip() if quartier else "douala")
    if not base:
        return None, None
    angle = (index_in_quartier * 137.5) % 360
    radius_deg = 0.0015
    lat = base[0] + radius_deg * math.cos(math.radians(angle))
    lng = base[1] + radius_deg * math.sin(math.radians(angle))
    return lat, lng


def main():
    if not os.path.exists(DESTINATIONS_FILE):
        print(f"❌ Fichier introuvable : {DESTINATIONS_FILE}")
        sys.exit(1)

    with open(DESTINATIONS_FILE, "r", encoding="utf-8") as f:
        destinations = json.load(f)

    with open(BACKUP_FILE, "w", encoding="utf-8") as f:
        json.dump(destinations, f, ensure_ascii=False, indent=2)
    print(f"💾 Backup créé : {BACKUP_FILE}\n")

    total = len(destinations)
    deja_ok = 0
    photon_ok = 0
    fallback_ok = 0
    echouees = []
    deja_vus_coords = set()  # pour détecter les doublons
    quartier_counters = {}

    print(f"🔍 Traitement de {total} destinations...\n")

    for i, d in enumerate(destinations, 1):
        name = d.get("name", "?")
        quartier = d.get("quartier", "")
        category = d.get("category", "")
        lat = d.get("latitude")
        lng = d.get("longitude")

        if lat and lng:
            deja_ok += 1
            # Mémoriser pour détecter les doublons
            deja_vus_coords.add((round(float(lat), 4), round(float(lng), 4)))
            print(f"[{i}/{total}] ✅ {name} : déjà OK")
            continue

        print(f"[{i}/{total}] 🔎 {name} ({quartier or '?'})...")

        new_lat, new_lng, source = geocode_precise(name, quartier, category)

        # Vérifier doublon
        if new_lat and new_lng:
            key = (round(new_lat, 4), round(new_lng, 4))
            if key in deja_vus_coords:
                print(f"         ⚠️ Doublon détecté → offset")
                qkey = quartier.lower().strip() if quartier else "douala"
                idx = quartier_counters.get(qkey, 0)
                quartier_counters[qkey] = idx + 1
                new_lat, new_lng = offset_from_quartier(quartier, idx)
                source = "offset_doublon"
            else:
                deja_vus_coords.add(key)

        if new_lat and new_lng:
            d["latitude"] = new_lat
            d["longitude"] = new_lng
            d["geocoded"] = source
            if "offset" in source or "fallback" in source:
                fallback_ok += 1
            else:
                photon_ok += 1
            print(f"         ✅ {source} : {new_lat:.4f}, {new_lng:.4f}")
            continue

        # Fallback quartier + offset
        qkey = quartier.lower().strip() if quartier else "douala"
        idx = quartier_counters.get(qkey, 0)
        quartier_counters[qkey] = idx + 1

        fb_lat, fb_lng = offset_from_quartier(quartier, idx)
        if fb_lat and fb_lng:
            d["latitude"] = fb_lat
            d["longitude"] = fb_lng
            d["geocoded"] = f"fallback_quartier_{idx}"
            fallback_ok += 1
            print(f"         ⚠️ Fallback quartier + offset : {fb_lat:.4f}, {fb_lng:.4f}")
        else:
            echouees.append(name)
            print(f"         ❌ Non trouvé")

    with open(DESTINATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(destinations, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("📊 RAPPORT FINAL")
    print("=" * 60)
    print(f"Total                  : {total}")
    print(f"Déjà OK                : {deja_ok}")
    print(f"Enrichies via Photon   : {photon_ok}")
    print(f"Fallback / Offset      : {fallback_ok}")
    print(f"Échouées               : {len(echouees)}")


if __name__ == "__main__":
    main()