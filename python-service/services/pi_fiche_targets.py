"""Objectifs mensuels / journaliers et zones de la fiche PI."""

# Clés = nom d'agence normalisé (sans AGENCE / C-E / PRINCIPALE).
PI_FICHE_TARGETS = {
    "CASTOR": {"zone": "DAKAR VILLE", "obj_month": 195, "obj_daily": 7},
    "GRAND COMPTE": {"zone": "GRAND COMPTE", "obj_month": 99, "obj_daily": 3},
    "SCAT URBAM": {"zone": "DAKAR VILLE", "obj_month": 71, "obj_daily": 2},
    "NIARRY TALLI": {"zone": "DAKAR VILLE", "obj_month": 27, "obj_daily": 1},
    "LAMINE GUEYE": {"zone": "DAKAR VILLE", "obj_month": 291, "obj_daily": 10},
    "MARISTES": {"zone": "DAKAR VILLE", "obj_month": 104, "obj_daily": 3},
    "POINT E": {"zone": "DAKAR VILLE", "obj_month": 463, "obj_daily": 15},
    "RUFISQUE": {"zone": "DAKAR BANLIEUE", "obj_month": 124, "obj_daily": 4},
    "PIKINE": {"zone": "DAKAR BANLIEUE", "obj_month": 142, "obj_daily": 5},
    "GUEDIAWAYE SAHM": {"zone": "DAKAR BANLIEUE", "obj_month": 8, "obj_daily": 1},
    "KEUR MASSAR": {"zone": "DAKAR BANLIEUE", "obj_month": 1, "obj_daily": 1},
    "LINGUERE LA": {"zone": "DAKAR BANLIEUE", "obj_month": 197, "obj_daily": 7},
    "LINGUERE": {"zone": "DAKAR BANLIEUE", "obj_month": 197, "obj_daily": 7},
    "LINGUERLA": {"zone": "DAKAR BANLIEUE", "obj_month": 197, "obj_daily": 7},
    "PARCELLES": {"zone": "DAKAR BANLIEUE", "obj_month": 266, "obj_daily": 9},
    "TAMBACOUNDA": {"zone": "PROVINCE CENTRE", "obj_month": 14, "obj_daily": 1},
    "ZIGUINCHOR": {"zone": "PROVINCE CENTRE", "obj_month": 155, "obj_daily": 5},
    "KAOLACK": {"zone": "PROVINCE CENTRE", "obj_month": 25, "obj_daily": 1},
    "THIES": {"zone": "PROVINCE CENTRE", "obj_month": 198, "obj_daily": 7},
    "MBOUR": {"zone": "PROVINCE CENTRE", "obj_month": 43, "obj_daily": 1},
    "OUROSSOGUI": {"zone": "PROVINCE NORD", "obj_month": 10, "obj_daily": 1},
    "LOUGA": {"zone": "PROVINCE NORD", "obj_month": 27, "obj_daily": 1},
    "DIOURBEL": {"zone": "PROVINCE NORD", "obj_month": 29, "obj_daily": 1},
    "TOUBA": {"zone": "PROVINCE NORD", "obj_month": 59, "obj_daily": 2},
    "SAINT LOUIS": {"zone": "PROVINCE NORD", "obj_month": 265, "obj_daily": 9},
}

TERRITORY_ZONES = (
    "DAKAR VILLE",
    "DAKAR BANLIEUE",
    "PROVINCE CENTRE",
    "PROVINCE NORD",
)

ZONE_ORDER = {name: index for index, name in enumerate(TERRITORY_ZONES)}

# Agences hors périmètre fiche (Digitale Fina, Siège, Touba Ocas, etc.).
IGNORED_AGENCIES = (
    "DIGITALE",
    "DIGITALE FINA",
    "FINA",
    "SIEGE",
    "SIEGES",
    "TOUBA OCAS",
    "OCAS",
)
