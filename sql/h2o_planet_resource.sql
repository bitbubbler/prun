-- SQLite
select 
    planet.natural_id as planet,
    item.symbol as item,
    resource.factor as factor,
    (select recipe.time_ms from recipes as recipe where recipe.symbol = 'RIG:=>') as base_recipe_time_ms,
    -- Calculate H2O production per cycle (15 * factor, floored)
    floor(15 * resource.factor) as h2o_per_cycle,
    -- Calculate cycle time with factor-based adjustment
    printf('%dh %dm', 
        (17280000 + (case 
            when resource.factor > 0.6 then 300000  -- +5m for high factor
            when resource.factor > 0.5 then 780000  -- +13m for medium factor
            else -480000                            -- -8m for low factor
        end)) / (1000 * 60 * 60),
        ((17280000 + (case 
            when resource.factor > 0.6 then 300000
            when resource.factor > 0.5 then 780000
            else -480000
        end)) / (1000 * 60)) % 60
    ) as cycle_time
from planets as planet
    join planet_resources as resource on planet.natural_id = resource.planet_natural_id
    join items as item on resource.material_id = item.material_id
WHERE
    item.symbol = 'H2O'
    and h2o_per_cycle > 10