# mypy: ignore-errors
from decimal import Decimal
from pathlib import Path
import logging
from sqlalchemy.orm import Session

from rich.console import Console
from rich.table import Table

from prun.services.cost_service import CalculatedCOGM

from .di import container
from .services.recipe_service import MultipleRecipesError
import click


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
    container.warehouse_service().sync_warehouses(username)  # Warehouses must be synced before storage

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


def print_cogm_analysis(result: CalculatedCOGM, item_symbol: str, quantity: int):
    """Print COGM analysis in a formatted table.

    Args:
        result: The calculated COGM result
        item_symbol: The symbol of the item being analyzed
        quantity: The quantity of items to calculate for
    """
    console = Console()

    # Calculate output quantity to get per unit costs
    output_quantity = next(
        (output.quantity for output in result.recipe_outputs if output.is_target), 1
    )

    # Calculate per unit costs
    total_cost_per_unit = result.total_cost / output_quantity

    # Create a simple table showing just the COGM
    cost_table = Table(title=f"COGM Analysis for {item_symbol}")
    cost_table.add_column("Metric", style="cyan")
    cost_table.add_column("Value", justify="right", style="green")

    # Show input costs per unit
    for input_cost in result.input_costs:
        per_unit_cost = input_cost.price * input_cost.quantity
        cost_table.add_row(f"Input: {input_cost.item_symbol}", f"{per_unit_cost:,.2f}")

    # Show workforce cost per unit
    workforce_cost_per_unit = result.workforce_cost / output_quantity
    cost_table.add_row("Workforce Cost", f"{workforce_cost_per_unit:,.2f}")

    # Show repair cost per unit
    repair_cost_per_unit = result.repair_cost / output_quantity
    cost_table.add_row("Repair Cost", f"{repair_cost_per_unit:,.2f}")

    # Show total COGM per unit
    cost_table.add_row(
        "Total COGM per unit", f"{total_cost_per_unit:,.2f}", style="bold"
    )

    # Show total for requested quantity
    cost_table.add_row(
        f"Total for {quantity} units",
        f"{total_cost_per_unit * quantity:,.2f}",
        style="bold",
    )

    console.print(cost_table)


@cli.command()
@click.argument("item_symbol")
@click.option(
    "--quantity", "-q", default=1, help="Quantity of items to calculate COGM for"
)
@click.option(
    "--recipe",
    "-r",
    "recipe_symbol",
    help="Specific recipe to use (required if multiple recipes exist)",
)
def cogm(item_symbol: str, quantity: int, recipe_symbol: str | None):
    """Calculate Cost of Goods Manufactured (COGM) for an item.

    Example: cogm RAT -q 10 -r 'FP:1xALG-1xMAI-1xNUT=>10xRAT'
    """
    try:
        result: CalculatedCOGM = container.cost_service().calculate_cogm(
            item_symbol, quantity, recipe_symbol
        )
        print_cogm_analysis(result, item_symbol, quantity)

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
                item_symbol, quantity, recipe.symbol
            )
            print_cogm_analysis(result, item_symbol, quantity)

    except ValueError as e:
        console = Console()
        console.print(f"[red]Error:[/red] {str(e)}")


if __name__ == "__main__":
    cli()
