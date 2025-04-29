-- SQLite
select 
    *
from recipes
    join recipe_inputs as inputs on recipes.symbol = inputs.recipe_symbol
    join recipe_outputs as outputs on recipes.symbol = outputs.recipe_symbol
    join items as input_item on inputs.item_symbol = input_item.symbol
    join items as output_item on outputs.item_symbol = output_item.symbol
where output_item.symbol = 'H2O'