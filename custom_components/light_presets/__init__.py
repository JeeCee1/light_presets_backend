"""Light Presets integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    PRESET_TYPES,
    SERVICE_APPLY_COLOR,
    SERVICE_DELETE_CATEGORY,
    SERVICE_DELETE_PRESET,
    SERVICE_GET_PRESETS,
    SERVICE_SAVE_CATEGORY,
    SERVICE_SAVE_PRESET,
)
from .store import LightPresetsStore

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Light Presets from a config entry."""
    store = LightPresetsStore(hass)
    await store.async_load()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = store

    # ----------------------------------------------------------------
    # Service: get_presets
    # Returns the full category/preset tree.
    # ----------------------------------------------------------------
    async def handle_get_presets(call: ServiceCall) -> ServiceResponse:
        return store.get_all()

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_PRESETS,
        handle_get_presets,
        supports_response=SupportsResponse.ONLY,
    )

    # ----------------------------------------------------------------
    # Service: applyColor
    # Applies a preset by id to one or more light entities.
    # Matches rgb-light-card's applyColor naming convention.
    # ----------------------------------------------------------------
    async def handle_apply_color(call: ServiceCall) -> None:
        preset_id: str = call.data["preset_id"]
        entity_ids: list[str] = call.data["entity_id"]

        preset = store.get_preset_by_id(preset_id)
        if preset is None:
            _LOGGER.error("light_presets.applyColor: preset %s not found", preset_id)
            return

        # Build light.turn_on service data from preset attributes.
        # Only include attributes relevant to the preset type.
        service_data: dict[str, Any] = {}

        if "brightness_pct" in preset:
            service_data["brightness_pct"] = preset["brightness_pct"]
        if "transition" in preset:
            service_data["transition"] = preset["transition"]

        preset_type = preset.get("type")
        if preset_type == "color_temp_kelvin":
            service_data["color_temp_kelvin"] = preset["color_temp_kelvin"]
        elif preset_type == "rgb":
            service_data["rgb_color"] = preset["rgb_color"]
        elif preset_type == "hs":
            service_data["hs_color"] = preset["hs_color"]
        # brightness_only: no color attributes added

        for entity_id in entity_ids:
            await hass.services.async_call(
                "light",
                "turn_on",
                {"entity_id": entity_id, **service_data},
            )

    hass.services.async_register(
        DOMAIN,
        SERVICE_APPLY_COLOR,
        handle_apply_color,
        schema=vol.Schema({
            vol.Required("preset_id"): cv.string,
            vol.Required("entity_id"): vol.All(cv.ensure_list, [cv.entity_id]),
        }),
    )

    # ----------------------------------------------------------------
    # Service: save_category
    # Creates or updates a category. Pass category_id to update.
    # ----------------------------------------------------------------
    async def handle_save_category(call: ServiceCall) -> ServiceResponse:
        cat = await store.async_save_category(
            category_id=call.data.get("category_id"),
            name=call.data["name"],
            order=call.data.get("order"),
        )
        return cat

    hass.services.async_register(
        DOMAIN,
        SERVICE_SAVE_CATEGORY,
        handle_save_category,
        schema=vol.Schema({
            vol.Optional("category_id"): cv.string,
            vol.Required("name"): cv.string,
            vol.Optional("order"): vol.Coerce(int),
        }),
        supports_response=SupportsResponse.ONLY,
    )

    # ----------------------------------------------------------------
    # Service: delete_category
    # ----------------------------------------------------------------
    async def handle_delete_category(call: ServiceCall) -> None:
        await store.async_delete_category(call.data["category_id"])

    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_CATEGORY,
        handle_delete_category,
        schema=vol.Schema({
            vol.Required("category_id"): cv.string,
        }),
    )

    # ----------------------------------------------------------------
    # Service: save_preset
    # Creates or updates a preset. Pass preset_id to update.
    # ----------------------------------------------------------------
    async def handle_save_preset(call: ServiceCall) -> ServiceResponse:
        preset_data = {
            "name": call.data["name"],
            "type": call.data["type"],
        }
        if "brightness_pct" in call.data:
            preset_data["brightness_pct"] = call.data["brightness_pct"]
        if "transition" in call.data:
            preset_data["transition"] = call.data["transition"]
        if "color_temp_kelvin" in call.data:
            preset_data["color_temp_kelvin"] = call.data["color_temp_kelvin"]
        if "rgb_color" in call.data:
            preset_data["rgb_color"] = call.data["rgb_color"]
        if "hs_color" in call.data:
            preset_data["hs_color"] = call.data["hs_color"]
        if "order" in call.data:
            preset_data["order"] = call.data["order"]

        preset = await store.async_save_preset(
            category_id=call.data["category_id"],
            preset_id=call.data.get("preset_id"),
            preset_data=preset_data,
        )
        return preset

    hass.services.async_register(
        DOMAIN,
        SERVICE_SAVE_PRESET,
        handle_save_preset,
        schema=vol.Schema({
            vol.Required("category_id"): cv.string,
            vol.Optional("preset_id"): cv.string,
            vol.Required("name"): cv.string,
            vol.Required("type"): vol.In(PRESET_TYPES),
            vol.Optional("brightness_pct"): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=100)
            ),
            vol.Optional("transition"): vol.All(
                vol.Coerce(float), vol.Range(min=0)
            ),
            vol.Optional("color_temp_kelvin"): vol.All(
                vol.Coerce(int), vol.Range(min=1000, max=10000)
            ),
            vol.Optional("rgb_color"): vol.All(
                list, vol.Length(min=3, max=3),
                [vol.All(vol.Coerce(int), vol.Range(min=0, max=255))]
            ),
            vol.Optional("hs_color"): vol.All(
                list, vol.Length(min=2, max=2),
            ),
            vol.Optional("order"): vol.Coerce(int),
        }),
        supports_response=SupportsResponse.ONLY,
    )

    # ----------------------------------------------------------------
    # Service: delete_preset
    # ----------------------------------------------------------------
    async def handle_delete_preset(call: ServiceCall) -> None:
        await store.async_delete_preset(
            category_id=call.data["category_id"],
            preset_id=call.data["preset_id"],
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_PRESET,
        handle_delete_preset,
        schema=vol.Schema({
            vol.Required("category_id"): cv.string,
            vol.Required("preset_id"): cv.string,
        }),
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and clean up services."""
    hass.data[DOMAIN].pop(entry.entry_id)

    # Only remove services if no other entries remain
    if not hass.data[DOMAIN]:
        for service in [
            SERVICE_GET_PRESETS,
            SERVICE_APPLY_COLOR,
            SERVICE_SAVE_CATEGORY,
            SERVICE_DELETE_CATEGORY,
            SERVICE_SAVE_PRESET,
            SERVICE_DELETE_PRESET,
        ]:
            hass.services.async_remove(DOMAIN, service)

    return True
