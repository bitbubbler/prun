# Input Pricing Strategy for Recipe Optimization

This document outlines a framework for determining the maximum price you should pay for recipe inputs to achieve a target profit margin when producing outputs.

## Problem Statement

When manufacturing items using recipes, we need to determine:
- What is the maximum price I'm willing to pay for each input material?
- How do I ensure my target profit margin while staying competitive?
- How do input prices affect the overall profitability of a production chain?

## Core Concept: Reverse Cost Calculation

Instead of calculating profit from known input costs, we work backward from desired profit to determine maximum acceptable input costs.

### Basic Formula

For a recipe with multiple inputs and outputs:

```
Target Selling Price = COGM + Target Profit
COGM = Input Costs + Workforce Costs + Repair Costs
Maximum Input Budget = Target Selling Price - Target Profit - Workforce Costs - Repair Costs
```

## Example Case Study: Silicon (SI) Production

From the production chain data, we have two recipes for producing Silicon (SI):

### Recipe 1: SME:1xC-1xFLX-1xO-3xSIO=>1xSI
- **Inputs**: 1x Carbon (C), 1x Flux (FLX), 1x Oxygen (O), 3x Silicon Oxide (SIO)
- **Output**: 1x Silicon (SI)
- **Building**: Smelter (SME)

### Recipe 2: SME:1xAL-3xSIO=>1xSI
- **Inputs**: 1x Aluminum (AL), 3x Silicon Oxide (SIO)  
- **Output**: 1x Silicon (SI)
- **Building**: Smelter (SME)

## Price Band Framework for Input Pricing

Instead of calculating single maximum prices, we create **price bands** for each input that provide different profitability tiers and purchasing strategies.

### Price Band Structure

For each recipe input, we calculate multiple price points:

```
1. EXCELLENT BUY: Maximizes profit margin (Target Profit + 25%)
2. GOOD BUY: Achieves target profit margin (Target Profit)
3. ACCEPTABLE BUY: Minimum acceptable profit (Target Profit - 50%)
4. BREAK-EVEN: Covers all costs, zero profit
5. LOSS THRESHOLD: Maximum price before operating at a loss
```

### Step 1: Determine Base Economics
1. **Market Research**: Check current selling prices on exchanges
2. **Target Profit**: Define your desired profit per unit (absolute or percentage)
3. **Fixed Costs**: Calculate workforce and repair costs for the recipe

### Step 2: Calculate Price Band Budget Allocations

For Recipe 2 (AL + SIO → SI), we work backward from different profit targets:

```
EXCELLENT Budget = Selling Price - (Target Profit × 1.25) - Fixed Costs
GOOD Budget = Selling Price - Target Profit - Fixed Costs
ACCEPTABLE Budget = Selling Price - (Target Profit × 0.5) - Fixed Costs
BREAK-EVEN Budget = Selling Price - Fixed Costs
```

### Step 3: Distribute Budget Across Inputs with Price Bands

#### Option A: Equal Distribution Strategy
Divide each budget tier equally across all inputs:
```
For EXCELLENT tier:
- AL_price_excellent = (EXCELLENT Budget × AL_weight) / AL_quantity
- SIO_price_excellent = (EXCELLENT Budget × SIO_weight) / SIO_quantity

Where weights are proportional to market price or strategic importance
```

#### Option B: Market-Proportional Strategy
Base allocation on current market prices:
```
Current AL market price: $1000
Current SIO market price: $300
Total current cost: (1 × $1000) + (3 × $300) = $1900

AL allocation = $1000 / $1900 = 52.6%
SIO allocation = $900 / $1900 = 47.4%

For each tier:
AL_price_tier = (Budget_tier × 0.526) / 1
SIO_price_tier = (Budget_tier × 0.474) / 3
```

#### Option C: Strategic Priority Strategy
Allocate more budget to strategically important inputs:
```
Priority weights (must sum to 1.0):
- AL (harder to source): 0.6
- SIO (abundant): 0.4

For each tier:
AL_price_tier = (Budget_tier × 0.6) / 1
SIO_price_tier = (Budget_tier × 0.4) / 3
```

## Advanced Considerations

### Multi-Recipe Optimization

When multiple recipes produce the same output:
1. Calculate the maximum input budget for each recipe
2. Compare total input costs across recipes
3. Select the recipe with the best margin potential
4. Use alternative recipes as backup when input prices fluctuate

### Supply Chain Integration

Consider your entire production chain:
- **Upstream**: If you produce inputs yourself, use your COGM as the "cost"
- **Downstream**: If the output feeds into another recipe, use that profit potential
- **Horizontal**: Consider switching between recipes based on input price fluctuations

### Dynamic Pricing Strategy

Implement rules for adjusting maximum input prices:
```
if current_market_price < (max_input_price × 0.8):
    # Great deal - buy more volume
    purchase_quantity = base_quantity × 1.5
elif current_market_price < max_input_price:
    # Acceptable - normal purchasing
    purchase_quantity = base_quantity
else:
    # Too expensive - reduce or pause purchasing
    purchase_quantity = 0
```

