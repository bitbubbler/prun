import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from fly.config import InternalOfferConfig, InternalOfferIn, CompanyIn
from fly.models.db_models import InternalOffer, Company
from fly.repository import InternalOfferRepository, ItemRepository, CompanyRepository

logger = logging.getLogger(__name__)


class InternalOfferService:
    """Service for managing internal offers."""

    def __init__(
        self,
        company_repository: CompanyRepository,
        item_repository: ItemRepository,
        offer_repository: InternalOfferRepository,
    ):
        """Initialize the internal offer service.

        Args:
            offer_repository: Repository for internal offer operations
            item_repository: Repository for item operations
            company_repository: Repository for company operations
        """
        self.company_repository = company_repository
        self.item_repository = item_repository
        self.offer_repository = offer_repository

    def find_offers_by_item(self, item_symbol: str) -> List[InternalOffer]:
        """Find all offers for a given item symbol.

        Args:
            item_symbol: The symbol of the item to find offers for
        """
        return self.offer_repository.get_offers_by_item(item_symbol)

    def process_offer_config(
        self, config: InternalOfferConfig, force_update: bool = False
    ) -> Tuple[int, int, int, int]:
        """Process a configuration of internal offers.

        Args:
            config: Internal offer configuration
            force_update: Whether to force update existing offers

        Returns:
            Tuple of (added_count, updated_count, skipped_count, errors_count)
        """
        added_count = 0
        updated_count = 0
        skipped_count = 0
        errors_count = 0

        for company_config in config.companies:
            # For each company in the config, process its offers
            for offer in company_config.offers:
                result = self.process_single_offer(company_config, offer, force_update)

                if result == "added":
                    added_count += 1
                elif result == "updated":
                    updated_count += 1
                elif result == "skipped":
                    skipped_count += 1
                elif result == "error":
                    errors_count += 1

        return added_count, updated_count, skipped_count, errors_count

    def process_single_offer(self, company: CompanyIn, offer_item: InternalOfferIn, force_update: bool = False) -> str:
        """Process a single internal offer.

        Args:
            offer_item: Internal offer item
            force_update: Whether to force update existing offers

        Returns:
            Result status: "added", "updated", "skipped", or "error"
        """
        # Check if the item exists
        item = self.item_repository.get_item(offer_item.item_symbol)
        if not item:
            logger.warning(f"Item {offer_item.item_symbol} not found in database. Skipping offer.")
            return "error"

        # Get or create the company
        company = self._get_or_create_company(
            company_name=company.name,
            user_name=company.user_name,
            stock_link=company.stock_link,
        )

        # Check if an offer with this item_symbol and user_name already exists
        existing_offer = self.offer_repository.get_offer_by_item_and_user(
            item_symbol=offer_item.item_symbol,
            user_name=company.user_name,
        )

        if existing_offer:
            logger.info(f"Offer for {offer_item.item_symbol} from {company.user_name} already exists.")
            # Update price and company if they've changed or if force flag is set
            if force_update or existing_offer.price != offer_item.price or existing_offer.company_id != company.id:
                logger.info(
                    f"Updating price from {existing_offer.price} to {offer_item.price} and company to {company.name}"
                )
                # Update only the fields that need to be updated
                existing_offer.price = offer_item.price
                existing_offer.company_id = company.id
                self.offer_repository.update_offer(existing_offer)
                return "updated"
            else:
                logger.info("No changes needed, skipping.")
                return "skipped"

        # Create new offer
        new_offer = InternalOffer(
            item_symbol=offer_item.item_symbol,
            price=offer_item.price,
            company_id=company.id,
            timestamp=datetime.utcnow(),  # Set initial timestamp
        )

        # Add to database
        self.offer_repository.create_offer(new_offer)
        logger.info(f"Added offer: {offer_item.item_symbol} at {offer_item.price} from {company.user_name}")
        return "added"

    def _get_or_create_company(self, company_name: str, user_name: str, stock_link: Optional[str] = None) -> Company:
        """Get or create a company by name and user.

        Args:
            company_name: Company name
            user_name: User name
            stock_link: Optional stock market link

        Returns:
            Company instance
        """
        # Use the company repository instead of the offer repository
        company = self.company_repository.get_company_by_name_and_user(company_name, user_name)

        if company:
            # Update stock_link if provided and different
            if stock_link is not None and company.stock_link != stock_link:
                # Create a modified copy with the new stock_link
                company.stock_link = stock_link
                self.company_repository.update_company(company)
                logger.info(f"Updated stock link for company: {company_name}")
            return company

        # Create a new company
        company = Company(name=company_name, user_name=user_name, stock_link=stock_link)
        self.company_repository.create_company(company)
        logger.info(f"Created new company: {company_name}")
        return company
