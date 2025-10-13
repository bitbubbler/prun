import math
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator, Field, model_validator

from .db_models import (
    Building,
    BuildingCost,
    Exchange,
    Planet,
    PlanetResource,
    Recipe,
    RecipeInput,
    RecipeOutput,
    StorageItem,
)

# =========================================================
#
# Fly models are used to represent data in prun-fly.
# These models are never database tables, but they often
# contain data that is stored in the database.
# It's common to build a fly model from one or more database models.
#
# =========================================================


class Experts(BaseModel):
    """Count of experts for each industry."""

    agriculture: int = Field(
        default=0, description="The number of agriculture experts", max_value=5
    )
    chemistry: int = Field(
        default=0, description="The number of chemistry experts", max_value=5
    )
    construction: int = Field(
        default=0, description="The number of construction experts", max_value=5
    )
    electronics: int = Field(
        default=0, description="The number of electronics experts", max_value=5
    )
    food_industries: int = Field(
        default=0, description="The number of food industry experts", max_value=5
    )
    fuel_refining: int = Field(
        default=0, description="The number of fuel refining experts", max_value=5
    )
    manufacturing: int = Field(
        default=0, description="The number of manufacturing experts", max_value=5
    )
    metallurgy: int = Field(
        default=0, description="The number of metallurgy experts", max_value=5
    )
    resource_extraction: int = Field(
        default=0, description="The number of resource extraction experts", max_value=5
    )

    @model_validator(mode="after")
    def validate_total_experts(cls, v: "Experts") -> "Experts":
        """Validate that the total number of experts does not exceed 6."""
        total = sum(
            [
                v.agriculture,
                v.chemistry,
                v.construction,
                v.electronics,
                v.food_industries,
                v.fuel_refining,
                v.manufacturing,
                v.metallurgy,
                v.resource_extraction,
            ]
        )
        if total > 6:
            raise ValueError(f"Total number of experts ({total}) cannot exceed 6")
        return v

    def num_experts(self, expertise: str) -> int:
        return getattr(self, expertise.lower())


# class EfficientRecipe(BaseModel):
#     """Model for efficient recipes in Prosperous Universe. (not a database table)"""

#     symbol: str
#     building_symbol: str
#     time_ms: int
#     inputs: list[RecipeInput]
#     outputs: list[RecipeOutput]
#     building: Building
#     efficiency: float

#     is_resource_extraction_recipe: bool = False

#     @classmethod
#     def efficient_recipe_from(
#         cls, recipe: Recipe, efficiency: float
#     ) -> "EfficientRecipe":
#         """Create an efficient recipe from a normal recipe."""

#         # Calculate the new time_ms based on expert_efficiency
#         # Efficiency reduces time, so we multiply by (1 - efficiency_factor)
#         # Ensure time_ms is an integer
#         effective_time_ms = int(recipe.time_ms * (1.0 - efficiency))

#         efficient_recipe = cls(
#             symbol=recipe.symbol,
#             building_symbol=recipe.building_symbol,
#             time_ms=effective_time_ms,
#             inputs=recipe.inputs,
#             outputs=recipe.outputs,
#             building=recipe.building,
#             efficiency=efficiency,
#         )

#         return efficient_recipe

#     @property
#     def hours_decimal(self) -> float:
#         """Get the recipe time_ms in hours, as a float."""
#         return self.time_ms / 3600000.0

#     @property
#     def percent_of_day(self) -> float:
#         """Get the recipe time_ms as a percentage of a day (31.2 hours / 24 hours). with 2 decimal places."""
#         return round(self.hours_decimal / 24, 2)


# class PlanetExtractionRecipe(BaseModel):
#     """Model for extraction recipes in Prosperous Universe. (not a database table)"""

#     symbol: str
#     building_symbol: str
#     time_ms: int
#     inputs: list[RecipeInput]
#     outputs: list[RecipeOutput]
#     building: Building

#     is_resource_extraction_recipe: bool = True

