from fastapi import FastAPI, HTTPException, Depends, Query
from sqlmodel import Session, select, SQLModel, create_engine
from typing import List, Optional
import uvicorn
from sqlmodel import Session
from sqlalchemy.orm import sessionmaker
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel

from fly.models import (
    # Database models
    Building,
    Planet,
    System,
    Item,
    Recipe,
    PlanetResource,
    # Fly models
    EfficientRecipe,
    PlanetExtractionRecipe,
    EmpirePlanetBuilding,
    InternalOffer,
)


# Create FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(
    title="PRUN API",
    description="API for Prosperous Universe data",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Database setup with synchronous engine
DATABASE_URL = "sqlite:///./prun.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)


# Dependency to get database session
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@app.get("/materials", response_model=List[Item])
def get_materials(session: Session = Depends(get_session)):
    materials = session.exec(select(Item)).all()
    return materials


@app.get("/recipes", response_model=List[Recipe])
def get_recipes(session: Session = Depends(get_session)):
    recipes = session.exec(select(Recipe)).all()
    return recipes


@app.get(
    "/planets",
    response_model=List[Planet],
    response_model_include={"__all__": {"natural_id", "name", "system_id", "planet_id"}},
)
def get_planets(
    session: Session = Depends(get_session),
):
    planets = session.exec(select(Planet)).all()
    return planets


@app.get("/buildings", response_model=List[Building])
def get_buildings(session: Session = Depends(get_session)):
    buildings = session.exec(select(Building)).all()
    return buildings


@app.get("/internal-offers")
def get_internal_offers(session: Session = Depends(get_session)):
    offers = session.exec(select(InternalOffer)).all()
    return offers


class InternalOfferCreate(BaseModel):
    item_symbol: str
    price: float
    company: str
    user_name: str


@app.post("/internal-offers", response_model=InternalOffer)
def create_internal_offer(offer: InternalOfferCreate, session: Session = Depends(get_session)):
    # Verify the item exists
    item = session.exec(select(Item).where(Item.symbol == offer.item_symbol)).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Item with symbol {offer.item_symbol} not found")

    new_offer = InternalOffer.model_validate(offer)
    session.add(new_offer)
    session.commit()
    session.refresh(new_offer)
    return new_offer


@app.put("/internal-offers/{offer_id}", response_model=InternalOffer)
def update_internal_offer(offer_id: int, offer: InternalOfferCreate, session: Session = Depends(get_session)):
    # Verify the offer exists
    db_offer = session.exec(select(InternalOffer).where(InternalOffer.id == offer_id)).first()
    if not db_offer:
        raise HTTPException(status_code=404, detail=f"Offer with ID {offer_id} not found")

    # Verify the item exists
    item = session.exec(select(Item).where(Item.symbol == offer.item_symbol)).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Item with symbol {offer.item_symbol} not found")

    # Update the offer
    db_offer.item_symbol = offer.item_symbol
    db_offer.price = offer.price
    db_offer.company = offer.company
    db_offer.user_name = offer.user_name

    session.commit()
    session.refresh(db_offer)
    return db_offer


@app.delete("/internal-offers/{offer_id}", status_code=204)
def delete_internal_offer(offer_id: int, session: Session = Depends(get_session)):
    # Verify the offer exists
    db_offer = session.exec(select(InternalOffer).where(InternalOffer.id == offer_id)).first()
    if not db_offer:
        raise HTTPException(status_code=404, detail=f"Offer with ID {offer_id} not found")

    # Delete the offer
    session.delete(db_offer)
    session.commit()
    return None


if __name__ == "__main__":
    uvicorn.run("fly.main:app", host="0.0.0.0", port=8000, reload=True)
