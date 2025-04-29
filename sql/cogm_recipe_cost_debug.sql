-- COGM recipe cost debugging
select
    recipe.symbol,
    recipe.time_ms,
    recipe.building_symbol as bldg,
    inputs.item_symbol as input,
    inputs.quantity as input_qty,
    outputs.item_symbol as output,
    outputs.quantity as output_qty
from recipes as recipe
   join recipe_inputs as inputs on inputs.recipe_symbol = recipe.symbol
   join recipe_outputs as outputs on outputs.recipe_symbol = recipe.symbol
where recipe.symbol = 'CHP:1xH2O-3xHAL=>1xCL-2xNA'
;