#     @classmethod
#     def extraction_recipe_from(
#         cls, recipe: Recipe, planet_resource: PlanetResource
#     ) -> "PlanetExtractionRecipe":
#         """Create an extraction recipe from a normal recipe."""

#         if not recipe.is_resource_extraction_recipe:
#             raise ValueError("Recipe is not a resource extraction recipe")

#         daily_extraction = (
#             planet_resource.factor * 100 * 0.7
#             if recipe.building_symbol in ["RIG", "EXT"]
#             else planet_resource.factor * 100 * 0.6
#         )

#         fractional_units_per_run = daily_extraction / (24 / recipe.hours_decimal)

#         remainder_units_per_run = (
#             math.ceil(fractional_units_per_run) - fractional_units_per_run
#         )

#         extraction_units_per_run = math.ceil(fractional_units_per_run)

#         extraction_time_hours_decimal = recipe.hours_decimal + (
#             recipe.hours_decimal * (remainder_units_per_run / fractional_units_per_run)
#         )

#         return cls(
#             symbol=recipe.symbol,
#             building_symbol=recipe.building_symbol,
#             time_ms=int(extraction_time_hours_decimal * 3600000),
#             inputs=[],
#             outputs=[
#                 RecipeOutput(
#                     item_symbol=planet_resource.item.symbol,
#                     quantity=extraction_units_per_run,
#                 )
#             ],
#             building=recipe.building,
#         )

#     @property
#     def hours_decimal(self) -> float:
#         """Get the recipe time_ms in hours, as a float."""
#         return self.time_ms / 3600000.0


# class EfficientPlanetExtractionRecipe(PlanetExtractionRecipe, EfficientRecipe):
#     """Model for efficient extraction recipes in Prosperous Universe. (not a database table)"""

#     @classmethod
#     def efficient_recipe_from(
#         cls, recipe: PlanetExtractionRecipe, efficiency: float
#     ) -> "EfficientPlanetExtractionRecipe":
#         return super().efficient_recipe_from(recipe, efficiency)

#     @classmethod
#     def extraction_recipe_from(
#         cls, recipe: EfficientRecipe, planet_resource: PlanetResource
#     ) -> "EfficientPlanetExtractionRecipe":
#         raise NotImplementedError(
#             "Use PlanetExtractionRecipe.extraction_recipe_from to get a"
#             "PlanetExtractionRecipe, then use EfficientPlanetExtractionRecipe.efficient_recipe_from "
#             "to get an EfficientPlanetExtractionRecipe"
#         )


# class PlanetBuilding(BaseModel):
#     """Model for buildings on a planet."""

#     building: Building
#     planet: Planet
#     building_costs: list[BuildingCost]

#     @classmethod
#     def planet_building_from(
#         cls, building: Building, planet: Planet
#     ) -> "PlanetBuilding":
#         """Create a building from a planet."""
#         building_costs = building.building_costs.copy()
#         if planet.surface:
#             building_costs.append(
#                 BuildingCost(
#                     item_symbol="MCG",
#                     amount=building.area_cost * 4,
#                 )
#             )
#         else:
#             building_costs.append(
#                 BuildingCost(
#                     item_symbol="AEF",
#                     amount=building.area_cost / 3,
#                 )
#             )
#         if planet.pressure < 0.25:
#             building_costs.append(
#                 BuildingCost(item_symbol="SEA", amount=building.area_cost)
#             )
#         elif planet.pressure > 2:
#             building_costs.append(BuildingCost(item_symbol="HSE", amount=1))
#         if planet.gravity < 0.25:
#             building_costs.append(BuildingCost(item_symbol="MGC", amount=1))
#         elif planet.gravity > 2.5:
#             building_costs.append(BuildingCost(item_symbol="BL", amount=1))
#         if planet.temperature < -25:
#             building_costs.append(
#                 BuildingCost(item_symbol="INS", amount=building.area_cost * 10)
#             )
#         elif planet.temperature > 75:
#             building_costs.append(BuildingCost(item_symbol="TSH", amount=1))
#         return cls(
#             building=building,
#             planet=planet,
#             building_costs=building_costs,
#         )


