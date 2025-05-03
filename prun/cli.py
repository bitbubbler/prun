# mypy: ignore-errors
import logging
import traceback
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from yaml import YAMLError

from prun.config import Empire, Planet
from prun.di import container
from prun.errors import (
    RecipeNotFoundError,
    MultipleRecipesError,
    PlanetResourceRequiredError,
)
from prun.models import PlanetResource, Planet
from prun.services.cost_service import CalculatedCOGM


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    # Set exc_info=True for all error logs
    logging.getLogger().error = lambda msg, *args, **kwargs: logging.getLogger()._error(
        msg, *args, exc_info=True, **kwargs
    )


@click.group()
def cli():
    """PrUn COGM - Production Economics Tracker"""
    setup_logging()


@cli.command()
@click.option("--username", "-u", required=True, help="FIO API username")
@click.option("--password", "-p", required=False, help="FIO API password")
@click.option("--apikey", "-k", required=False, help="FIO API password")
def sync(username: str, password: str, apikey: str | None):
    """Sync data from the FIO API"""
    logger = logging.getLogger(__name__)
    fio_client = container.fio_client()
    if apikey:
        fio_client.authenticate(apikey=apikey)
    elif password:
        fio_client.authenticate(username=username, password=password)

    logger.info("Starting sync operations")
    # Sync in order of dependencies
    logger.info("Syncing materials...")
    container.item_service().sync_materials()  # Must sync materials first

    logger.info("Syncing recipes...")
    container.recipe_service().sync_recipes()  # Recipes depend on buildings

    logger.info("Syncing buildings...")
    container.building_service().sync_buildings()  # Buildings depend on materials for costs

    logger.info("Syncing comex exchanges...")
    container.exchange_service().sync_comex_exchanges()  # Sync exchanges before prices

    logger.info("Syncing prices...")
    container.exchange_service().sync_prices()  # Prices depend on exchanges

    logger.info("Syncing systems...")
    container.system_service().sync_systems()  # Systems must be synced before planets

    logger.info("Syncing planets...")
    container.planet_service().sync_planets()  # Planets depend on systems

    logger.info("Syncing workforce needs...")
    container.workforce_service().sync_workforce_needs()  # Workforce needs depend on materials

    logger.info("Syncing sites...")
    container.site_service().sync_sites(
        username
    )  # Sites depend on planets and buildings

    logger.info("Syncing warehouses...")
    container.warehouse_service().sync_warehouses(
        username
    )  # Warehouses must be synced before storage

    logger.info("Syncing storage...")
    container.storage_service().sync_storage(
        username
    )  # Storage depends on materials and warehouses

    logger.info("Sync completed successfully")
    logger.info("Cleaning up resources")
    container.shutdown_resources()


@cli.command()
@click.option("--username", "-u", required=True, help="FIO API username")
@click.option("--password", "-p", required=True, help="FIO API password")
def sync_storage(username: str, password: str):
    """Sync storage data from the FIO API"""
    fio_client = container.fio_client()
    fio_client.authenticate(username=username, password=password)
    container.storage_service().sync_storage(username)


def print_cogm_analysis(result: CalculatedCOGM, item_symbol: str):
    """Print COGM analysis in a formatted table.

    Args:
        result: The calculated COGM result
        item_symbol: The symbol of the item being analyzed
    """
    console = Console()

    # Create a simple table showing just the COGM
    cost_table = Table(title=f"COGM Analysis for {item_symbol}")
    cost_table.add_column("Metric", style="cyan")
    cost_table.add_column("Value", justify="right", style="green")

    # Show input costs per unit
    for input_cost in result.input_costs.inputs:
        cost_table.add_row(
            f"Input: {input_cost.item_symbol}", f"{input_cost.total:,.2f}"
        )

    cost_table.add_row("Input Cost", f"{result.input_costs.total:,.2f}")

    # Show workforce cost per unit
    for input_cost in result.workforce_cost.inputs:
        cost_table.add_row(
            f"Workforce {input_cost.workforce_type}: {input_cost.item_symbol}",
            f"{input_cost.total:,.2f}",
        )

    # show workforce cost per recipe run
    cost_table.add_row("Workforce Cost", f"{result.workforce_cost.total:,.2f}")

    # Show repair cost per unit
    cost_table.add_row("Repair Cost", f"{result.repair_cost:,.2f}")

    # Show total COGM per unit
    cost_table.add_row("Total COGM", f"{result.total_cost:,.2f}", style="bold")

    console.print(cost_table)


