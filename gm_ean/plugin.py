# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List, Optional
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.urls import path, re_path, reverse
from django.utils.translation import gettext_lazy as _

from plugin import InvenTreePlugin
from plugin.mixins import PanelMixin, UrlsMixin, SettingsMixin, BarcodeMixin

from part.models import Part

# --- GTIN Validation (8/12/13/14) ---
import re
GTIN_PATTERN = re.compile(r"^\d{8}$|^\d{12}$|^\d{13}$|^\d{14}$")

def is_gs1_like(code: str) -> bool:
    return bool(GTIN_PATTERN.match((code or '').strip()))

def gtin_checksum_is_valid(code: str) -> bool:
    code = (code or '').strip()
    if not is_gs1_like(code):
        return False
    digits = [int(c) for c in code]
    check = digits.pop()
    weight = 3
    total = 0
    for d in reversed(digits):
        total += d * weight
        weight = 1 if weight == 3 else 3
    calc = (10 - (total % 10)) % 10
    return calc == check


class GrischaMediaEANPlugin(PanelMixin, UrlsMixin, SettingsMixin, BarcodeMixin, InvenTreePlugin):
    """EAN / GTIN Unterstützung für InvenTree 0.18."""

    NAME = "GM_EAN"
    SLUG = "gm-ean"
    TITLE = _("EAN / GTIN Unterstützung")
    DESCRIPTION = _("Erfassen, validieren und scannen von EAN/GTIN Codes für Teile")
    VERSION = "1.0.0"
    AUTHOR = "GrischaMedia"
    WEBSITE = "https://grischamedia.ch"
    LICENSE = "Proprietary"

    SETTINGS = {
        "ENABLE_PANEL": {
            "name": _("Panel aktivieren"),
            "description": _("Zeigt ein EAN-Panel auf der Teile-Detailseite an"),
            "validator": bool,
            "default": True,
        },
        "ENABLE_BARCODE_SCAN": {
            "name": _("Scan aktivieren"),
            "description": _("Beim Scannen einer EAN wird das zugehörige Teil geöffnet"),
            "validator": bool,
            "default": True,
        },
        "EAN_METADATA_KEY": {
            "name": _("Metadaten-Schlüssel"),
            "description": _("Key im Part.metadata für die EAN/GTIN"),
            "default": "ean",
        },
        "LOCK_CORE_FIELDS": {
            "name": _("Kernfelder schuetzen"),
            "description": _("Erlaubt in diesem Endpoint ausschliesslich das Schreiben von metadata['ean']"),
            "validator": bool,
            "default": True,
        }
    }

    # ---------- Panel (Legacy-UI 0.18) ----------
    def get_custom_panels(self, view, request: HttpRequest) -> List[Dict[str, Any]]:
        try:
            from part.views import PartDetail
        except Exception:
            return []

        if not self.get_setting("ENABLE_PANEL"):
            return []

        if isinstance(view, PartDetail):
            part = view.get_object()
            key = self.get_setting("EAN_METADATA_KEY")
            ean = (part.metadata or {}).get(key, "")

            return [{
                "title": "EAN / GTIN",
                "icon": "fas fa-barcode",
                "content_template": "gm_ean/part_panel.html",
                "context": {
                    "part": part,
                    "ean": ean,
                    "metadata_key": key,
                    "plugin_slug": self.SLUG,
                },
            }]
        return []

    # ---------- URLs ----------
    def setup_urls(self):
        return [
            re_path(rf"{self.SLUG}/set/(?P<pk>\d+)/$", self.set_ean, name="set-ean"),
            path(f"{self.SLUG}/search/", self.search_ean, name="search"),
        ]

    def _find_part_by_ean(self, code: str) -> Optional[Part]:
        key = self.get_setting("EAN_METADATA_KEY")
        qs = Part.objects.filter(metadata__has_key=key).filter(**{f"metadata__{key}": code})
        return qs.first()

    def set_ean(self, request: HttpRequest, pk: int, *args, **kwargs) -> HttpResponse:
        if request.method != "POST":
            return HttpResponseBadRequest("POST required")

        try:
            part = Part.objects.get(pk=pk)
        except Part.DoesNotExist:
            return HttpResponseBadRequest("Part not found")

        # Defensiver Guard: Erlaube ausschliesslich das Setzen von 'ean' ueber diesen Endpoint
        if self.get_setting("LOCK_CORE_FIELDS"):
            allowed_keys = {"ean", "csrfmiddlewaretoken"}
            unexpected = [k for k in request.POST.keys() if k not in allowed_keys]
            if unexpected:
                return JsonResponse({
                    "success": False,
                    "error": "Unerlaubte Felder in der Anfrage"
                }, status=400)

        code = (request.POST.get("ean") or request.GET.get("ean") or "").strip()
        if not is_gs1_like(code) or not gtin_checksum_is_valid(code):
            return JsonResponse({"success": False, "error": "Ungültige EAN/GTIN"}, status=400)

        # uniqueness
        other = self._find_part_by_ean(code)
        if other and other.pk != part.pk:
            return JsonResponse({"success": False, "error": f"EAN bereits vergeben (Teil #{other.pk})"}, status=400)

        key = self.get_setting("EAN_METADATA_KEY")
        meta = part.metadata or {}
        meta[key] = code
        part.metadata = meta
        part.save(update_fields=["metadata"])

        return JsonResponse({"success": True, "ean": code})

    def search_ean(self, request: HttpRequest) -> HttpResponse:
        code = (request.GET.get("code") or "").strip()
        if not code:
            return HttpResponseBadRequest("Missing code")

        p = self._find_part_by_ean(code)
        if not p:
            return JsonResponse({"success": False, "error": "Kein Teil mit dieser EAN gefunden"}, status=404)

        return HttpResponseRedirect(reverse("part-detail", kwargs={"pk": p.pk}))

    # ---------- Barcode Scan Hook ----------
    def scan(self, barcode_data: Any):
        if not self.get_setting("ENABLE_BARCODE_SCAN"):
            return None

        if isinstance(barcode_data, str) and is_gs1_like(barcode_data) and gtin_checksum_is_valid(barcode_data):
            part = self._find_part_by_ean(barcode_data)
            if part:
                label = part.barcode_model_type()
                return {
                    label: part.format_matched_response(),
                    "success": str(_("Gefundenes Teil")),
                }
        return None