# class EmpirePlanetBuilding(PlanetBuilding):
#     """Model for buildings on a planet, in an empire."""

#     count: int
#     """The count of this type of building on the planet."""

#     production_queue: list["QueueItem"] = []
#     """The production queue for this building."""


# class EmpirePlanetStorage(BaseModel):
#     """Model for a storage facility on a planet in an empire."""

#     planet: Planet
#     """The planet that this storage facility belongs to."""

#     weight_capacity: int
#     """The weight capacity of this storage facility."""

#     volume_capacity: int
#     """The volume capacity of this storage facility."""

#     stored_items: list[StorageItem]
#     """The items stored in this storage facility."""


# class EmpirePlanet(BaseModel):
#     """Model for a planet in an empire."""

#     buildings: list[EmpirePlanetBuilding]
#     """The buildings on the planet."""

#     site_storage: EmpirePlanetStorage | None = None
#     """The base storage facility on the planet."""

#     warehouse_storage: EmpirePlanetStorage | None = None
#     """The warehouse storage facility on the planet."""


class QueueItem(BaseModel):
    """Model for production queue items."""

    recipe: Recipe
    """The recipe to produce."""

    recurring: bool = False
    """Whether this queue item should repeat."""

    quantity: int | None = None
    """The number of runs to perform. If None and recurring=True, runs indefinitely."""

    ratio: float | None = None
    """The ratio of production time to allocate to this recipe. Only valid when recurring=True."""

    @field_validator("ratio")
    @classmethod
    def ratio_must_be_positive_and_not_with_quantity(
        cls, v: float | None, info
    ) -> float | None:
        if v is not None:
            if v <= 0:
                raise ValueError("Ratio must be positive")
            if info.data.get("quantity") is not None:
                raise ValueError("Cannot specify both ratio and quantity")
            if not info.data.get("recurring", False):
                raise ValueError("Ratio can only be used with recurring items")
        return v

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive_and_not_with_ratio(
        cls, v: int | None, info
    ) -> int | None:
        if v is not None:
            if v <= 0:
                raise ValueError("Quantity must be positive")
            if info.data.get("ratio") is not None:
                raise ValueError("Cannot specify both ratio and quantity")
        return v

    @property
    def is_ratio_based(self) -> bool:
        """Whether this queue item uses ratio-based scheduling."""
        return self.recurring and self.ratio is not None

    @property
    def is_quantity_based(self) -> bool:
        """Whether this queue item uses quantity-based scheduling."""
        return self.quantity is not None



class PioneerFulfillment(BaseModel):
    """Pioneer fulfillment."""

    dw: float = 1
    rat: float = 1
    ove: float = 1
    pwo: float = 1
    cof: float = 1


class SettlerFulfillment(BaseModel):
    """Settler fulfillment."""

    dw: float = 1
    rat: float = 1
    exo: float = 1
    pt: float = 1
    rep: float = 1
    kom: float = 1


class TechnicianFulfillment(BaseModel):
    """Technician fulfillment."""

    dw: float = 1
    rat: float = 1
    med: float = 1
    hms: float = 1
    scn: float = 1
    ale: float = 1
    sc: float = 1


class EngineerFulfillment(BaseModel):
    """Engineer fulfillment."""

    dw: float = 1
    fim: float = 1
    med: float = 1
    hss: float = 1
    pda: float = 1
    gin: float = 1
    vg: float = 1


class ScientistFulfillment(BaseModel):
    """Scientist fulfillment."""

    dw: float = 1
    mea: float = 1
    med: float = 1
    lc: float = 1
    ws: float = 1
    win: float = 1
    nst: float = 1


