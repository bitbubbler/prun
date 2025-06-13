import json
import logging
import traceback
from datetime import datetime

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from yaml import YAMLError
from rich.align import Align
from rich.text import Text
from rich import box
from pydantic import BaseModel

from prun.config import EmpireIn, EmpirePlanetIn, InternalOfferConfig, BuyListConfig
from prun.models import Experts
from prun.di import container
from prun.errors import (
    MultipleRecipesError,
    RecipeNotFoundError,
    RecipeSymbolRequiredError,
)
from prun.services.cost_service import (
    CalculatedRecipeOutputCOGM,
    CalculatedEmpireCOGM,
    CostContext,
)
from prun.database import init_db


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    # Set exc_info=True for all error logs
    logging.getLogger().error = lambda msg, *args, **kwargs: logging.getLogger()._error(  # type: ignore
        msg, *args, exc_info=True, **kwargs
    )


@click.group()
def cli() -> None:
    """PrUn COGM - Production Economics Tracker"""
    setup_logging()


@cli.command()
@click.option("--username", "-u", required=True, help="FIO API username")
@click.option("--password", "-p", required=False, help="FIO API password")
@click.option("--apikey", "-k", required=False, help="FIO API password")
@click.option("--all", "-a", is_flag=True, help="Sync all data")
def sync(username: str, password: str, apikey: str | None, all: bool) -> None:
    """Sync data from the FIO API"""
    logger = logging.getLogger(__name__)
    fio_client = container.fio_client()
    if apikey:
        fio_client.authenticate(apikey=apikey)
    elif password:
        fio_client.authenticate(username=username, password=password)

    logger.info("Starting sync operations")
    # Sync in order of dependencies
    if all:
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

    if all:
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
@click.argument("item_symbol")
@click.option(
    "--planet",
    "-p",
    "planet_natural_id",
    help="Planet ID (required)",
)
@click.option(
    "--recipe",
    "-r",
    "recipe_symbol",
    help="Specific recipe to use (required if multiple recipes exist)",
)
@click.option(
    "--experts",
    "-e",
    "num_experts",
    help="Number of experts to use, defaults to 0. Assumes you know what you're doing (double check you actually have experts for this building)",
    default=0,
)
@click.option(
    "--json",
    is_flag=True,
    help="Output in JSON format",
)
def cogm(
    item_symbol: str,
    planet_natural_id: str,
    recipe_symbol: str | None,
    num_experts: int,
    json: bool,
) -> None:
    """Calculate Cost of Goods Manufactured (COGM) for an item.

    Example usage:
      cogm CL -p LS-300c
      cogm RAT -p KW-688c -r FP:1xALG-1xMAI-1xNUT=>10xRAT

    Note: Only one planet (-p/--planet) should be specified per command.
    """
    stderr_console = Console(stderr=True)
    cogm_price_cache: dict[str, float] = {}

    def get_buy_price(item_symbol: str) -> float:
        buy_price = container.exchange_service().get_buy_price(
            exchange_code="AI1", item_symbol=item_symbol
        )
        if not buy_price:
            raise ValueError(f"No exchange ask_price found for {item_symbol}")
        return buy_price

    def set_cogm_price(item_symbol: str, price: float) -> None:
        buy_price = get_buy_price(item_symbol)
        cogm_price = cogm_price_cache.get(item_symbol)
        # we don't store a cogm price if it's higher than the buy price
        if buy_price < price:
            return
        # only store the new cogm price if it's lower than the existing cogm price
        if cogm_price is None or price < cogm_price:
            cogm_price_cache[item_symbol] = price

    cost_context = CostContext(
        get_buy_price=get_buy_price,
        set_cogm_price=set_cogm_price,
        cogm_price_cache=cogm_price_cache,
    )

    try:
        cost_service = container.cost_service()
        planet_service = container.planet_service()
        recipe_service = container.recipe_service()

        # try to find the planet, it's required
        planet = planet_service.find_planet(planet_natural_id)
        cogc_program = planet_service.get_cogc_program(planet.natural_id).program

        if not planet:
            raise ValueError("Planet is required")

        planet_resource = next(
            (
                resource
                for resource in planet.resources
                if resource.item.symbol == item_symbol
            ),
            None,
        )

        recipe = recipe_service.find_recipe(
            item_symbol=item_symbol,
            recipe_symbol=recipe_symbol,
            planet_resource=planet_resource,
        )

        if not recipe:
            if not recipe_symbol:
                raise RecipeSymbolRequiredError()
            raise RecipeNotFoundError(recipe_symbol)

        experts = Experts()

        setattr(experts, recipe.building.expertise.lower(), num_experts)

        if recipe.is_resource_extraction_recipe:
            efficient_recipe = recipe_service.get_efficient_planet_extraction_recipe(
                recipe_symbol=recipe.symbol,
                planet_resource=planet_resource,
                experts=experts,
                cogc_program=cogc_program,
            )
        else:
            efficient_recipe = recipe_service.get_efficient_recipe(
                recipe_symbol=recipe.symbol,
                experts=experts,
                cogc_program=cogc_program,
            )

        result: CalculatedRecipeOutputCOGM = cost_service.calculate_cogm(
            cost_context=cost_context,
            recipe=efficient_recipe,
            planet=planet,
            item_symbol=item_symbol,
        )
        if json:
            print(result.model_dump_json())
        else:
            print_recipe_cogm_analysis(item_symbol=item_symbol, cogm=result)

    except MultipleRecipesError as e:
        if json:
            print(serialize_exception(e))
        else:
            print_multiple_recipes_error(e)
        exit(1)

    except ValueError as e:
        if json:
            print(serialize_exception(e))
        else:
            traceback.print_exc()
            stderr_console.print(f"[red]Error:[/red] {str(e)}")
        exit(1)


