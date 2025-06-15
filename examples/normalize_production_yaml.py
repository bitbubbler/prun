import sys
import yaml
import json
from collections import defaultdict

# Usage: python normalize_production_yaml.py input.yaml recipes.txt output.yaml

def load_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_recipes(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_recipe_symbol(symbol):
    # Example: 'FER:1xAMM-3xDW-2xGRN-1xHOP=>6xALE'
    if ':' not in symbol:
        return None, None, None
    building, rest = symbol.split(':', 1)
    if '=>' not in rest:
        return building, [], []
    inputs, outputs = rest.split('=>')
    def parse_side(side):
        items = []
        for part in side.strip().split('-'):
            part = part.strip()
            if not part:
                continue
            if 'x' in part:
                amount, ticker = part.split('x', 1)
                items.append((ticker, int(amount)))
            else:
                items.append((part, 1))
        return items
    return building, parse_side(inputs), parse_side(outputs)

def build_canonical_lookup(recipes):
    # Map from (building_symbol, output tickers tuple) to canonical recipe dict
    lookup = {}
    for r in recipes:
        building = r['BuildingTicker']
        outputs = tuple(sorted(o['Ticker'] for o in r['Outputs']))
        lookup[(building, outputs)] = r
    return lookup

def find_canonical_recipe(recipe_symbol, building_symbol, canonical_lookup):
    # Try to match by building and output tickers
    if ':' in recipe_symbol and '=>' in recipe_symbol:
        building, rest = recipe_symbol.split(':', 1)
        if '=>' in rest:
            _, outputs = rest.split('=>')
            output_tickers = tuple(sorted([part.split('x', 1)[1] for part in outputs.split('-') if 'x' in part]))
            key = (building_symbol, output_tickers)
            return canonical_lookup.get(key)
    return None

def normalize_planet_recipes(planet, canonical_lookup):
    # For each building, keep only the first recipe, normalized
    seen = set()
    new_recipes = []
    for recipe in planet.get('recipes', []):
        bld = recipe['building_symbol']
        if bld in seen:
            continue
        seen.add(bld)
        canon = find_canonical_recipe(recipe['recipe_symbol'], bld, canonical_lookup)
        if canon:
            norm_symbol = canon['StandardRecipeName']
            new_recipe = {
                'building_symbol': canon['BuildingTicker'],
                'recipe_symbol': norm_symbol
            }
            # Preserve item_symbol for EXT, RIG, COL
            if canon['BuildingTicker'] in ("EXT", "RIG", "COL") and 'item_symbol' in recipe:
                new_recipe['item_symbol'] = recipe['item_symbol']
            new_recipes.append(new_recipe)
        else:
            # Fallback: keep the original recipe
            new_recipes.append(recipe)
    planet['recipes'] = new_recipes
    return planet

def main():
    if len(sys.argv) != 4:
        print("Usage: python normalize_production_yaml.py input.yaml recipes.txt output.yaml")
        sys.exit(1)
    input_yaml, recipes_txt, output_yaml = sys.argv[1:4]
    data = load_yaml(input_yaml)
    recipes = load_recipes(recipes_txt)
    canonical_lookup = build_canonical_lookup(recipes)
    for planet in data.get('planets', []):
        # Ensure planet name is a string
        if 'name' in planet:
            planet['name'] = str(planet['name'])
        normalize_planet_recipes(planet, canonical_lookup)
    # Use a custom representer to force strings for building_symbol and recipe_symbol
    class QuotedStr(str):
        pass
    def quoted_str_representer(dumper, data):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')
    class StrDumper(yaml.SafeDumper):
        pass
    StrDumper.add_representer(QuotedStr, quoted_str_representer)
    # Ensure planet name, building_symbol, recipe_symbol, and item_symbol are QuotedStr
    for planet in data.get('planets', []):
        if 'name' in planet:
            planet['name'] = QuotedStr(str(planet['name']))
        for recipe in planet.get('recipes', []):
            if 'building_symbol' in recipe:
                recipe['building_symbol'] = QuotedStr(str(recipe['building_symbol']))
            if 'recipe_symbol' in recipe:
                recipe['recipe_symbol'] = QuotedStr(str(recipe['recipe_symbol']))
            if 'item_symbol' in recipe:
                recipe['item_symbol'] = QuotedStr(str(recipe['item_symbol']))
    with open(output_yaml, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True, Dumper=StrDumper)

if __name__ == '__main__':
    main() 