## Implementation in Prun System

### Proposed Models: Price Band Data Structures

```python
class InputPriceBand(BaseModel):
    """Price band for a single recipe input."""
    
    item_symbol: str
    quantity: float
    excellent_buy: float  # Maximum profit scenario
    good_buy: float      # Target profit scenario
    acceptable_buy: float # Minimum profit scenario
    break_even: float    # Zero profit scenario
    loss_threshold: float # Maximum before loss
    current_market_price: Optional[float] = None
    recommendation: str  # "EXCELLENT", "GOOD", "ACCEPTABLE", "AVOID", etc.

class RecipePriceBands(BaseModel):
    """Complete price band analysis for a recipe."""
    
    recipe_symbol: str
    item_symbol: str  # Output item
    planet_name: str
    target_selling_price: float
    target_profit: float
    
    # Fixed costs breakdown
    workforce_cost: float
    repair_cost: float
    fixed_costs_total: float
    
    # Budget allocations for each tier
    excellent_budget: float
    good_budget: float
    acceptable_budget: float
    break_even_budget: float
    
    # Price bands for each input
    input_bands: List[InputPriceBand]
    
    # Overall assessment
    current_profitability: str  # "EXCELLENT", "GOOD", "ACCEPTABLE", "BREAK_EVEN", "LOSS"
    total_current_input_cost: float
    projected_profit: float

class RecipeComparison(BaseModel):
    """Comparison of multiple recipes for the same output."""
    
    item_symbol: str
    planet_name: str
    target_selling_price: float
    target_profit: float
    
    recipe_analyses: List[RecipePriceBands]
    recommended_recipe: str
    reasoning: str
```

### Proposed Service: `InputPricingService`

```python
class InputPricingService:
    def __init__(
        self,
        cost_service: CostService,
        exchange_service: ExchangeService,
        recipe_service: RecipeService,
        planet_service: PlanetService
    ):
        self.cost_service = cost_service
        self.exchange_service = exchange_service
        self.recipe_service = recipe_service
        self.planet_service = planet_service
    
    def calculate_price_bands(
        self, 
        item_symbol: str,
        planet_name: str,
        profit_margin_percent: float,
        recipe_symbol: Optional[str] = None,
        exchange_code: str = "NC1"
    ) -> RecipePriceBands:
        """Calculate price bands automatically from market data.
        
        Args:
            item_symbol: Output item to produce (e.g., "SI")
            planet_name: Planet where production occurs
            profit_margin_percent: Target profit margin (e.g., 25.0 for 25%)
            recipe_symbol: Optional specific recipe, otherwise finds best one
            exchange_code: Exchange to get market prices from
            
        Returns:
            Complete price band analysis with recommendations
        """
        # 1. Get current market selling price for our output automatically
        target_selling_price = self.exchange_service.get_sell_price(
            exchange_code, item_symbol
        )
        
        # 2. Calculate target profit from margin
        target_profit = target_selling_price * (profit_margin_percent / 100)
        
        # 3. Find recipe (or get specified one)
        # 4. Calculate fixed costs using existing cost_service
        # 5. Get current input ask prices (what we'd pay for inputs)
        # 6. Work backward to create price bands and compare with current ask prices
        
    def compare_all_recipes(
        self,
        item_symbol: str,
        planet_name: str,
        profit_margin_percent: float,
        exchange_code: str = "NC1"
    ) -> RecipeComparison:
        """Compare all recipes for an item and recommend the best one."""
        
    def get_market_assessment(
        self,
        item_symbol: str,
        planet_name: str,
        profit_margin_percent: float,
        recipe_symbol: Optional[str] = None,
        exchange_code: str = "NC1"
    ) -> RecipePriceBands:
        """Get current market status with live price data and recommendations."""
```

### CLI Command: `prun input-pricing`

Much simpler! The system automatically calculates target prices and profits:

```bash
# Basic command - calculate price bands for SI production with 25% profit margin
prun input-pricing SI --planet hyalos --margin 25%

# Specify recipe if multiple exist
prun input-pricing SI --recipe "SME:1xAL-3xSIO=>1xSI" --planet hyalos --margin 20%

# Compare all recipes for an item
prun input-pricing SI --planet hyalos --margin 25% --compare-recipes

# Use different exchange for market data
prun input-pricing SI --planet hyalos --margin 25% --exchange AI1

# JSON output for automation
prun input-pricing SI --planet hyalos --margin 25% --json
```

