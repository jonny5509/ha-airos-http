"""Config flow for the Ubiquiti AirOS HTTP integration."""

from typing import Any
from urllib.parse import urlsplit

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN


def _normalise_host(value: str) -> str:
    """Normalize a host or URL to the plain HTTP URL used by the coordinator."""
    value = value.strip()
    if not value:
        raise ValueError("empty host")

    # Accept a bare host or an explicitly supplied http(s) URL, but don't
    # silently accept paths or query strings as part of the device address.
    candidate = value if "://" in value else f"http://{value}"
    parsed = urlsplit(candidate)
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or any(character.isspace() for character in parsed.netloc)
    ):
        raise ValueError("invalid host")

    # This legacy integration only supports plain HTTP.
    return f"http://{parsed.netloc.lower()}"


class AiRXS2ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle configuration of an AirOS HTTP device."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                host = _normalise_host(user_input[CONF_HOST])
            except (TypeError, ValueError):
                errors["base"] = "invalid_host"
            else:
                data = {
                    **user_input,
                    CONF_NAME: user_input[CONF_NAME].strip(),
                    CONF_HOST: host,
                    CONF_USERNAME: user_input[CONF_USERNAME].strip(),
                }
                if not data[CONF_NAME] or not data[CONF_USERNAME] or not data[CONF_PASSWORD]:
                    errors["base"] = "invalid_input"
                else:
                    # A host/IP address is mutable and is not a suitable device
                    # unique ID. Match existing entries by their normalized host.
                    self._async_abort_entries_match({CONF_HOST: host})
                    return self.async_create_entry(
                        title=data[CONF_NAME],
                        data=data,
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): str,
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )
