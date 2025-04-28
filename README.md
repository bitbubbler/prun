# PrUn CLI

A command-line interface for interacting with the PrUn COGM calculator.

## Installation

First, install [uv](https://github.com/astral-sh/uv#installation) if you haven't already.

Then install dependencies:
```bash
uv sync
```

## Commands

### Sync Data

Sync all data from the FIO API:

```bash
python -m prun.cli sync -u YOUR_USERNAME -p YOUR_PASSWORD
```

This command will sync:
- Materials
- Recipes
- Buildings
- Exchange data
- Prices
- Systems
- Planets
- Workforce needs
- Sites
- Warehouses
- Storage

### Sync Storage Only

Sync only storage data:

```bash
python -m prun.cli sync-storage -u YOUR_USERNAME -p YOUR_PASSWORD
```

### Calculate COGM

Calculate the Cost of Goods Manufactured for an item:

```bash
python -m prun.cli cogm ITEM_SYMBOL [--quantity QUANTITY] [--recipe RECIPE]
```

Options:
- `--quantity`, `-q`: Quantity of items to calculate COGM for (default: 1)
- `--recipe`, `-r`: Specific recipe to use (required if multiple recipes exist)

Example:
```bash
python -m prun.cli cogm RAT -q 10 -r 'FP:1xALG-1xMAI-1xNUT=>10xRAT'
```

## Features

- Rich CLI interface with formatted tables
- Detailed cost breakdowns
- Multiple recipe support
- Real-time data synchronization with FIO API

## Requirements

- Python 3.12+
- FIO API credentials 