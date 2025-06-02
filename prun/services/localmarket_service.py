import logging
from typing import List
from fio import FIOClientInterface
from prun.models.db_models import LocalMarketAd
from prun.repository import LocalMarketAdRepository
from datetime import datetime

logger = logging.getLogger(__name__)


class LocalMarketService:
    """Service for syncing local market ads."""

    def __init__(self, fio_client: FIOClientInterface, localmarket_repository: LocalMarketAdRepository):
        self.fio_client = fio_client
        self.localmarket_repository = localmarket_repository

    def sync_localmarket_ads(self, planet_natural_id: str) -> None:
        """Sync local market ads for a given planet from the FIO API to the database."""
        logger.info(f"Syncing local market ads for planet {planet_natural_id}")
        fio_ads = self.fio_client.get_localmarket_ads(planet_natural_id)
        # Remove existing ads for this planet
        self.localmarket_repository.delete_ads_by_planet(planet_natural_id)
        ads: List[LocalMarketAd] = []
        now = datetime.utcnow()
        for ad in fio_ads.BuyingAds:
            ads.append(
                LocalMarketAd(
                    ad_type="buy",
                    contract_natural_id=ad.ContractNaturalId,
                    planet_id=ad.PlanetId,
                    planet_natural_id=ad.PlanetNaturalId,
                    planet_name=ad.PlanetName,
                    creator_company_id=ad.CreatorCompanyId,
                    creator_company_name=ad.CreatorCompanyName,
                    creator_company_code=ad.CreatorCompanyCode,
                    delivery_time=ad.DeliveryTime,
                    creation_time_epoch_ms=ad.CreationTimeEpochMs,
                    expiry_time_epoch_ms=ad.ExpiryTimeEpochMs,
                    minimum_rating=ad.MinimumRating,
                    material_id=ad.MaterialId,
                    material_name=ad.MaterialName,
                    material_ticker=ad.MaterialTicker,
                    material_category=ad.MaterialCategory,
                    material_weight=ad.MaterialWeight,
                    material_volume=ad.MaterialVolume,
                    material_amount=ad.MaterialAmount,
                    price=ad.Price,
                    price_currency=ad.PriceCurrency,
                )
            )
        for ad in fio_ads.SellingAds:
            ads.append(
                LocalMarketAd(
                    ad_type="sell",
                    contract_natural_id=ad.ContractNaturalId,
                    planet_id=ad.PlanetId,
                    planet_natural_id=ad.PlanetNaturalId,
                    planet_name=ad.PlanetName,
                    creator_company_id=ad.CreatorCompanyId,
                    creator_company_name=ad.CreatorCompanyName,
                    creator_company_code=ad.CreatorCompanyCode,
                    delivery_time=ad.DeliveryTime,
                    creation_time_epoch_ms=ad.CreationTimeEpochMs,
                    expiry_time_epoch_ms=ad.ExpiryTimeEpochMs,
                    minimum_rating=ad.MinimumRating,
                    material_id=ad.MaterialId,
                    material_name=ad.MaterialName,
                    material_ticker=ad.MaterialTicker,
                    material_category=ad.MaterialCategory,
                    material_weight=ad.MaterialWeight,
                    material_volume=ad.MaterialVolume,
                    material_amount=ad.MaterialAmount,
                    price=ad.Price,
                    price_currency=ad.PriceCurrency,
                )
            )
        for ad in fio_ads.ShippingAds:
            ads.append(
                LocalMarketAd(
                    ad_type="shipping",
                    contract_natural_id=ad.ContractNaturalId,
                    planet_id=ad.PlanetId,
                    planet_natural_id=ad.PlanetNaturalId,
                    planet_name=ad.PlanetName,
                    creator_company_id=ad.CreatorCompanyId,
                    creator_company_name=ad.CreatorCompanyName,
                    creator_company_code=ad.CreatorCompanyCode,
                    delivery_time=ad.DeliveryTime,
                    creation_time_epoch_ms=ad.CreationTimeEpochMs,
                    expiry_time_epoch_ms=ad.ExpiryTimeEpochMs,
                    minimum_rating=ad.MinimumRating,
                    origin_planet_id=ad.OriginPlanetId,
                    origin_planet_natural_id=ad.OriginPlanetNaturalId,
                    origin_planet_name=ad.OriginPlanetName,
                    destination_planet_id=ad.DestinationPlanetId,
                    destination_planet_natural_id=ad.DestinationPlanetNaturalId,
                    destination_planet_name=ad.DestinationPlanetName,
                    cargo_weight=ad.CargoWeight,
                    cargo_volume=ad.CargoVolume,
                    payout_price=ad.PayoutPrice,
                    payout_currency=ad.PayoutCurrency,
                )
            )
        self.localmarket_repository.upsert_ads(ads)
        logger.info(f"Synced {len(ads)} local market ads for planet {planet_natural_id}")
