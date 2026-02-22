"""Storage handler for light_presets."""
from __future__ import annotations

import uuid
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    DEFAULT_CATEGORY_NAME,
    DOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
)


def _new_id() -> str:
    return str(uuid.uuid4())


def _empty_store() -> dict[str, Any]:
    """Return a fresh store with a single default category."""
    return {
        "version": STORAGE_VERSION,
        "categories": [
            {
                "id": _new_id(),
                "name": DEFAULT_CATEGORY_NAME,
                "order": 0,
                "presets": [],
            }
        ],
    }


class LightPresetsStore:
    """Manages loading and saving of light presets to .storage."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, STORAGE_KEY
        )
        self._data: dict[str, Any] = {}

    async def async_load(self) -> None:
        """Load data from storage, initialising if empty."""
        stored = await self._store.async_load()
        if stored is None:
            self._data = _empty_store()
            await self._store.async_save(self._data)
        else:
            self._data = stored

    async def async_save(self) -> None:
        """Persist current data to storage."""
        await self._store.async_save(self._data)

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def get_all(self) -> dict[str, Any]:
        """Return the full category/preset tree."""
        return self._data

    def _find_category(self, category_id: str) -> dict[str, Any] | None:
        for cat in self._data["categories"]:
            if cat["id"] == category_id:
                return cat
        return None

    def _find_preset(
        self, category_id: str, preset_id: str
    ) -> dict[str, Any] | None:
        cat = self._find_category(category_id)
        if cat is None:
            return None
        for preset in cat["presets"]:
            if preset["id"] == preset_id:
                return preset
        return None

    # ------------------------------------------------------------------
    # Category operations
    # ------------------------------------------------------------------

    async def async_save_category(
        self, category_id: str | None, name: str, order: int | None
    ) -> dict[str, Any]:
        """Create or update a category. Returns the saved category."""
        if category_id is None:
            # Create
            new_order = order if order is not None else len(self._data["categories"])
            cat: dict[str, Any] = {
                "id": _new_id(),
                "name": name,
                "order": new_order,
                "presets": [],
            }
            self._data["categories"].append(cat)
        else:
            cat = self._find_category(category_id)
            if cat is None:
                raise ValueError(f"Category {category_id} not found")
            cat["name"] = name
            if order is not None:
                cat["order"] = order
        await self.async_save()
        return cat

    async def async_delete_category(self, category_id: str) -> None:
        """Delete a category and all its presets."""
        cats = self._data["categories"]
        self._data["categories"] = [c for c in cats if c["id"] != category_id]
        await self.async_save()

    # ------------------------------------------------------------------
    # Preset operations
    # ------------------------------------------------------------------

    async def async_save_preset(
        self,
        category_id: str,
        preset_id: str | None,
        preset_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Create or update a preset within a category. Returns the saved preset."""
        cat = self._find_category(category_id)
        if cat is None:
            raise ValueError(f"Category {category_id} not found")

        if preset_id is None:
            # Create
            preset: dict[str, Any] = {
                "id": _new_id(),
                "order": len(cat["presets"]),
                **preset_data,
            }
            cat["presets"].append(preset)
        else:
            preset = self._find_preset(category_id, preset_id)
            if preset is None:
                raise ValueError(f"Preset {preset_id} not found in category {category_id}")
            preset.update(preset_data)
        await self.async_save()
        return preset

    async def async_delete_preset(
        self, category_id: str, preset_id: str
    ) -> None:
        """Delete a preset from a category."""
        cat = self._find_category(category_id)
        if cat is None:
            raise ValueError(f"Category {category_id} not found")
        cat["presets"] = [p for p in cat["presets"] if p["id"] != preset_id]
        await self.async_save()

    def get_preset_by_id(self, preset_id: str) -> dict[str, Any] | None:
        """Find a preset by id across all categories."""
        for cat in self._data["categories"]:
            for preset in cat["presets"]:
                if preset["id"] == preset_id:
                    return preset
        return None
