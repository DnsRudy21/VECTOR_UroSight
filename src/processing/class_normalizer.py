ALIASES = {
    "rbc": "eritrocitos",
    "eryth": "eritrocitos",
    "wbc": "leucocitos",
    "leuko": "leucocitos",
    "pus": "leucocitos",
    "ep": "celulas_epiteliales",
    "epith": "celulas_epiteliales",
    "epithelial": "celulas_epiteliales",
    "epithn": "celulas_epiteliales_nucleadas",
    "núcleos epiteliales": "celulas_epiteliales_nucleadas",
    "nucleos epiteliales": "celulas_epiteliales_nucleadas",
    "cryst": "cristales",
    "crystal": "cristales",
    "cast": "cilindros",
    "mycete": "levaduras_hongos",
    "células epiteliales": "celulas_epiteliales",
    "levaduras y hongos": "levaduras_hongos",
}

DISPLAY_NAMES = {
    "eritrocitos": "Eritrocitos", "leucocitos": "Leucocitos",
    "celulas_epiteliales": "Células epiteliales",
    "celulas_epiteliales_nucleadas": "Núcleos epiteliales",
    "cilindros": "Cilindros", "cristales": "Cristales",
    "levaduras_hongos": "Levaduras y hongos",
}

def normalize_class_name(name: str) -> str:
    key = name.strip().lower()
    return ALIASES.get(key, key.replace(" ", "_"))


def class_display_name(name: str) -> str:
    """Keep persisted identifiers stable while displaying the USE ontology."""
    canonical = normalize_class_name(name)
    return DISPLAY_NAMES.get(canonical, canonical.replace("_", " "))
