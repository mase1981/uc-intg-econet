"""Constants for the Rheem EcoNet integration."""

STATE_ON = "ON"
STATE_UNAVAILABLE = "UNAVAILABLE"

POLL_INTERVAL = 60

KIND_WATER_HEATER = "water_heater"
KIND_THERMOSTAT = "thermostat"

# Friendly labels for pyeconet WaterHeaterOperationMode enum names.
WH_MODE_LABELS = {
    "OFF": "Off",
    "ELECTRIC_MODE": "Electric",
    "ELECTRIC": "Electric",
    "ENERGY_SAVING": "Energy Saver",
    "ENERGY_SAVER": "Energy Saver",
    "HEAT_PUMP_ONLY": "Heat Pump",
    "HEAT_PUMP": "Heat Pump",
    "HIGH_DEMAND": "High Demand",
    "GAS": "Gas",
    "ELECTRIC_GAS": "Electric/Gas",
    "PERFORMANCE": "Performance",
    "VACATION": "Vacation",
}

# Thermostat fan-mode labels (pyeconet ThermostatFanMode enum names).
FAN_MODE_LABELS = {
    "AUTO": "Auto",
    "ON_CONTINUOUS": "On",
}

TEMPERATURE_UNIT = "FAHRENHEIT"
