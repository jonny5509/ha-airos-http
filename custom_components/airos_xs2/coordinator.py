"""HTTP polling for legacy Ubiquiti airOS 4.x devices."""
import json
import logging
import re
from datetime import timedelta
from urllib.parse import urljoin

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


def _flatten(value, output, prefix=""):
    """Flatten status.cgi JSON into stable scalar keys."""
    if isinstance(value, dict):
        for key, child in value.items():
            name = f"{prefix}_{key}" if prefix else str(key)
            _flatten(child, output, name)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _flatten(child, output, f"{prefix}_{index}")
    elif value is not None and not isinstance(value, (dict, list)):
        output[prefix] = value


def _normalise(data):
    """Map common airOS status key spellings to the integration's sensor keys."""
    aliases = {
        "signal": ("signal", "wlan_signal", "wireless_signal", "signal_strength"),
        "noise": ("noise", "wlan_noise", "wireless_noise"),
        "ccq": ("ccq", "wlan_ccq", "tx_ccq"),
        "snr": ("snr", "wlan_snr"),
        "wlanTxRate": ("wlantxrate", "wlan_tx_rate", "tx_rate"),
        "wlanRxRate": ("wlanrxrate", "wlan_rx_rate", "rx_rate"),
        "essid": ("essid", "ssid", "wlan_essid"),
        "frequency": ("frequency", "wlan_frequency", "freq"),
        "wlanMac": ("wlanmac", "wlan_mac", "wireless_mac"),
        "mac": ("mac", "devicemac", "device_mac"),
        "hostname": ("hostname", "host_name", "devicename"),
        "ip_address": ("ip_address", "deviceip", "ipaddr", "lan_ip"),
        "firmwareVersion": ("firmwareversion", "firmware_version", "version"),
        "platform": ("platform", "board", "boardname", "board_name"),
        "uptime_seconds": ("uptime_seconds", "uptime", "system_uptime"),
    }
    lookup = {re.sub(r"[^a-z0-9]", "", str(k).lower()): v for k, v in data.items()}
    result = dict(data)
    for target, candidates in aliases.items():
        for candidate in candidates:
            value = lookup.get(re.sub(r"[^a-z0-9]", "", candidate))
            if value not in (None, ""):
                result[target] = value
                break

    def number(key):
        try:
            return float(result[key])
        except (KeyError, TypeError, ValueError):
            result.pop(key, None)
            return None

    for key in ("signal", "noise", "wlanTxRate", "wlanRxRate", "frequency", "ccq"):
        number(key)
    if "ccq" in result and float(result["ccq"]) > 100:
        result["ccq"] = float(result["ccq"]) / 10
    if "signal" in result and "noise" in result:
        result["snr"] = float(result["signal"]) - float(result["noise"])
    result.setdefault("device_model", "NanoStation5")
    result["firmware_upgrade_latest_version"] = "4.0.4.5074"
    result["firmware_upgrade_source"] = "https://ui.com/download/airmax-legacy"
    version = str(result.get("firmwareVersion", ""))
    match = re.search(r"v?(\d+)\.(\d+)\.(\d+)(?:\.(\d+))?", version, re.I)
    if match and result.get("device_model") == "NanoStation5":
        installed = tuple(int(part or 0) for part in match.groups())
        latest = (4, 0, 4, 5074)
        result["firmware_upgrade"] = (
            "Update available" if installed < latest else
            "Up to date" if installed == latest else "Unknown"
        )
        result["firmware_upgrade_installed_version"] = version
    else:
        result["firmware_upgrade"] = "Unknown"
    return result


class AiRXS2Coordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, host, username, password, name):
        self.host = "http://" + host.removeprefix("https://").removeprefix("http://").strip("/").rstrip("/") + "/"
        self.username = username
        self.password = password
        self.device_name = name
        timeout = aiohttp.ClientTimeout(total=15)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            cookie_jar=aiohttp.CookieJar(unsafe=True),
            headers={"User-Agent": "HomeAssistant-AirOS-HTTP/2.0"},
        )
        super().__init__(
            hass, logger=_LOGGER, name=f"airos_http_{name}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def async_close(self):
        if not self.session.closed:
            await self.session.close()

    async def _request(self, path, **kwargs):
        url = urljoin(self.host, path.lstrip("/"))
        async with self.session.request(kwargs.pop("method", "GET"), url, **kwargs) as response:
            body = await response.text()
            if response.status >= 400:
                raise UpdateFailed(f"airOS HTTP {response.status} from {path}")
            return body

    async def _login(self):
        # airOS 4.x uses the legacy CGI form login and a session cookie.
        await self._request("login.cgi")
        # Legacy airOS login.cgi expects multipart/form-data (the same format
        # used by the device's browser form), not application/x-www-form-urlencoded.
        form = aiohttp.FormData()
        form.add_field("username", self.username)
        form.add_field("password", self.password)
        form.add_field("uri", "status.cgi")
        body = await self._request(
            "login.cgi",
            method="POST",
            data=form,
            headers={"Expect": ""},
        )
        if "invalid credentials" in body.lower() or "login failed" in body.lower():
            raise UpdateFailed("airOS rejected the HTTP login credentials")

    async def _async_update_data(self):
        try:
            await self._login()
            body = await self._request("status.cgi")
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                # Some builds return the status JSON inside a script/HTML wrapper.
                match = re.search(r"(\{.*\}|\[.*\])", body, re.S)
                if not match:
                    raise UpdateFailed(
                        "status.cgi did not return JSON. Check that HTTP access is enabled and the device firmware exposes status.cgi."
                    )
                try:
                    parsed = json.loads(match.group(1))
                except json.JSONDecodeError as err:
                    raise UpdateFailed("Could not parse airOS status.cgi response") from err
            flattened = {}
            _flatten(parsed, flattened)
            # Keep a raw snapshot for troubleshooting without logging credentials.
            data = _normalise(flattened)
            data.setdefault("device_model", "NanoStation5")
            return data
        except UpdateFailed:
            raise
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Could not connect to airOS over HTTP: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected airOS HTTP error: {err}") from err
