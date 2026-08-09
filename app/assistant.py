"""
app/assistant.py
Moteur d'assistant de voyage intelligent pour Ô'MBOA.
Analyse les demandes en langage naturel et propose des destinations.
"""

def analyze_natural_language(query: str) -> dict:
    """
    Analyse une demande en langage naturel et extrait les préférences.
    Retourne un dictionnaire avec les critères détectés.
    """
    query = query.lower()
    
    # Initialiser les critères par défaut
    criteria = {
        "activite": None,
        "compagnie": None,
        "moment": None,
        "ambiance": None,
        "critere": None,
        "tags": []
    }
    
    # Détecter l'activité
    if any(word in query for word in ["sortir", "bar", "club", "boire", "ambiance"]):
        criteria["activite"] = "sortie"
        criteria["tags"].append("sortie")
    elif any(word in query for word in ["manger", "restaurant", "diner", "gastronomie", "food"]):
        criteria["activite"] = "gastronomie"
        criteria["tags"].append("gastronomie")
    elif any(word in query for word in ["musee", "histoire", "culture", "art", "exposition"]):
        criteria["activite"] = "culture"
        criteria["tags"].append("culture")
    elif any(word in query for word in ["photo", "vue", "decor", "paysage", "monument"]):
        criteria["activite"] = "photo"
        criteria["tags"].append("photo")
    elif any(word in query for word in ["sport", "stade", "football", "loisirs"]):
        criteria["activite"] = "sport"
        criteria["tags"].append("sport")
    elif any(word in query for word in ["detente", "relax", "calme", "tranquille", "repos"]):
        criteria["activite"] = "detente"
        criteria["tags"].append("calme")
    
    # Détecter la compagnie
    if any(word in query for word in ["copine", "copain", "romantique", "couple"]):
        criteria["compagnie"] = "couple"
        criteria["tags"].append("romantique")
    elif any(word in query for word in ["famille", "enfants", "maman", "papa"]):
        criteria["compagnie"] = "famille"
        criteria["tags"].append("famille")
    elif any(word in query for word in ["amis", "entre amis", "groupe"]):
        criteria["compagnie"] = "amis"
        criteria["tags"].append("amis")
    
    # Détecter le moment
    if any(word in query for word in ["soir", "soirée", "nuit", "ce soir"]):
        criteria["moment"] = "soir"
    elif any(word in query for word in ["matin", "matinée"]):
        criteria["moment"] = "matin"
    elif any(word in query for word in ["apres-midi", "après-midi", "midi"]):
        criteria["moment"] = "apres-midi"
    
    # Détecter l'ambiance
    if any(word in query for word in ["calme", "tranquille", "paisible"]):
        criteria["ambiance"] = "calme"
        criteria["tags"].append("calme")
    elif any(word in query for word in ["anime", "vivant", "ambiance", "foule"]):
        criteria["ambiance"] = "anime"
        criteria["tags"].append("anime")
    
    # Détecter le critère esthétique
    if any(word in query for word in ["beau", "joli", "decor", "decoration", "architecture", "vue"]):
        criteria["critere"] = "decoration_photo"
        criteria["tags"].append("photo")
    
    return criteria

def get_recommendations_for_criteria(criteria: dict, destinations: list) -> list:
    """
    Filtre les destinations selon les critères détectés par l'analyseur.
    """
    results = []
    for d in destinations:
        # Vérifier si la destination possède au moins un des tags requis
        if not d.get("tags"):
            continue
        
        matches = 0
        for tag in criteria.get("tags", []):
            if any(t.lower() == tag for t in d["tags"]):
                matches += 1
        
        # Ajouter la destination si elle correspond à au moins 2 critères
        if matches >= 2:
            results.append(d)
    
    # Trier par pertinence (nombre de tags correspondants)
    results.sort(key=lambda x: sum(1 for tag in criteria.get("tags", []) if tag in x.get("tags", [])), reverse=True)
    
    return results[:5]  # Limiter à 5 résultats