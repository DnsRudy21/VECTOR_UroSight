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
    "cryst": "cristales",
    "crystal": "cristales",
    "cast": "cilindros",
    "mycete": "levaduras_hongos",
}

def normalize_class_name(name: str) -> str:
    key = name.strip().lower()
    return ALIASES.get(key, key.replace(" ", "_"))
