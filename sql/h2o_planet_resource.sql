-- SQLite
with base_calculations as (
    select 
        planet.natural_id as planet,
        item.symbol as item,
        resource.factor as raw_concentration,
        -- Calculate H2O production per day using RIG formula: (RawConcentration * 100) * 0.7
        ((resource.factor * 100) * 0.6) as units_per_day,
        -- Convert milliseconds to hours (divide by 3600000)
        (cast(recipe.time_ms as float) / 3600000.0) as recipe_hours_decimal
    from planets as planet
        join planet_resources as resource on planet.natural_id = resource.planet_natural_id
        join items as item on resource.material_id = item.material_id
        join recipes as recipe on recipe.building_symbol = 'COL'
    where
        planet.natural_id in ('UV-351a')
        and resource.factor > 0
        and item.symbol = 'O'
)
select 
    planet,
    item,
    raw_concentration,
    units_per_day,
    recipe_hours_decimal,
    (units_per_day / (24/recipe_hours_decimal)) as units_per_cycle
from base_calculations;