class StockLinkOut(BaseModel):
    company: str
    user_name: str
    stock_link: str


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option(
    "--json",
    is_flag=True,
    help="Output in JSON format",
)
def analyze_empire(config_file: str, json: bool) -> None:
    """Analyze an empire defined in a YAML configuration file.

    Example: analyze-empire empire.yaml
    """
    cost_service = container.cost_service()
    exchange_service = container.exchange_service()
    console = Console()

    # Load and validate the configuration
    try:
        empire = EmpireIn.from_yaml(config_file)
    except FileNotFoundError as e:
        if json:
            print(serialize_exception(e))
        else:
            console.print(f"[red]Error:[/red] {str(e)}")
        exit(1)
    except YAMLError as e:
        if json:
            print(serialize_exception(e))
        else:
            console.print(f"[red]Error: Invalid YAML file:[/red] {str(e)}")
        exit(1)
    except ValueError as e:
        if json:
            print(serialize_exception(e))
        else:
            console.print(f"[red]Error: Invalid configuration:[/red] {str(e)}")
        exit(1)

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

        if not exchange_price:
            raise ValueError(f"No exchange price found for {item_symbol}")

        return exchange_price

    def set_cogm_price(item_symbol: str, price: float) -> None:
        cogm_price_cache[item_symbol] = price

    cost_context = CostContext(
        get_buy_price=get_buy_price,
        set_cogm_price=set_cogm_price,
        cogm_price_cache=cogm_price_cache,
    )

    empire_cogm = cost_service.calculate_empire_cogm(
        cost_context=cost_context,
        empire=empire,
    )

    if json:
        print(empire_cogm.model_dump_json())
    else:
        print_empire_cogm_analysis(empire=empire, empire_cogm=empire_cogm)


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option(
    "--exchange",
    "-e",
    "exchange_code",
    help="Override the exchange code from the config",
    default="AI1",
)
@click.option(
    "--json",
    is_flag=True,
    help="Output in JSON format",
)
def buy_list(config_file: str, exchange_code: str | None, json: bool) -> None:
    """Process a buy list defined in a YAML configuration file and display as a table.

    Calculates the best places to buy each material, prices, and totals.

    Example: buy-list buy_list.yaml
    """
    console = Console()
    exchange_service = container.exchange_service()
    internal_offer_service = container.internal_offer_service()

    # Load and validate the configuration
    try:
        buy_list = BuyListConfig.from_yaml(config_file)
    except FileNotFoundError as e:
        if json:
            print(serialize_exception(e))
        else:
            console.print(f"[red]Error:[/red] {str(e)}")
        exit(1)
    except YAMLError as e:
        if json:
            print(serialize_exception(e))
        else:
            console.print(f"[red]Error: Invalid YAML file:[/red] {str(e)}")
        exit(1)
    except ValueError as e:
        if json:
            print(serialize_exception(e))
        else:
            console.print(f"[red]Error: Invalid configuration:[/red] {str(e)}")
        exit(1)

    # Use provided exchange_code if any, otherwise use the one from config
    if exchange_code:
        buy_list.exchange_code = exchange_code

    # Process each item in the buy list
    results = []
    companies_linked: set[str] = set()
    stock_links: list[StockLinkOut] = []
    total_cost = 0.0

    for planet in buy_list.planets:
        for item_symbol, amount in planet.items.root.items():
            result = {
                "planet": planet.name,
                "material": item_symbol,
                "amount": amount,
                "buy_from": None,
                "buy_at": None,
                "total": 0.0,
            }

            # Get exchange price
            exchange_buy_price = exchange_service.get_buy_price(
                exchange_code=buy_list.exchange_code, item_symbol=item_symbol
            )

            # Get internal price if available
            best_internal_price: float | None = None
            best_internal_seller: str | None = None
            best_internal_seller_stock_link: str | None = None

            internal_offers = internal_offer_service.find_offers_by_item(item_symbol)

            if internal_offers:
                for offer in internal_offers:
                    offer_price = offer.price
                    if not best_internal_price or offer_price < best_internal_price:
                        best_internal_price = offer_price
                        best_internal_seller = offer.company.user_name
                        best_internal_seller_stock_link = offer.company.stock_link

            # Determine where to buy based on price comparison
            if best_internal_price and (
                not exchange_buy_price or best_internal_price < exchange_buy_price
            ):
                result["buy_from"] = best_internal_seller
                result["buy_at"] = best_internal_price
                if best_internal_seller not in companies_linked:
                    companies_linked.add(best_internal_seller)
                    if best_internal_seller_stock_link:
                        stock_links.append(
                            StockLinkOut(
                                company=best_internal_seller,
                                user_name=best_internal_seller,
                                stock_link=best_internal_seller_stock_link,
                            )
                        )
            else:
                result["buy_from"] = buy_list.exchange_code
                result["buy_at"] = exchange_buy_price

            # Calculate total
            result["total"] = result["buy_at"] * amount if result["buy_at"] else 0.0
            total_cost += result["total"]

            results.append(result)

    # Display results
    if json:
        print(
            json.dumps(
                {"buy_list": buy_list.name, "items": results, "total_cost": total_cost}
            )
        )
    else:
        print_buy_list(buy_list.name, results, total_cost, stock_links)