**How it works automatically:**
1. **Target Selling Price**: Looks up current market selling price using `exchange_service.get_sell_price()` (what we can sell our output for)
2. **Target Profit**: Calculates from margin % of selling price 
3. **Fixed Costs**: Uses existing `cost_service` methods for workforce + repair costs
4. **Current Input Prices**: Gets current ask prices using `exchange_service.get_buy_price()` (what we'd pay for inputs)
5. **Price Bands**: Works backward from target values and compares with current ask prices

### Example Output

```
$ prun input-pricing SI --planet hyalos --margin 25%

Silicon (SI) Input Pricing Analysis
Recipe: SME:1xAL-3xSIO=>1xSI (Planet: hyalos)

Market Data (Exchange: NC1):
├─ Current SI Sell Price: $2,450
├─ Target Profit Margin: 25% ($612.50)
└─ Target Profit: $612.50

Production Costs:
├─ Workforce: $85.50
├─ Repair: $45.20
└─ Fixed Costs Total: $130.70

Input Budget Available: $1,707 (Price - Profit - Fixed Costs)

Price Bands for Recipe Inputs:

┌─────────────┬──────────┬───────────┬──────────┬──────────┬─────────────┬─────────────┐
│ Input       │ Quantity │ Excellent │ Good     │ Acceptable│ Break Even  │ Current     │
│             │          │ (35% mrg) │ (25% mrg)│ (12% mrg) │ (0% profit) │ Ask Price   │
├─────────────┼──────────┼───────────┼──────────┼──────────┼─────────────┼─────────────┤
│ AL          │ 1x       │ ≤ $711    │ ≤ $899   │ ≤ $1,018 │ ≤ $1,121    │ $1,050 ✓    │
│ SIO         │ 3x       │ ≤ $213    │ ≤ $269   │ ≤ $305   │ ≤ $336      │ $285 ✓      │
└─────────────┴──────────┴───────────┴──────────┴──────────┴─────────────┴─────────────┘

Assessment: GOOD PROFITABILITY 🟢
├─ Total Current Input Cost: $1,905 (AL: $1,050 ask + SIO: $855 ask)
├─ Actual Profit: $414.30 (16.9% margin)
├─ vs Target: $198 below target margin
└─ Recommendation: PROCEED - Consider finding better SIO suppliers

Alternative Recipe: SME:1xC-1xFLX-1xO-3xSIO=>1xSI
└─ Status: CHECKING... (run with --compare-recipes for full analysis)
```

## Practical Workflow: Using Price Bands

### Daily Operations Workflow

1. **Morning Market Check**
   ```bash
   prun input-pricing SI --planet hyalos --margin 25%
   ```
   - System automatically checks current market prices vs. your price bands
   - Identify which inputs are in "excellent buy" range 
   - Plan purchasing priorities for the day

2. **Purchasing Decisions**
   - **Excellent Band**: Buy maximum quantity, stock up
   - **Good Band**: Normal purchasing, proceed as planned
   - **Acceptable Band**: Buy minimum needed, look for alternatives
   - **Above Break-Even**: Pause production, wait for better prices
   - **Loss Territory**: Definitely halt, find alternative suppliers

3. **Recipe Switching**
   ```bash
   prun input-pricing SI --planet hyalos --margin 25% --compare-recipes
   ```
   - When input prices shift, check if alternative recipes become more profitable
   - System shows best recipe automatically based on current market conditions

### Strategic Planning Workflow

1. **Weekly Analysis**
   - Track which price bands you're consistently operating in
   - Identify patterns in input price volatility
   - Adjust target profits based on market conditions

2. **Supply Chain Optimization**
   - For inputs frequently in "loss territory", consider vertical integration
   - For inputs often in "excellent" territory, increase production volumes
   - Negotiate long-term contracts for critical inputs

3. **Market Opportunity Assessment**
   - When competitors' inputs hit "loss territory", increase your market share
   - When your inputs hit "excellent territory", maximize production

### Alert System Integration

Set up automated alerts:
```python
# Pseudo-code for alert system
if AL_current_price <= AL_excellent_buy:
    send_alert("🟢 AL at EXCELLENT buy price! Current: $X, Target: $Y")
elif AL_current_price >= AL_break_even:
    send_alert("🔴 AL above break-even! Consider halting SI production")
```

## Key Metrics to Track

1. **Price Band Performance**: Percentage of time operating in each band
2. **Input Price Efficiency**: Actual vs. budgeted input costs
3. **Recipe Selection Rate**: How often each recipe is most profitable
4. **Margin Consistency**: Variance in actual profits achieved
5. **Market Timing**: Success rate in buying during excellent/good bands
6. **Production Efficiency**: Capacity utilization vs. input price bands

## Risk Management

### Price Volatility
- Set maximum price limits with safety margins
- Monitor input price trends and adjust strategies
- Maintain multiple supplier relationships

### Supply Disruption
- Keep minimum inventory levels for critical inputs
- Have backup recipes ready for activation
- Monitor competitor activities and market conditions

## Next Steps

1. Implement the `InputPricingService` in the prun system
2. Add CLI commands for input pricing analysis
3. Integrate with existing COGM calculations
4. Create alerts for when input prices exceed thresholds
5. Develop automated purchasing recommendations

This framework provides a systematic approach to input pricing that maximizes profitability while maintaining operational flexibility.
