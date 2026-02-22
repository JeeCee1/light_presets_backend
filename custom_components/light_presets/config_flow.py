"""Config flow for Light Presets."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import DOMAIN


class LightPresetsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Single-step config flow — just confirm to install."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user step."""
        # Prevent multiple instances
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="Light Presets", data={})

        return self.async_show_form(step_id="user")