def print_buy_list(
    list_name: str, results: list, total_cost: float, stock_links: list[StockLinkOut]
) -> None:
    """Print buy list in a formatted table."""
    console = Console()

    console.print(Panel(f"Buy List: {list_name}", style="bold blue"))

    table = Table(box=box.SIMPLE)
    table.add_column("planet", style="cyan")
    table.add_column("material", style="green")
    table.add_column("amount", justify="right")
    table.add_column("buy from", style="yellow")
    table.add_column("buy at", justify="right", style="yellow")
    table.add_column("total", justify="right", style="bold")

    for item in results:
        table.add_row(
            item["planet"],
            item["material"],
            str(item["amount"]),
            item["buy_from"] or "-",
            f"${item['buy_at']:,.2f}" if item["buy_at"] else "-",
            f"${item['total']:,.2f}" if item["total"] else "-",
        )

    # Add a grand total row
    table.add_row(
        "",
        "",
        "",
        "",
        "",
        "",
        "[bold]Grand Total:[/bold]",
        f"[bold]${total_cost:,.2f}[/bold]",
    )

    console.print(table)

    company_links_shown: set[str] = set()

    # Print stock links if available
    if len(stock_links) > 0:
        console.print("\n[bold]Stock Links:[/bold]")
        stock_table = Table(box=box.SIMPLE)
        stock_table.add_column("User", style="cyan")
        stock_table.add_column("Stock Link", style="green")

        for stock_link in stock_links:
            if stock_link.user_name in company_links_shown:
                continue
            company_links_shown.add(stock_link.user_name)
            stock_table.add_row(stock_link.user_name, stock_link.stock_link)

        console.print(stock_table)


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--force", "-f", is_flag=True, help="Force update of existing offers")
def insert_offers(config_file: str, force: bool) -> None:
    """Insert internal offers from a YAML configuration file.

    The YAML file should define offers with item symbol, price, user name, and company name.
    Companies can also include an optional stock_link field for stock market references.

    Example: insert-offers internal_offers.yaml
    """
    logger = logging.getLogger(__name__)
    console = Console()

    # Initialize database
    logger.info("Initializing database...")
    init_db()

    # Load and validate the configuration
    try:
        offer_config = InternalOfferConfig.from_yaml(config_file)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        exit(1)
    except YAMLError as e:
        console.print(f"[red]Error: Invalid YAML file:[/red] {str(e)}")
        exit(1)
    except ValueError as e:
        console.print(f"[red]Error: Invalid configuration:[/red] {str(e)}")
        exit(1)

    # Calculate total number of offers across all companies
    total_offers = sum(len(company.offers) for company in offer_config.companies)
    console.print(
        f"Loaded {total_offers} offers from {len(offer_config.companies)} companies"
    )

    # Process offers using the service
    internal_offer_service = container.internal_offer_service()

    # Use a context manager session through the service
    added, updated, skipped, errors = internal_offer_service.process_offer_config(
        config=offer_config, force_update=force
    )

    # Print summary
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  Offers added: {added}")
    console.print(f"  Offers updated: {updated}")
    console.print(f"  Offers skipped (no changes): {skipped}")
    console.print(f"  Errors (items not found): {errors}")
    console.print(f"  Total processed: {added + updated + skipped + errors}")


