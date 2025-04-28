"""Configuration for PrUn services."""

# Liquidity configuration
LIQUIDITY_CONFIG = {
    "safety_buffer_percent": 0.1,  # 10% of balance
    "min_safety_buffer": 1000,  # Minimum 1000 A$
    "variance_tolerance": 0.05,  # 5% variance allowed
    "workforce_rates": {
        "pioneer": 30,  # A$/hour
        "settler": 40,  # A$/hour
        "technician": 50,  # A$/hour
        "engineer": 60,  # A$/hour
        "scientist": 70,  # A$/hour
    },
    "power_rate": 5,  # A$/kWh
    "power_usage": 0.5,  # kW per building
    "wear_rate": 0.1,  # A$/tick
}
