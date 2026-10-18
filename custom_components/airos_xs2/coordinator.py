"""HTTP polling for legacy Ubiquiti airOS 4.x devices."""
import json
import logging
import re
import secrets
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


def _parse_status(body):
    """Parse JSON or the JavaScript assignments returned by airOS 4."""
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        pass

    assignments = {}
    pattern = re.compile(
        r"""\b([A-Za-z_]\w*)\s*=\s*(?:"((?:\\.|[^"\\])*)"|'((?:\\.|[^'\\])*)'|(-?\d+(?:\.\d+)?)|(true|false))\s*;""",
        re.IGNORECASE | re.MULTILINE,
    )
    for match in pattern.finditer(body):
        key, double_quoted, single_quoted, number, boolean = match.groups()
        if double_quoted is not None:
            value = double_quoted
        elif single_quoted is not None:
            value = single_quoted
        elif number is not None:
            value = float(number) if "." in number else int(number)
        else:
            value = boolean.lower() == "true"
        assignments[key] = value
    if not assignments:
        raise UpdateFailed("status.cgi did not contain recognised airOS status values.")
    return assignments


def _normalise(data):
    """Map common airOS status key spellings to the integration's sensor keys."""
    aliases = {
        "signal": ("signal", "wlan_signal", "wireless_signal", "signal_strength"),
        "noise": ("noise", "noisef", "wlan_noise", "wireless_noise"),
        "ccq": ("ccq", "wlan_ccq", "tx_ccq"),
        "snr": ("snr", "wlan_snr"),
        "wlanTxRate": ("wlantxrate", "wlan_tx_rate", "tx_rate"),
        "wlanRxRate": ("wlanrxrate", "wlan_rx_rate", "rx_rate"),
        "essid": ("essid", "ssid", "wlan_essid"),
        "frequency": ("frequency", "wlan_frequency", "freq"),
        "wlanMac": ("wlanmac", "wlan_mac", "wireless_mac", "wmac"),
        "mac": ("mac", "devicemac", "device_mac", "lmac"),
        "ip_address": ("ip_address", "deviceip", "ipaddr", "lan_ip", "lip"),
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
            match = re.match(r"^\s*(-?\d+(?:\.\d+)?)", str(result[key]))
            if not match:
                raise ValueError
            result[key] = float(match.group(1))
        except (KeyError, TypeError, ValueError):
            result.pop(key, None)

    for key in ("signal", "noise", "wlanTxRate", "wlanRxRate", "frequency", "ccq"):
        number(key)
    if "ccq" in result and float(result["ccq"]) > 100:
        result["ccq"] = float(result["ccq"]) / 10
    if "signal" in result and "noise" in result:
        result["snr"] = float(result["signal"]) - float(result["noise"])
    return result


def _identify_device(data, extra_output=""):
    """Infer the hardware model from airOS metadata and system-page text."""
    identity_keys = {
        "platform", "deviceid", "board", "boardname", "board_name",
        "product", "productname", "model", "devicemodel", "hardware",
        "firmwareversion", "cpu_model",
    }
    parts = [extra_output]
    for key, value in list(data.items()):
        if key.lower() in identity_keys:
            parts.append(str(value))
        # Older airOS versions bundle identity values into one string.
        if key.lower() in {"side_devicename", "devicename", "device_name"}:
            raw = str(value)
            parts.append(raw)
            for match in re.finditer(
                r"(deviceId|firmwareVersion|platform|deviceIp|board|product|model)\s*=\s*([^,;]+)",
                raw,
                re.IGNORECASE,
            ):
                data.setdefault(match.group(1), match.group(2).strip())

    identity = " ".join(parts)
    compact = re.sub(r"[^a-z0-9]", "", identity.lower())
    if re.search(r"nanostation\s*2|\bns2\b|\bxs2\b", identity, re.IGNORECASE) or "nanostation2" in compact or "xs2" in compact:
        data["device_model"] = "NanoStation2"
    elif re.search(r"nanostation\s*5|\bns5\b|\bxs5\b", identity, re.IGNORECASE) or "nanostation5" in compact or "xs5" in compact:
        data["device_model"] = "NanoStation5"
    else:
        # deviceId is often the vendor string "UBNT", not a hardware model.
        # Never promote generic vendor labels to Home Assistant's model field.
        for key in ("platform", "board", "boardname", "board_name", "product", "productname", "model", "devicemodel", "hardware", "cpu_model"):
            value = data.get(key)
            if not value:
                continue
            candidate = str(value).strip()
            if candidate and candidate.lower() not in {"ubnt", "ubiquiti", "unknown", "air os", "airos"}:
                data["device_model"] = candidate
                break
        else:
            # Generic vendor identifiers are not hardware models. Always use
            # the manufacturer name rather than exposing "UBNT" in Home Assistant.
            data["device_model"] = "Ubiquiti"


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
        async with self.session.request(self.session_method(kwargs), url, **kwargs) as response:
            body = await response.text()
            if response.status >= 400:
                raise UpdateFailed(f"airOS HTTP {response.status} from {path}")
            return body

    @staticmethod
    def session_method(kwargs):
        """Pop an optional HTTP method, defaulting to GET."""
        return kwargs.pop("method", "GET")

    async def _login(self):
        """Log in using the exact minimal multipart shape expected by old airOS CGI."""
        await self._request("login.cgi")

        # libcurl's -F fields used by the working device test have no per-part
        # Content-Type headers. Build that same simple multipart form explicitly:
        # some old airOS CGI builds fail to parse aiohttp's extra part headers.
        boundary = "------------------------" + secrets.token_hex(12)
        fields = (
            ("uri", ""),
            ("username", self.username),
            ("password", self.password),
        )
        chunks = []
        for name, value in fields:
            chunks.append(
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n'
                "\r\n"
                f"{value}\r\n"
            )
        chunks.append(f"--{boundary}--\r\n")
        payload = "".join(chunks).encode("utf-8")

        async with self.session.post(
            urljoin(self.host, "login.cgi"),
            data=payload,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(payload)),
                "Referer": urljoin(self.host, "login.cgi"),
            },
            allow_redirects=False,
        ) as response:
            body = await response.text()
            status = response.status
            location = response.headers.get("Location", "")

        if status in (301, 302, 303, 307, 308) and "index.cgi" in location.lower():
            return

        lowered = body.lower()
        if "invalid credentials" in lowered or "login failed" in lowered or 'id="loginform"' in lowered:
            raise UpdateFailed(
                f"airOS login.cgi returned the login page (HTTP {status}, "
                f"Location: {location or 'none'}). Login was not accepted; "
                "verify the integration files were updated and restart Home Assistant. "
                "Passwords and session cookies are never logged."
            )
        if status >= 400:
            raise UpdateFailed(f"airOS HTTP {status} from login.cgi")
        raise UpdateFailed(
            f"Unexpected airOS login response (HTTP {status}, "
            f"Location: {location or 'none'})."
        )

    async def async_reboot(self):
        """Request a normal reboot over HTTP; never call the factory-reset endpoint."""
        await self._login()
        try:
            # The System page's Reboot... control opens reboot.cgi with GET.
            # reset.cgi is deliberately never requested by this integration.
            await self._request("reboot.cgi")
        except (aiohttp.ClientError, TimeoutError) as err:
            # Some firmware closes the connection as the device restarts.
            _LOGGER.debug("Connection ended while requesting airOS reboot: %s", err)

    async def _async_update_data(self):
        try:
            await self._login()
            body = await self._request("status.cgi")
            parsed = _parse_status(body)
            flattened = {}
            _flatten(parsed, flattened)
            result = _normalise(flattened)
            _identify_device(result)

            # airOS 4 exposes the configured hostname on system.cgi, not status.cgi.
            try:
                system_page = await self._request("system.cgi")
                hostname_input = re.search(
                    r"""<input\b(?=[^>]*\b(?:name|id)\s*=\s*["']hostname["'])[^>]*>""",
                    system_page,
                    re.IGNORECASE,
                )
                if hostname_input:
                    hostname_value = re.search(
                        r"""\bvalue\s*=\s*["']([^"']*)["']""",
                        hostname_input.group(0),
                        re.IGNORECASE,
                    )
                    if hostname_value and hostname_value.group(1).strip():
                        result["hostname"] = hostname_value.group(1).strip()
                # System-page text can expose legacy board/model identifiers that
                # status.cgi omits, similar to the SSH integration's board/version probes.
                _identify_device(result, re.sub(r"<[^>]+>", " ", system_page))
            except (aiohttp.ClientError, TimeoutError, UpdateFailed):
                # Status sensors remain available if the optional settings page fails.
                pass

            _identify_device(result)
            return result
        except UpdateFailed:
            raise
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Could not connect to airOS over HTTP: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected airOS HTTP error: {err}") from err
