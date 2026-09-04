# Rheem EcoNet Integration for Unfolded Circle Remote 2/3

Control your **Rheem EcoNet water heaters and thermostats** directly from your Unfolded Circle Remote 2 or Remote 3. Set the water temperature and operation mode, control thermostats, toggle away mode, and monitor hot-water availability, tank health, humidity, and running status - all from your EcoNet account.

![Rheem](https://img.shields.io/badge/Rheem-EcoNet-E4002B)
[![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-econet?style=flat-square)](https://github.com/mase1981/uc-intg-econet/releases)
![License](https://img.shields.io/badge/license-MPL--2.0-blue?style=flat-square)
[![GitHub issues](https://img.shields.io/github/issues/mase1981/uc-intg-econet?style=flat-square)](https://github.com/mase1981/uc-intg-econet/issues)
[![Community Forum](https://img.shields.io/badge/community-forum-blue?style=flat-square)](https://unfolded.community/)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-econet/total?style=flat-square)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg?style=flat-square)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA&style=flat-square)](https://github.com/sponsors/mase1981)

## Supported Devices

Rheem EcoNet-connected **water heaters** (electric, gas, hybrid/heat-pump, tankless) and **EcoNet thermostats**. Any water heater or thermostat visible in the Rheem EcoNet app is supported.

## Features

- **🌡️ Water heater climate** - set the target water temperature and turn the heater on/off as a climate entity.
- **🎚️ Operation-mode selector** - choose the water-heater mode: Energy Saver, Heat Pump, High Demand, Electric, Gas, Performance, or Off.
- **🏖️ Away switch** - toggle away/vacation mode.
- **❄️ Thermostat climate** - heat / cool / auto / fan, target temperature (single and range), and fan mode.
- **📊 Sensors** - hot-water availability, tank health, compressor health, humidity, running status, and Wi-Fi signal.
- **☁️ Realtime updates** - state changes are pushed from the EcoNet cloud over MQTT, with polling as a fallback.
- **Multi-device** - every water heater and thermostat on your account is added automatically.

---
## ❤️ Support Development ❤️

If you find this integration useful, consider supporting development:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?style=for-the-badge&logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/mmiyara)

Your support helps maintain this integration. Thank you! ❤️
---

## How It Works

Rheem EcoNet devices are cloud-connected. This integration signs in to your EcoNet account and talks to the same cloud service the EcoNet app uses:

- **One account, all devices** - every water heater and thermostat on the account is added.
- **Realtime push** - the integration subscribes to the EcoNet cloud (MQTT) so changes appear promptly, and also polls periodically as a fallback.
- **Temperatures in Fahrenheit** - matching the EcoNet platform.

> Because this is a cloud integration, your Remote must have internet access and the EcoNet cloud must be reachable.

## Requirements

- A Rheem EcoNet account with at least one connected water heater or thermostat.
- Your EcoNet **email and password**.
- Unfolded Circle Remote 2 / 3 with firmware supporting custom integrations.

## Installation

### Option 1: Remote Web Interface (Recommended)

1. Download the latest `uc-intg-econet-<version>.tar.gz` from the [**Releases**](https://github.com/mase1981/uc-intg-econet/releases) page.
2. Open your Remote's web interface (`http://your-remote-ip`).
3. Go to **Settings → Integrations → Add Integration → Install Custom** and upload the `.tar.gz`.

### Option 2: Docker (Advanced Users)

**Image**: `ghcr.io/mase1981/uc-intg-econet:latest`

**Docker Compose:**
```yaml
services:
  uc-intg-econet:
    image: ghcr.io/mase1981/uc-intg-econet:latest
    container_name: uc-intg-econet
    network_mode: host
    volumes:
      - ./config:/config
    environment:
      - UC_CONFIG_HOME=/config
      - UC_INTEGRATION_HTTP_PORT=9090
      - UC_INTEGRATION_INTERFACE=0.0.0.0
      - PYTHONPATH=/app
    restart: unless-stopped
```

**Docker Run:**
```bash
docker run -d --name uc-intg-econet --restart unless-stopped --network host -v $(pwd)/config:/config -e UC_CONFIG_HOME=/config -e UC_INTEGRATION_INTERFACE=0.0.0.0 -e UC_INTEGRATION_HTTP_PORT=9090 -e PYTHONPATH=/app ghcr.io/mase1981/uc-intg-econet:latest
```

## Configuration

1. Start setup and enter your Rheem EcoNet **email** and **password**.
2. The integration signs in and adds every water heater and thermostat on the account.

For each device the integration creates:

| Entity | Purpose |
|--------|---------|
| **Climate** (`<name>`) | Water heater: target temperature + on/off. Thermostat: heat/cool/auto, fan, target temperature. |
| **Select** (`<name> Mode`) | Water-heater operation mode (Energy Saver, Heat Pump, High Demand, ...). |
| **Switch** (`<name> Away`) | Away / vacation mode (water heaters that support it). |
| **Sensors** | Hot-water availability, tank/compressor health, humidity, running status, Wi-Fi signal. |

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| "Could not sign in to Rheem EcoNet" | Check the email and password (the same you use in the EcoNet app). |
| "No water heaters or thermostats were found" | Make sure the device is set up and visible in the EcoNet app first. |
| Devices unavailable after a while | The Remote lost internet or the EcoNet cloud was unreachable; it recovers automatically when connectivity returns. |
| A mode is missing from the selector | Only the modes your specific model reports are offered. |

## Credits

- **Developer**: Meir Miyara
- **EcoNet cloud API**: based on the [pyeconet](https://github.com/w1ll1am23/pyeconet) library and the Home Assistant EcoNet integration.
- **Unfolded Circle**: Remote 2/3 integration framework ([ucapi](https://github.com/unfoldedcircle/integration-python-library) / [ucapi-framework](https://github.com/JackJPowell/ucapi-framework)).

## License

Mozilla Public License 2.0 (MPL-2.0) - see the LICENSE file.

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-econet/issues)
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
- **Developer**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara)

---

**Made with ❤️ for the Unfolded Circle Community**

**Thank You**: Meir Miyara
