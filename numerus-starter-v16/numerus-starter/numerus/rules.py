
from __future__ import annotations
import json, os, unicodedata
from dataclasses import dataclass
from typing import Dict, List, Set

DATA_DIR = os.path.join(os.path.dirname(__file__), "systems")

@dataclass
class SystemRules:
    name: str
    char_map: Dict[str, int]
    master_numbers: Set[int]
    reduce_master: bool  # if True, master numbers are also reduced (rare). Default False
    keep_master: bool    # if True, do not reduce master numbers when they appear
    vowels: Set[str]     # uppercase vowels (policy for 'Y' handled via include_y_as_vowel)
    include_y_as_vowel: bool
    normalization: str   # 'ascii' or 'none'
    reduce_method: str   # 'classic' (sum digits until 1-9 unless master), 'digital_root'

    @staticmethod
    def load(system: str) -> "SystemRules":
        path = os.path.join(DATA_DIR, f"{system}.json")
        if not os.path.exists(path):
            raise ValueError(f"Unknown system: {system}")
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return SystemRules(
            name=raw["name"],
            char_map={k.upper(): v for k, v in raw["char_map"].items()},
            master_numbers=set(raw.get("master_numbers", [])),
            reduce_master=bool(raw.get("reduce_master", False)),
            keep_master=bool(raw.get("keep_master", True)),
            vowels=set([c.upper() for c in raw.get("vowels", list("AEIOU"))]),
            include_y_as_vowel=bool(raw.get("include_y_as_vowel", True)),
            normalization=raw.get("normalization", "ascii"),
            reduce_method=raw.get("reduce_method", "classic"),
        )

def normalize_name(name: str, normalization: str = "ascii") -> str:
    name = name.strip()
    if normalization == "ascii":
        # Remove diacritics, keep basic letters/numbers/spaces
        nfkd = unicodedata.normalize("NFKD", name)
        stripped = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
        return stripped
    return name
