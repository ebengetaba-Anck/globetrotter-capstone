"""
app/models.py

Data models and file I/O helpers.

All persistent data is stored in JSON files under the /data directory.
  - data/users.json       – registered users
  - data/itineraries.json – user itineraries
  - data/destinations.json – static destination catalogue (seed data)
"""
import json
import os
import unicodedata

# Resolve the /data directory relative to this file's location so the app
# works regardless of the current working directory.
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_BASE_DIR, "data")

USERS_FILE = os.path.join(DATA_DIR, "users.json")
ITINERARIES_FILE = os.path.join(DATA_DIR, "itineraries.json")
DESTINATIONS_FILE = os.path.join(DATA_DIR, "destinations.json")
ACTIVITIES_FILE = os.path.join(DATA_DIR, "activities.json")
TRANSPORT_FILE = os.path.join(DATA_DIR, "transport.json")
RESERVATIONS_FILE = os.path.join(DATA_DIR, "reservations.json")
FAVORITES_FILE = os.path.join(DATA_DIR, "favorites.json")
REVIEWS_FILE = os.path.join(DATA_DIR, "reviews.json")


# ---------------------------------------------------------------------------
# Generic file I/O helpers
# ---------------------------------------------------------------------------
def normalize_text(text: str) -> str:
    """Lowercase *text* and strip accents, for accent-insensitive search.

    E.g. "Marché" and "marche" both normalize to "marche".
    """
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return without_accents.lower()

def _read_json(filepath: str) -> list:
    """Read a JSON file and return its contents as a Python list.

    Returns an empty list if the file does not exist or is empty.
    """
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            content = fh.read().strip()
            if not content:
                return []
            return json.loads(content)
    except (json.JSONDecodeError, Exception):
        return []


