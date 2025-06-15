import yaml
import json

# Custom class to force double-quoted strings
class QuotedStr(str):
    pass

def quoted_str_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')

yaml.add_representer(QuotedStr, quoted_str_representer)

# Building to expertise mapping (from user data)
building_expertise_map = {
    "AAF": "MANUFACTURING",
    "AML": "CHEMISTRY",
    "APF": "MANUFACTURING",
    "ASM": "METALLURGY",
    "BMP": "MANUFACTURING",
    "CHP": "CHEMISTRY",
    "CLF": "MANUFACTURING",
    "CLR": "ELECTRONICS",
    "COL": "RESOURCE_EXTRACTION",
    "DRS": "ELECTRONICS",
    "ECA": "ELECTRONICS",
    "EDM": "ELECTRONICS",
    "EEP": "CHEMISTRY",
    "ELP": "ELECTRONICS",
    "EXT": "RESOURCE_EXTRACTION",
    "FER": "FOOD_INDUSTRIES",
    "FP": "FOOD_INDUSTRIES",
    "FRM": "AGRICULTURE",
    "FS": "METALLURGY",
    "GF": "METALLURGY",
    "HWP": "METALLURGY",
    "HYF": "AGRICULTURE",
    "INC": "RESOURCE_EXTRACTION",
    "IVP": "FOOD_INDUSTRIES",
    "LAB": "CHEMISTRY",
    "MCA": "MANUFACTURING",
    "ORC": "AGRICULTURE",
    "PAC": "MANUFACTURING",
    "PHF": "CHEMISTRY",
    "POL": "CHEMISTRY",
    "PP1": "CONSTRUCTION",
    "PP2": "CONSTRUCTION",
    "PP3": "CONSTRUCTION",
    "PP4": "CONSTRUCTION",
    "PPF": "MANUFACTURING",
    "REF": "FUEL_REFINING",
    "RIG": "RESOURCE_EXTRACTION",
    "SCA": "MANUFACTURING",
    "SD": "ELECTRONICS",
    "SE": "ELECTRONICS",
    "SKF": "METALLURGY",
    "SL": "ELECTRONICS",
    "SME": "METALLURGY",
    "SPF": "MANUFACTURING",
    "SPP": "MANUFACTURING",
    "TNP": "CHEMISTRY",
    "UPF": "CONSTRUCTION",
    "WEL": "CONSTRUCTION",
    "WPL": "MANUFACTURING"
}

with open("production_Aaron987.txt", "r", encoding="utf-8") as f:
    empire_orders = json.load(f)

planets_dict = {}
for planet in empire_orders:
    planet_name = planet.get("PlanetName") or planet.get("name") or "Unknown"
    key = QuotedStr(str(planet_name))
    expertise_types = set()
    recipes = []
    for order in planet.get("Orders", []):
        std_recipe = order.get("StandardRecipeName")
        building_symbol = std_recipe.split(":")[0] if std_recipe and ":" in std_recipe else None
        expertise = building_expertise_map.get(building_symbol)
        if expertise:
            expertise_types.add(expertise)
        recipe_entry = {
            "building_symbol": QuotedStr(str(building_symbol)),
            "recipe_symbol": QuotedStr(str(std_recipe))
        }
        if building_symbol in ("EXT", "RIG", "COL"):
            outputs = order.get("Outputs", [])
            if outputs:
                recipe_entry["item_symbol"] = outputs[0]["MaterialTicker"]
        recipes.append(recipe_entry)
    if not recipes:
        continue
    # Merge with existing planet if already present
    if key in planets_dict:
        planets_dict[key]["recipes"].extend(recipes)
        planets_dict[key]["experts"].update({exp: 5 for exp in expertise_types})
    else:
        experts = {exp: 5 for exp in sorted(expertise_types)}
        planets_dict[key] = {
            "name": key,
            "experts": experts,
            "recipes": recipes
        }

# Only keep planets with at least one recipe
yaml_output = {"planets": [p for p in planets_dict.values() if p["recipes"]]}

# Sort planets by name (case-insensitive)
yaml_output["planets"] = sorted(yaml_output["planets"], key=lambda p: p["name"].lower())

with open("empire_output.yaml", "w", encoding="utf-8") as f:
    yaml.dump(yaml_output, f, sort_keys=False, allow_unicode=True)

print("YAML file generated: empire_output.yaml") 