@cli.command()
@click.argument("item_symbol")
@click.option(
    "--planet",
    "-p",
    "planet_natural_id",
    help="Planet ID (required)",
)
@click.option(
    "--building",
    "-b",
    "building_symbol",
    help="Building symbol (required if item_symbol is a planet resource)",
)
@click.option(
    "--recipe",
    "-r",
    "recipe_symbol",
    help="Specific recipe to use (required if multiple recipes exist)",
)
def cogm(
    item_symbol: str,
    planet_natural_id: str,
    building_symbol: str | None,
    recipe_symbol: str | None,
):
    """Calculate Cost of Goods Manufactured (COGM) for an item.

    Example: cogm RAT -q 10 -r 'FP:1xALG-1xMAI-1xNUT=>10xRAT'
    """
    planet: Planet | None = None
    planet_resource: PlanetResource | None = None

    def get_buy_price(item_symbol: str) -> float:
        return container.exchange_service().get_buy_price(
            exchange_code="AI1", item_symbol=item_symbol
        )

    try:
        cost_service = container.cost_service()
        planet_service = container.planet_service()
        recipe_service = container.recipe_service()
        building_service = container.building_service()

        # try to find the planet, it's required
        planet = planet_service.get_planet(planet_natural_id)
        # also try to find the building here, it's optional though
        building = building_service.get_building(building_symbol)

        if not planet:
            raise ValueError("Planet is required")

        # try to find the planet resource
        planet_resource = next(
            (
                resource
                for resource in planet.resources
                if resource.item.symbol == item_symbol
            ),
            None,
        )
        try:
            recipe = recipe_service.find_recipe(
                item_symbol=item_symbol,
                recipe_symbol=recipe_symbol,
                planet_resource=planet_resource,
            )
        except PlanetResourceRequiredError as e:
            console.print(f"[red]Error:[/red] {str(e)}")
            return

        result: CalculatedCOGM = cost_service.calculate_cogm(
            recipe=recipe,
            planet=planet,
            item_symbol=item_symbol,
            get_buy_price=get_buy_price,
        )
        print_cogm_analysis(result, item_symbol)

    except MultipleRecipesError as e:
        console = Console()
        console.print(f"[red]Error:[/red] {str(e)}")

        # Show available recipes in a table
        recipe_table = Table(title="Available Recipes")
        recipe_table.add_column("Recipe", style="cyan")
        recipe_table.add_column("Building", style="yellow")
        recipe_table.add_column("Inputs", style="green")
        recipe_table.add_column("Outputs", style="green")

        for recipe in e.available_recipes:
            inputs = ", ".join(f"{i.quantity}x {i.item_symbol}" for i in recipe.inputs)
            outputs = ", ".join(
                f"{o.quantity}x {o.item_symbol}" for o in recipe.outputs
            )
            recipe_table.add_row(recipe.symbol, recipe.building_symbol, inputs, outputs)

        console.print()
        console.print(recipe_table)
        console.print("\nUse --recipe/-r to specify which recipe to use.")

        # Print COGM analysis for each available recipe
        for recipe in e.available_recipes:
            console.print(f"\n[bold]Analysis for recipe: {recipe.symbol}[/bold]")
            result = container.cost_service().calculate_cogm(
                recipe=recipe,
                planet=planet,
                item_symbol=item_symbol,
                get_buy_price=get_buy_price,
            )
            print_cogm_analysis(result, item_symbol)

    except ValueError as e:
        traceback.print_exc()
        console = Console()
        console.print(f"[red]Error:[/red] {str(e)}")


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
def analyze_empire(config_file: str):
    """Analyze an empire defined in a YAML configuration file.

    Example: analyze-empire empire.yaml
    """
    cost_service = container.cost_service()
    exchange_service = container.exchange_service()
    planet_service = container.planet_service()
    recipe_service = container.recipe_service()
    console = Console()

    # Load and validate the configuration
    try:
        empire = Empire.from_yaml(config_file)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        return
    except YAMLError as e:
        console.print(f"[red]Error: Invalid YAML file:[/red] {str(e)}")
        return
    except ValueError as e:
        console.print(f"[red]Error: Invalid configuration:[/red] {str(e)}")
        return

    console.print(Panel(f"Analyzing Empire: {empire.name}", style="bold blue"))

    # Create a table for the chain analysis
    chain_table = Table(title="Empire Analysis")
    chain_table.add_column("Step", style="cyan")
    chain_table.add_column("Planet", style="yellow")
    chain_table.add_column("Recipe", style="green")
    chain_table.add_column("Output", style="green")
    chain_table.add_column("COGM", justify="right", style="bold")

    cogm_price_cache: dict[str, float] = {}

    def get_buy_price(item_symbol: str) -> float:
        if empire.material_buy_prices:
            for material, price in empire.material_buy_prices.items():
                if material == item_symbol:
                    return price

        if item_symbol in cogm_price_cache:
            return cogm_price_cache[item_symbol]

        exchange_price = exchange_service.get_buy_price(
            exchange_code="AI1", item_symbol=item_symbol
        )
        return exchange_price

    # Process each recipe in the chain
    def process_empire(do_print: bool = False):
        for empire_planet in empire.planets:
            try:
                # Get the planet resources if planet is specified
                planet: Planet | None = None
                planet_resource: PlanetResource | None = None

                planet = planet_service.get_planet(empire_planet.natural_id)

                for empire_recipe in empire_planet.recipes:
                    planet_resource = next(
                        (
                            resource
                            for resource in planet.resources
                            if resource.item.symbol == empire_recipe.item_symbol
                        ),
                        None,
                    )
                    recipe = recipe_service.find_recipe(
                        item_symbol=empire_recipe.item_symbol,
                        recipe_symbol=empire_recipe.recipe_symbol,
                        planet_resource=planet_resource,
                    )

                    if not recipe:
                        raise RecipeNotFoundError(empire_recipe.recipe_symbol)

                    for output in recipe.outputs:
                        # Calculate COGM for this output
                        output_cogm = cost_service.calculate_cogm(
                            recipe=recipe,
                            planet=planet,
                            item_symbol=output.item_symbol,
                            get_buy_price=get_buy_price,
                        )

                        cogm_price_cache[output.item_symbol] = output_cogm.total_cost

                        if not do_print:
                            continue
                            # Add row to the table
                        chain_table.add_row(
                            f"{planet.name} => {output.item_symbol}",
                            planet.natural_id,
                            recipe.symbol,
                            output.item_symbol,
                            f"{output_cogm.total_cost:,.2f}",
                        )

                        # Print detailed analysis for this output
                        console.print(
                            f"\n[bold]Detailed Analysis for Step {empire_recipe.recipe_symbol} => {output.item_symbol}:[/bold]"
                        )
                        print_cogm_analysis(output_cogm, output.item_symbol)

            except Exception as e:
                # Print the error traceback
                traceback.print_exc()
                console.print(
                    f"[red]Error processing planet {planet.natural_id}:[/red] {str(e)}"
                )
                continue

    # we do two passes
    # the first pass fills the cogm cache
    # the second pass calculates final values and prints the table
    process_empire(do_print=False)
    process_empire(do_print=True)

    # Print the summary table
    console.print("\n[bold]Empire Summary:[/bold]")
    console.print(chain_table)


if __name__ == "__main__":
    cli()
