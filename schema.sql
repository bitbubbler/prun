CREATE TABLE buildings (
	symbol VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	expertise VARCHAR, 
	pioneers INTEGER NOT NULL, 
	settlers INTEGER NOT NULL, 
	technicians INTEGER NOT NULL, 
	engineers INTEGER NOT NULL, 
	scientists INTEGER NOT NULL, 
	area_cost INTEGER NOT NULL, 
	PRIMARY KEY (symbol)
);
CREATE TABLE exchanges (
	comex_exchange_id VARCHAR NOT NULL, 
	exchange_name VARCHAR NOT NULL, 
	exchange_code VARCHAR NOT NULL, 
	exchange_operator_id VARCHAR, 
	exchange_operator_code VARCHAR, 
	exchange_operator_name VARCHAR, 
	currency_numeric_code INTEGER NOT NULL, 
	currency_code VARCHAR NOT NULL, 
	currency_name VARCHAR NOT NULL, 
	currency_decimals INTEGER NOT NULL, 
	location_id VARCHAR NOT NULL, 
	location_name VARCHAR NOT NULL, 
	location_natural_id VARCHAR NOT NULL, 
	PRIMARY KEY (comex_exchange_id)
);
CREATE TABLE items (
	material_id VARCHAR NOT NULL, 
	symbol VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	category VARCHAR NOT NULL, 
	weight FLOAT NOT NULL, 
	volume FLOAT NOT NULL, 
	PRIMARY KEY (symbol)
);
CREATE INDEX ix_items_material_id ON items (material_id);
CREATE TABLE systems (
	system_id VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	natural_id VARCHAR NOT NULL, 
	type VARCHAR NOT NULL, 
	position_x FLOAT NOT NULL, 
	position_y FLOAT NOT NULL, 
	position_z FLOAT NOT NULL, 
	sector_id VARCHAR NOT NULL, 
	sub_sector_id VARCHAR NOT NULL, 
	PRIMARY KEY (system_id)
);
CREATE TABLE warehouses (
	warehouse_id VARCHAR NOT NULL, 
	units INTEGER NOT NULL, 
	weight_capacity FLOAT NOT NULL, 
	volume_capacity FLOAT NOT NULL, 
	next_payment_timestamp_epoch_ms INTEGER NOT NULL, 
	fee_amount FLOAT NOT NULL, 
	fee_currency VARCHAR NOT NULL, 
	fee_collector_id VARCHAR, 
	fee_collector_name VARCHAR, 
	fee_collector_code VARCHAR, 
	location_name VARCHAR NOT NULL, 
	location_natural_id VARCHAR NOT NULL, 
	PRIMARY KEY (warehouse_id)
);
CREATE TABLE building_costs (
	id INTEGER NOT NULL, 
	building_symbol VARCHAR NOT NULL, 
	item_symbol VARCHAR NOT NULL, 
	amount INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(building_symbol) REFERENCES buildings (symbol), 
	FOREIGN KEY(item_symbol) REFERENCES items (symbol)
);
CREATE TABLE exchange_prices (
	id INTEGER NOT NULL, 
	item_symbol VARCHAR NOT NULL, 
	exchange_code VARCHAR NOT NULL, 
	timestamp DATETIME NOT NULL, 
	mm_buy FLOAT, 
	mm_sell FLOAT, 
	average_price FLOAT NOT NULL, 
	ask_amount INTEGER, 
	ask_price FLOAT, 
	ask_available INTEGER, 
	bid_amount INTEGER, 
	bid_price FLOAT, 
	bid_available INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(item_symbol) REFERENCES items (symbol), 
	FOREIGN KEY(exchange_code) REFERENCES exchanges (exchange_code)
);
CREATE TABLE planets (
	natural_id VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	system_id VARCHAR NOT NULL, 
	planet_id VARCHAR NOT NULL, 
	gravity FLOAT NOT NULL, 
	magnetic_field FLOAT NOT NULL, 
	mass FLOAT NOT NULL, 
	mass_earth FLOAT NOT NULL, 
	orbit_semi_major_axis INTEGER NOT NULL, 
	orbit_eccentricity FLOAT NOT NULL, 
	orbit_inclination FLOAT NOT NULL, 
	orbit_right_ascension INTEGER NOT NULL, 
	orbit_periapsis INTEGER NOT NULL, 
	orbit_index INTEGER NOT NULL, 
	pressure FLOAT NOT NULL, 
	radiation FLOAT NOT NULL, 
	radius FLOAT NOT NULL, 
	sunlight FLOAT NOT NULL, 
	surface BOOLEAN NOT NULL, 
	temperature FLOAT NOT NULL, 
	fertility FLOAT NOT NULL, 
	has_local_market BOOLEAN NOT NULL, 
	has_chamber_of_commerce BOOLEAN NOT NULL, 
	has_warehouse BOOLEAN NOT NULL, 
	has_administration_center BOOLEAN NOT NULL, 
	has_shipyard BOOLEAN NOT NULL, 
	faction_code VARCHAR, 
	faction_name VARCHAR, 
	governor_id VARCHAR, 
	governor_user_name VARCHAR, 
	governor_corporation_id VARCHAR, 
	governor_corporation_name VARCHAR, 
	governor_corporation_code VARCHAR, 
	currency_name VARCHAR, 
	currency_code VARCHAR, 
	collector_id VARCHAR, 
	collector_name VARCHAR, 
	collector_code VARCHAR, 
	base_local_market_fee INTEGER NOT NULL, 
	local_market_fee_factor INTEGER NOT NULL, 
	warehouse_fee INTEGER NOT NULL, 
	population_id VARCHAR, 
	cogc_program_status VARCHAR, 
	planet_tier INTEGER NOT NULL, 
	timestamp DATETIME NOT NULL, 
	PRIMARY KEY (natural_id), 
	FOREIGN KEY(system_id) REFERENCES systems (system_id)
);
CREATE TABLE recipes (
	symbol VARCHAR NOT NULL, 
	building_symbol VARCHAR NOT NULL, 
	time_ms INTEGER NOT NULL, 
	PRIMARY KEY (symbol), 
	FOREIGN KEY(building_symbol) REFERENCES buildings (symbol)
);
CREATE TABLE systemconnection (
	system_connection_id VARCHAR NOT NULL, 
	system_id VARCHAR NOT NULL, 
	connecting_id VARCHAR NOT NULL, 
	PRIMARY KEY (system_connection_id), 
	FOREIGN KEY(system_id) REFERENCES systems (system_id), 
	FOREIGN KEY(connecting_id) REFERENCES systems (system_id)
);
CREATE TABLE workforce_needs (
	id INTEGER NOT NULL, 
	workforce_type VARCHAR NOT NULL, 
	item_symbol VARCHAR NOT NULL, 
	amount_per_100_workers_per_day FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(item_symbol) REFERENCES items (symbol)
);
CREATE TABLE cogc_programs (
	id INTEGER NOT NULL, 
	planet_natural_id VARCHAR NOT NULL, 
	program_type VARCHAR, 
	start_epoch_ms DATETIME NOT NULL, 
	end_epoch_ms DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(planet_natural_id) REFERENCES planets (natural_id)
);
CREATE TABLE cogc_votes (
	id INTEGER NOT NULL, 
	planet_natural_id VARCHAR NOT NULL, 
	company_name VARCHAR NOT NULL, 
	company_code VARCHAR, 
	influence FLOAT NOT NULL, 
	vote_type VARCHAR NOT NULL, 
	vote_time_epoch_ms DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(planet_natural_id) REFERENCES planets (natural_id)
);
CREATE TABLE planet_building_requirements (
	id INTEGER NOT NULL, 
	planet_natural_id VARCHAR NOT NULL, 
	item_symbol VARCHAR NOT NULL, 
	amount INTEGER NOT NULL, 
	weight FLOAT NOT NULL, 
	volume FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(planet_natural_id) REFERENCES planets (natural_id), 
	FOREIGN KEY(item_symbol) REFERENCES items (symbol)
);
CREATE TABLE planet_production_fees (
	id INTEGER NOT NULL, 
	planet_natural_id VARCHAR NOT NULL, 
	category VARCHAR NOT NULL, 
	workforce_level VARCHAR NOT NULL, 
	fee_amount INTEGER NOT NULL, 
	fee_currency VARCHAR, 
	PRIMARY KEY (id), 
	FOREIGN KEY(planet_natural_id) REFERENCES planets (natural_id)
);
CREATE TABLE planet_resources (
	id INTEGER NOT NULL, 
	planet_natural_id VARCHAR NOT NULL, 
	material_id VARCHAR NOT NULL, 
	resource_type VARCHAR NOT NULL, 
	factor FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(planet_natural_id) REFERENCES planets (natural_id), 
	FOREIGN KEY(material_id) REFERENCES items (material_id)
);
CREATE TABLE recipe_inputs (
	id INTEGER NOT NULL, 
	recipe_symbol VARCHAR NOT NULL, 
	item_symbol VARCHAR NOT NULL, 
	quantity INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(recipe_symbol) REFERENCES recipes (symbol), 
	FOREIGN KEY(item_symbol) REFERENCES items (symbol)
);
CREATE TABLE recipe_outputs (
	id INTEGER NOT NULL, 
	recipe_symbol VARCHAR NOT NULL, 
	item_symbol VARCHAR NOT NULL, 
	quantity INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(recipe_symbol) REFERENCES recipes (symbol), 
	FOREIGN KEY(item_symbol) REFERENCES items (symbol)
);
CREATE TABLE sites (
	site_id VARCHAR NOT NULL, 
	invested_permits INTEGER NOT NULL, 
	maximum_permits INTEGER NOT NULL, 
	planet_natural_id VARCHAR NOT NULL, 
	PRIMARY KEY (site_id), 
	FOREIGN KEY(planet_natural_id) REFERENCES planets (natural_id)
);
CREATE TABLE site_buildings (
	site_building_id VARCHAR NOT NULL, 
	building_created DATETIME NOT NULL, 
	building_last_repair DATETIME, 
	condition FLOAT NOT NULL, 
	site_id VARCHAR NOT NULL, 
	building_symbol VARCHAR NOT NULL, 
	PRIMARY KEY (site_building_id), 
	FOREIGN KEY(site_id) REFERENCES sites (site_id), 
	FOREIGN KEY(building_symbol) REFERENCES buildings (symbol)
);
CREATE TABLE storages (
	storage_id VARCHAR(32) NOT NULL, 
	addressable_id VARCHAR(32) NOT NULL, 
	name VARCHAR, 
	type VARCHAR NOT NULL, 
	weight_capacity INTEGER NOT NULL, 
	volume_capacity INTEGER NOT NULL, 
	site_id VARCHAR, 
	warehouse_id VARCHAR, 
	PRIMARY KEY (storage_id), 
	FOREIGN KEY(site_id) REFERENCES sites (site_id), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (warehouse_id)
);
CREATE TABLE site_building_materials (
	id INTEGER NOT NULL, 
	amount INTEGER NOT NULL, 
	site_building_id VARCHAR NOT NULL, 
	material_type VARCHAR NOT NULL, 
	item_symbol VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(site_building_id) REFERENCES site_buildings (site_building_id), 
	FOREIGN KEY(item_symbol) REFERENCES items (symbol)
);
CREATE TABLE storage_items (
	id INTEGER NOT NULL, 
	storage_id VARCHAR NOT NULL, 
	item_symbol VARCHAR, 
	amount INTEGER NOT NULL, 
	type VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(storage_id) REFERENCES storages (storage_id), 
	FOREIGN KEY(item_symbol) REFERENCES items (symbol)
);
CREATE TABLE companies (
	id INTEGER NOT NULL, 
	name VARCHAR NOT NULL, 
	user_name VARCHAR NOT NULL, 
	stock_link VARCHAR, 
	PRIMARY KEY (id)
);
CREATE INDEX ix_companies_user_name ON companies (user_name);
CREATE INDEX ix_companies_name ON companies (name);
CREATE TABLE internal_offers (
	id INTEGER NOT NULL, 
	item_symbol VARCHAR NOT NULL, 
	company_id INTEGER NOT NULL, 
	price FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(item_symbol) REFERENCES items (symbol), 
	FOREIGN KEY(company_id) REFERENCES companies (id)
);
