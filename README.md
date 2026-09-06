# HomeAssistant - Blauberg S21 Custom Component

# What This Is

This custom component lets you control and monitor your Blauberg S21 HVAC system locally.

# Installation and Configuration

## Manual install
Copy `custom_components` folder from this repository to `/config` of your Home Assistant instalation.

To configure this integration, go to Home Assistant web interface Configuration -> Integrations and then press "+" button and select "Blauberg S21".

When you are done with configuration you should see your device in Settings -> Devices & Services

# Telemetry sensors

The integration adds the following sensors alongside the climate entity:

- Supply air inlet and outlet temperatures
- Extract air inlet and exhaust air outlet temperatures
- Supply and extract fan speeds
- Remaining filter time and total working time
- Raw alarm status

Unavailable optional telemetry is shown as `unknown`; it does not make the device unavailable.

# Library dependency

Version `0.5.0` installs the maintained [pybls21](https://github.com/simonasr/pybls21)
4.3.0 revision from an immutable Git commit.

The integration refreshes the device once every 30 seconds through a shared coordinator. Control
commands request one immediate refresh so the climate entity and all telemetry sensors update together.

For local checks, install `requirements_test.txt` and run `pytest` from the repository root.

See the [underlying pybls21 library](https://github.com/simonasr/pybls21).
