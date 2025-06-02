SELECT 
    p.natural_id as planet_id,
    p.name as planet_name,
    s.name as system_name,
    cp.*
FROM planets p
JOIN systems s ON p.system_id = s.system_id
JOIN cogc_programs cp ON p.natural_id = cp.planet_natural_id
ORDER BY s.name, p.name, cp.start_epoch_ms; 