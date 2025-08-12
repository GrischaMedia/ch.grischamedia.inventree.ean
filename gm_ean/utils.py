# -*- coding: utf-8 -*-
from __future__ import annotations

import re

GTIN_PATTERN = re.compile(r"^\d{8}$|^\d{12}$|^\d{13}$|^\d{14}$")


def is_gs1_like(code: str) -> bool:
    """Quick check for EAN/UPC/GTIN-like numeric strings (8/12/13/14)."""
    return bool(GTIN_PATTERN.match(code or ""))


def gtin_checksum_is_valid(code: str) -> bool:
    """Validate GTIN-8/12/13/14 checksum.

    Algorithm: Mod10 with positions from right (excluding check digit), weights 3/1 alternating.
    """
    code = (code or "").strip()
    if not is_gs1_like(code):
        return False

    digits = [int(c) for c in code]
    check = digits.pop()  # last digit
    # weight from rightmost (originally check-1) → first weight = 3
    weight = 3
    total = 0
    for d in reversed(digits):
        total += d * weight
        weight = 1 if weight == 3 else 3
    calc = (10 - (total % 10)) % 10
    return calc == check