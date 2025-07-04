WITH RECURSIVE jump_paths AS (
    -- Base case: direct connections (1 jump)
    SELECT 
        s1.system_id as source_system,
        s2.system_id as target_system,
        1 as jumps,
        s1.system_id || ',' || s2.system_id as path
    FROM systems s1
    JOIN systemconnection sc ON s1.system_id = sc.system_id
    JOIN systems s2 ON sc.connecting_id = s2.system_id

    UNION ALL

    -- Recursive case: find paths with more jumps
    SELECT 
        jp.source_system,
        s2.system_id as target_system,
        jp.jumps + 1 as jumps,
        jp.path || ',' || s2.system_id as path
    FROM jump_paths jp
    JOIN systemconnection sc ON jp.target_system = sc.system_id
    JOIN systems s2 ON sc.connecting_id = s2.system_id
    WHERE 
        jp.jumps < 12  -- Only look for paths up to 10 jumps
        AND jp.path NOT LIKE '%' || s2.system_id || '%'  -- Prevent cycles
),
min_jumps AS (
    -- Get minimum jumps between each pair of systems
    SELECT 
        source_system,
        target_system,
        MIN(jumps) as min_jumps
    FROM jump_paths
    GROUP BY source_system, target_system
),
latest_programs AS (
    -- Get the most recent program for each planet
    SELECT 
        planet_natural_id,
        program_type,
        start_epoch_ms,
        ROW_NUMBER() OVER (PARTITION BY planet_natural_id ORDER BY start_epoch_ms DESC) as rn
    FROM cogc_programs
),
resource_extraction_planets AS (
    -- Find triple green planets with RESOURCE_EXTRACTION program
    SELECT 
        p.natural_id as planet_id,
        p.name as planet_name,
        p.system_id,
        s.name as system_name
    FROM planets p
    JOIN systems s ON p.system_id = s.system_id
    JOIN latest_programs lp ON p.natural_id = lp.planet_natural_id
    WHERE lp.program_type LIKE '%RESOURCE_EXTRACTION%'
        AND lp.rn = 1  -- Only get the most recent program
        AND p.gravity >= 0.25 AND p.gravity <= 2.5
        AND p.temperature >= -25 AND p.temperature <= 75
        AND p.pressure >= 0.25 AND p.pressure <= 2.0
),
zv307_jump_paths AS (
    -- Base case: direct connections (1 jump)
    SELECT 
        s1.system_id as source_system,
        s2.system_id as target_system,
        1 as jumps,
        s1.system_id || ',' || s2.system_id as path
    FROM systems s1
    JOIN systemconnection sc ON s1.system_id = sc.system_id
    JOIN systems s2 ON sc.connecting_id = s2.system_id
    WHERE s1.system_id IN (SELECT system_id FROM resource_extraction_planets)

    UNION ALL

    -- Recursive case: find paths with more jumps
    SELECT 
        jp.source_system,
        s2.system_id as target_system,
        jp.jumps + 1 as jumps,
        jp.path || ',' || s2.system_id as path
    FROM zv307_jump_paths jp
    JOIN systemconnection sc ON jp.target_system = sc.system_id
    JOIN systems s2 ON sc.connecting_id = s2.system_id
    WHERE 
        jp.jumps < 12  -- Look for longer paths to ZV-307
        AND jp.path NOT LIKE '%' || s2.system_id || '%'  -- Prevent cycles
),
zv307_distances AS (
    -- Calculate distances to ZV-307 system
    SELECT 
        source_system,
        MIN(jumps) as jumps_to_zv307
    FROM zv307_jump_paths
    WHERE target_system = (SELECT system_id FROM systems WHERE name = 'Antares I')
    GROUP BY source_system
),
agriculture_planets AS (
    -- Find triple green planets with extractable H2O
    SELECT DISTINCT
        p.natural_id as planet_id,
        p.name as planet_name,
        p.system_id,
        s.name as system_name
    FROM planets p
    JOIN systems s ON p.system_id = s.system_id
    JOIN latest_programs lp ON p.natural_id = lp.planet_natural_id
    WHERE lp.program_type LIKE '%AGRICULTURE%'
)
-- Find food planets within 20 jumps of H2O planets
SELECT 
    re.planet_name as resource_extraction_planet_name,
    ap.planet_name as agriculture_planet_name,
    mj.min_jumps as jumps_apart,
    COALESCE(zd.jumps_to_zv307, 999) as jumps_to_zv307
FROM resource_extraction_planets re
JOIN min_jumps mj ON re.system_id = mj.source_system
JOIN agriculture_planets ap ON ap.system_id = mj.target_system
LEFT JOIN zv307_distances zd ON re.system_id = zd.source_system
WHERE mj.min_jumps <= 20 and zd.jumps_to_zv307 < 10
ORDER BY zd.jumps_to_zv307 asc, mj.min_jumps, re.planet_name; 