def print_recipe_cogm_analysis(
    item_symbol: str,
    cogm: CalculatedRecipeOutputCOGM,
) -> None:
    """Print COGM analysis in a formatted table, styled like the provided screenshot."""
    console = Console()

    # --- Parameters Section ---
    parameters_table = Table(show_header=False, box=box.SIMPLE)
    parameters_table.add_column("Label", min_width=16)
    parameters_table.add_column("Value", justify="right")
    parameters_table.add_column("Extra", justify="right")

    # Runtime in hours and minutes
    total_minutes = int(cogm.time_ms // 60000)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    runtime_str = f"{hours}h {minutes:02d}m"
    percent_per_day = (hours + minutes / 60) / 24 * 100
    percent_per_day_str = f"{percent_per_day:.2f} % / Day"

    efficiency = (
        f"{cogm.expert_efficiency * 100:.2f} %"
        if cogm.expert_efficiency is not None
        else "-"
    )
    parameters_table.add_row("[b]Recipe Runtime[/b]", runtime_str, percent_per_day_str)
    parameters_table.add_row("[b]Efficiency[/b]", efficiency, "")

    # --- Cost Section ---
    cost_table = Table(show_header=False, box=box.SIMPLE)
    cost_table.add_column("Label", min_width=16)
    cost_table.add_column("Value", justify="right")
    cost_table.add_column("Extra", justify="right")
    degradation = f"{getattr(cogm, 'repair_cost', '-'):,.2f} $"
    cost_table.add_row("[b]Degradation[/b]", degradation, percent_per_day_str)

    # --- Materials Section ---
    materials_table = Table(title="Materials", box=box.SIMPLE_HEAVY)
    materials_table.add_column("Ticker")
    materials_table.add_column("Units")
    materials_table.add_column("$ / Unit")
    materials_table.add_column("$ Total")
    for input_cost in cogm.input_costs.inputs:
        materials_table.add_row(
            input_cost.item_symbol,
            str(input_cost.quantity),
            f"{input_cost.price:,.2f}",
            f"{input_cost.total:,.2f}",
        )
    materials_table.add_row(
        "[b]Input Total[/b]", "", "", f"{cogm.input_costs.total:,.2f} $"
    )

    # --- Workforce Section ---
    workforce_table = Table(title="Workforce", expand=False, box=box.SIMPLE_HEAVY)
    workforce_table.add_column("Type")
    workforce_table.add_column("Units")
    workforce_table.add_column("$ Total")
    for need in cogm.workforce_cost.needs:
        workforce_table.add_row(
            need.workforce_type.title(), str(need.workforce_count), f"{need.total:,.2f}"
        )
    workforce_table.add_row(
        "[b]Workforce Total[/b]", "", f"{cogm.workforce_cost.total:,.2f} $"
    )

    # --- Total Section ---
    total_cost = cogm.total_cost
    total_panel = Panel(
        f"[b]{total_cost:,.2f} $[/b]",
        title="Total",
        expand=False,
    )

    # --- Cost Of Goods Manufactured Summary Table ---
    summary_table = Table(title="Cost Of Goods Manufactured", box=box.SIMPLE_HEAVY)
    summary_table.add_column("Ticker")
    summary_table.add_column("Units")
    summary_table.add_column("Cost / Split")
    summary_table.add_column("Cost / All Cost")
    summary_table.add_row(
        f"[b]{item_symbol}[/b]", "1", f"{total_cost:,.2f}", f"{total_cost:,.2f}"
    )

    # --- Print All Sections ---
    console.print(
        Panel(parameters_table, title="Parameters", style="bold", expand=False)
    )
    console.print(Panel(cost_table, title="Cost", style="bold", expand=False))
    console.print(materials_table)
    console.print(workforce_table)
    console.print(total_panel)
    console.print(summary_table)


def print_empire_cogm_analysis(
    empire: EmpireIn,
    empire_cogm: CalculatedEmpireCOGM,
) -> None:
    # Print the empire name
    console = Console()
    console.print(Panel(f"Analyzing Empire: {empire.name}", style="bold blue"))

    # Create a table for the chain analysis
    chain_table = Table(title="Empire COGM")
    chain_table.add_column("Step", style="cyan")
    chain_table.add_column("Planet", style="yellow")
    chain_table.add_column("Recipe", style="green")
    chain_table.add_column("Output", style="green")
    chain_table.add_column("Time", style="blue")
    chain_table.add_column("COGM", justify="right", style="bold")

    for planet_cogm in empire_cogm.planets:
        for planet_recipe_output_cogm in planet_cogm.recipes:
            # Convert time_ms to hours and minutes
            total_minutes = int(planet_recipe_output_cogm.time_ms // 60000)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            time_str = f"{hours}h {minutes:02d}m"

            chain_table.add_row(
                f"{planet_cogm.planet_name} => {planet_recipe_output_cogm.item_symbol}",
                planet_cogm.planet_name,
                planet_recipe_output_cogm.recipe_symbol,
                planet_recipe_output_cogm.item_symbol,
                time_str,
                f"{planet_recipe_output_cogm.total_cost:,.2f}",
            )

    # Print the summary table
    console.print(chain_table)


def print_multiple_recipes_error(
    e: MultipleRecipesError,
) -> None:
    """Print error and available recipes when multiple recipes are found.

    Args:
        e: The MultipleRecipesError instance
        planet: The planet being analyzed
        item_symbol: The symbol of the item being analyzed
        get_buy_price: Function to get buy price for an item
    """
    stderr_console = Console(stderr=True)
    stderr_console.print(f"[red]Error:[/red] {str(e)}")

    # Show available recipes in a table
    recipe_table = Table(title="Available Recipes")
    recipe_table.add_column("Recipe", style="cyan")
    recipe_table.add_column("Building", style="yellow")
    recipe_table.add_column("Inputs", style="green")
    recipe_table.add_column("Outputs", style="green")

    for recipe in e.available_recipes:
        inputs = ", ".join(f"{i.quantity}x {i.item_symbol}" for i in recipe.inputs)
        outputs = ", ".join(f"{o.quantity}x {o.item_symbol}" for o in recipe.outputs)
        recipe_table.add_row(recipe.symbol, recipe.building_symbol, inputs, outputs)

    stderr_console.print()
    stderr_console.print(recipe_table)
    stderr_console.print("\nUse --recipe/-r to specify which recipe to use.")


def serialize_exception(exc: Exception) -> str:
    payload = {
        "type": exc.__class__.__name__,
        "message": str(exc),
        "args": exc.args,
        "traceback": traceback.format_exc().splitlines(),  # or leave as one string
    }
    return json.dumps(payload)


@cli.command()
@click.argument("item_pattern", required=True)
@click.option("-p", "planet_pattern", required=False)
@click.option(
    "--json",
    is_flag=True,
    help="Output in JSON format",
)
def recipe_search(
    item_pattern: str | None, planet_pattern: str | None, json: bool
) -> None:
    """Search for recipes by item symbol.

    Examples:
        prun.cli recipe-search h2o
        prun.cli recipe-search CL
    """
    console = Console()
    item_service = container.item_service()
    recipe_service = container.recipe_service()
    planet_service = container.planet_service()

    try:
        item = item_service.find_item(item_pattern)
        planet = planet_service.find_planet(planet_pattern) if planet_pattern else None

        if planet_pattern and not planet:
            console.print(f"[yellow]No planet found named {planet_pattern}[/yellow]")
            return

        if not item:
            console.print("[yellow]No item found[/yellow]")
            return

        recipes = recipe_service.find_all_recipes(
            item_symbol=item.symbol, planet=planet
        )
        if not recipes:
            console.print("[yellow]No recipe found, try including a planet[/yellow]")
            return

        if json:
            print(json.dumps(recipes))
            return

        recipe_table = Table(title="Recipes")
        recipe_table.add_column("Symbol", style="cyan")
        recipe_table.add_column("Building", style="yellow")
        recipe_table.add_column("Inputs", style="green")
        recipe_table.add_column("Outputs", style="green")

        for recipe in recipes:
            inputs = ", ".join(f"{i.quantity}x {i.item_symbol}" for i in recipe.inputs)
            outputs = ", ".join(
                f"{o.quantity}x {o.item_symbol}" for o in recipe.outputs
            )
            recipe_table.add_row(recipe.symbol, recipe.building_symbol, inputs, outputs)

        console.print(recipe_table)

    except (RecipeNotFoundError, RecipeSymbolRequiredError):
        console.print("[yellow]No recipe found[/yellow]")


if __name__ == "__main__":
    cli()
