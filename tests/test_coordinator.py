"""Unit tests for legacy airOS status parsing and normalisation."""
import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.airos_xs2.coordinator import _flatten, _normalise, _parse_status


def test_parse_status_json_object():
    parsed = _parse_status('{"signal": -63, "noise": -96, "essid": "Lab"}')
    assert parsed == {"signal": -63, "noise": -96, "essid": "Lab"}


def test_parse_status_flattens_nested_json():
    parsed = _parse_status('{"wireless": {"signal": -63}, "interfaces": [{"rxbytes": 12}]}')
    flattened = {}
    _flatten(parsed, flattened)
    assert flattened == {"wireless_signal": -63, "interfaces_0_rxbytes": 12}


def test_parse_status_javascript_assignments():
    parsed = _parse_status('signal = -63;\nnoise = -96;\nessid = "TestNet";\nradio_enabled = true;')
    assert parsed == {
        "signal": -63,
        "noise": -96,
        "essid": "TestNet",
        "radio_enabled": True,
    }


def test_parse_status_rejects_unrecognised_html():
    with pytest.raises(UpdateFailed, match="did not contain recognised"):
        _parse_status("<html><body>not a status response</body></html>")


def test_normalise_common_wireless_aliases_and_derive_snr():
    result = _normalise({
        "wlan_signal": "-63 dBm",
        "wlan_noise": "-96 dBm",
        "wlan_ccq": "975",
        "ssid": "Lab",
        "wlan_tx_rate": "150.0",
    })
    assert result["signal"] == -63
    assert result["noise"] == -96
    assert result["snr"] == 33
    assert result["ccq"] == 97.5
    assert result["essid"] == "Lab"
    assert result["wlanTxRate"] == 150.0


def test_normalise_identifies_only_original_nano_station_2_and_5_aliases():
    ns2 = _normalise({"platform": "XS2"})
    ns5 = _normalise({"platform": "XS5"})
    loco = _normalise({"platform": "NanoStation Loco5"})
    powerstation = _normalise({"platform": "PowerStation2"})

    assert ns2["device_model"] == "NanoStation 2"
    assert ns5["device_model"] == "NanoStation 5"
    assert loco.get("device_model") != "NanoStation 5"
    assert powerstation.get("device_model") != "NanoStation 2"


def test_normalise_ignores_invalid_numeric_values():
    result = _normalise({"signal": "unknown", "frequency": "not set"})
    assert "signal" not in result
    assert "frequency" not in result