def _write_json(filepath: str, data: list) -> None:
    """Serialise *data* and write it to *filepath* (pretty-printed)."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


# ---------------------------------------------------------------------------
# User helpers
# ---------------------------------------------------------------------------

def get_all_users() -> list:
    """Return all registered users."""
    return _read_json(USERS_FILE)


def get_user_by_username(username: str) -> dict | None:
    """Return the user dict for *username*, or None if not found."""
    users = get_all_users()
    for user in users:
        if user.get("username") == username:
            return user
    return None


def save_user(user: dict) -> None:
    """Append *user* to the users store."""
    users = get_all_users()
    users.append(user)
    _write_json(USERS_FILE, users)


# ---------------------------------------------------------------------------
# Destination helpers
# ---------------------------------------------------------------------------

def get_all_destinations() -> list:
    """Return all destinations from the static catalogue."""
    return _read_json(DESTINATIONS_FILE)


# ---------------------------------------------------------------------------
# Itinerary helpers
# ---------------------------------------------------------------------------

def get_all_itineraries() -> list:
    """Return all itineraries across all users."""
    return _read_json(ITINERARIES_FILE)


def get_itineraries_for_user(username: str) -> list:
    """Return itineraries that belong to *username*."""
    return [it for it in get_all_itineraries() if it.get("username") == username]


def save_itinerary(itinerary: dict) -> None:
    """Append *itinerary* to the itineraries store."""
    itineraries = get_all_itineraries()
    itineraries.append(itinerary)
    _write_json(ITINERARIES_FILE, itineraries)
def get_itinerary_by_id(itinerary_id: str) -> dict | None:
    """Return the itinerary matching *itinerary_id*, or None."""
    for it in get_all_itineraries():
        if it.get("id") == itinerary_id:
            return it
    return None


def update_itinerary(itinerary_id: str, updates: dict) -> dict | None:
    """Update the itinerary matching *itinerary_id* with *updates*.

    Returns the updated itinerary, or None if not found.
    """
    itineraries = get_all_itineraries()
    for it in itineraries:
        if it.get("id") == itinerary_id:
            it.update(updates)
            _write_json(ITINERARIES_FILE, itineraries)
            return it
    return None


def delete_itinerary(itinerary_id: str) -> bool:
    """Delete the itinerary matching *itinerary_id*. Returns True if deleted."""
    itineraries = get_all_itineraries()
    filtered = [it for it in itineraries if it.get("id") != itinerary_id]
    if len(filtered) == len(itineraries):
        return False
    _write_json(ITINERARIES_FILE, filtered)
    return True


# ---------------------------------------------------------------------------
# Activity helpers
# ---------------------------------------------------------------------------

def get_all_activities() -> list:
    """Return all activities from the static catalogue."""
    return _read_json(ACTIVITIES_FILE)


# ---------------------------------------------------------------------------
# Transport helpers
# ---------------------------------------------------------------------------

def get_all_transport() -> list:
    """Return all transport options from the static catalogue."""
    return _read_json(TRANSPORT_FILE)


def get_transport_by_id(transport_id: str) -> dict | None:
    """Return the transport dict matching *transport_id*, or None."""
    for t in get_all_transport():
        if t.get("id") == transport_id:
            return t
    return None


# ---------------------------------------------------------------------------
# Reservation helpers
# ---------------------------------------------------------------------------

def get_all_reservations() -> list:
    """Return all transport reservations across all users."""
    return _read_json(RESERVATIONS_FILE)



def get_reservations_for_user(username: str) -> list:
    """Return reservations that belong to *username*."""
    return [r for r in get_all_reservations() if r.get("username") == username]


def save_reservation(reservation: dict) -> None:
    """Append *reservation* to the reservations store."""
    reservations = get_all_reservations()
    reservations.append(reservation)
    _write_json(RESERVATIONS_FILE, reservations)
def get_reservation_by_id(reservation_id: str) -> dict | None:
    """Return the reservation matching *reservation_id*, or None."""
    for r in get_all_reservations():
        if r.get("id") == reservation_id:
            return r
    return None


def delete_reservation(reservation_id: str) -> bool:
    """Delete the reservation matching *reservation_id*. Returns True if deleted."""
    reservations = get_all_reservations()
    filtered = [r for r in reservations if r.get("id") != reservation_id]
    if len(filtered) == len(reservations):
        return False
    _write_json(RESERVATIONS_FILE, filtered)
    return True


# ---------------------------------------------------------------------------
# Favorites helpers
# ---------------------------------------------------------------------------

def get_all_favorites() -> list:
    """Return all favorites. Returns empty list if file is missing or broken."""
    if not os.path.exists(FAVORITES_FILE):
        return []
    try:
        with open(FAVORITES_FILE, "r", encoding="utf-8") as fh:
            content = fh.read().strip()
            if not content:
                return []
            return json.loads(content)
    except (json.JSONDecodeError, IOError):
        return []

def get_favorites_for_user(username: str) -> list:
    """Return favorites that belong to *username*."""
    return [f for f in get_all_favorites() if f.get("username") == username]

def save_favorite(favorite: dict) -> None:
    """Append *favorite* to the favorites store safely."""
    favorites = get_all_favorites()
    favorites.append(favorite)
    temp_file = FAVORITES_FILE + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as fh:
        json.dump(favorites, fh, indent=2)
    os.replace(temp_file, FAVORITES_FILE)

def delete_favorite(username: str, destination_id: str) -> bool:
    """Delete the favorite matching *username* and *destination_id*."""
    favorites = get_all_favorites()
    filtered = [f for f in favorites if not (f.get("username") == username and str(f.get("destination_id")) == str(destination_id))]
    if len(filtered) == len(favorites):
        return False
    temp_file = FAVORITES_FILE + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as fh:
        json.dump(filtered, fh, indent=2)
    os.replace(temp_file, FAVORITES_FILE)
    return True


# ---------------------------------------------------------------------------
# Reviews helpers (AJOUTÉ ICI)
# ---------------------------------------------------------------------------

def get_all_reviews() -> list:
    """Return all reviews. Returns empty list if file is missing or broken."""
    if not os.path.exists(REVIEWS_FILE):
        return []
    try:
        with open(REVIEWS_FILE, "r", encoding="utf-8") as fh:
            content = fh.read().strip()
            if not content:
                return []
            return json.loads(content)
    except (json.JSONDecodeError, IOError):
        return []

def get_reviews_for_destination(destination_id: str) -> list:
    """Return reviews that belong to *destination_id*."""
    return [r for r in get_all_reviews() if str(r.get("destination_id")) == str(destination_id)]

def save_review(review: dict) -> None:
    """Append *review* to the reviews store safely."""
    reviews = get_all_reviews()
    reviews.append(review)
    temp_file = REVIEWS_FILE + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as fh:
        json.dump(reviews, fh, indent=2)
    os.replace(temp_file, REVIEWS_FILE)