class WorkforceFulfillment(BaseModel):
    """Workforce fulfillment."""

    pioneer: PioneerFulfillment
    settler: SettlerFulfillment
    technician: TechnicianFulfillment
    engineer: EngineerFulfillment
    scientist: ScientistFulfillment


class MaterialPrice(BaseModel):
    """Model for material prices."""

    symbol: str
    price: float


class ROICalculation(BaseModel):
    """Model for ROI calculations."""

    item_symbol: str
    building_symbol: str
    planet_name: str
    investment: float
    daily_profit: float
    payback_period: float


class BuildingCostDetails(BaseModel):
    """Model for detailed building costs."""

    material: MaterialPrice
    quantity: float
    total_cost: float


class PlanetBuildingCostDetails(BaseModel):
    """Model for detailed planet building costs."""

    base_costs: list[BuildingCostDetails]
    planetary_costs: list[BuildingCostDetails]
    total_cost: float


class InvestmentDetails(BaseModel):
    """Model for investment details."""

    building_costs: PlanetBuildingCostDetails
    total_investment: float


class ReturnDetails(BaseModel):
    """Model for return details."""

    cogm: float
    sell_price: float
    profit_per_unit: float
    daily_profit: float


class DetailedROICalculation(BaseModel):
    """Model for detailed ROI calculations."""

    investment: InvestmentDetails
    return_: ReturnDetails
    payback_period: float


class InputPriceBand(BaseModel):
    """Price band for a single recipe input."""

    item_symbol: str = Field(description="The symbol of the input item")
    quantity: float = Field(description="Quantity needed for recipe")
    excellent_buy: float = Field(description="Maximum profit scenario price")
    good_buy: float = Field(description="Target profit scenario price")
    acceptable_buy: float = Field(description="Minimum profit scenario price")
    break_even: float = Field(description="Zero profit scenario price")
    loss_threshold: float = Field(description="Maximum price before loss")
    current_ask_price: float | None = Field(
        default=None, description="Current market ask price"
    )
    recommendation: str = Field(
        description="Recommendation: EXCELLENT, GOOD, ACCEPTABLE, AVOID, etc."
    )


class RecipePriceBands(BaseModel):
    """Complete price band analysis for a recipe."""

    recipe_symbol: str = Field(description="Recipe symbol")
    item_symbol: str = Field(description="Output item symbol")
    planet_name: str = Field(description="Planet name")
    target_selling_price: float = Field(description="Target selling price")
    target_profit_margin_percent: float = Field(
        description="Target profit margin percentage"
    )
    target_profit: float = Field(description="Target profit amount")

    # Fixed costs breakdown
    workforce_cost: float = Field(description="Workforce cost per recipe run")
    repair_cost: float = Field(description="Repair cost per recipe run")
    fixed_costs_total: float = Field(description="Total fixed costs")

    # Budget allocations for each tier
    excellent_budget: float = Field(description="Budget for excellent profitability")
    good_budget: float = Field(description="Budget for good profitability")
    acceptable_budget: float = Field(description="Budget for acceptable profitability")
    break_even_budget: float = Field(description="Budget for break even")

    # Price bands for each input
    input_bands: list[InputPriceBand] = Field(description="Price bands for each input")

    # Overall assessment
    current_profitability: str = Field(description="Current profitability tier")
    total_current_input_cost: float = Field(description="Total current input cost")
    actual_profit: float = Field(description="Actual profit with current prices")
    actual_margin_percent: float = Field(description="Actual margin percentage")


class RecipeComparison(BaseModel):
    """Comparison of multiple recipes for the same output."""

    item_symbol: str = Field(description="Output item symbol")
    planet_name: str = Field(description="Planet name")
    target_profit_margin_percent: float = Field(
        description="Target profit margin percentage"
    )

    recipe_analyses: list[RecipePriceBands] = Field(
        description="Analysis for each recipe"
    )
    recommended_recipe: str = Field(description="Recommended recipe symbol")
    reasoning: str = Field(description="Reasoning for recommendation")
