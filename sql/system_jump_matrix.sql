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
        jp.jumps < 10  -- Reduced max jumps
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
system_programs AS (
    -- Get current program for each system
    SELECT 
        p.system_id,
        GROUP_CONCAT(DISTINCT REPLACE(cp.program_type, 'ADVERTISING_', '')) as current_program
    FROM planets p
    JOIN cogc_programs cp ON p.natural_id = cp.planet_natural_id
    GROUP BY p.system_id
)
-- Generate the final matrix
SELECT 
    s1.system_id as source_system,
    s1.name as source_name,
    sp1.current_program as source_program,
    s2.system_id as target_system,
    s2.name as target_name,
    sp2.current_program as target_program,
    CASE 
        WHEN s1.system_id = s2.system_id THEN 0
        ELSE mj.min_jumps
    END as jumps
FROM systems s1
CROSS JOIN systems s2
LEFT JOIN min_jumps mj ON 
    mj.source_system = s1.system_id AND 
    mj.target_system = s2.system_id
LEFT JOIN system_programs sp1 ON s1.system_id = sp1.system_id
LEFT JOIN system_programs sp2 ON s2.system_id = sp2.system_id
WHERE 
    s1.system_id = s2.system_id  -- Include same system
    OR mj.min_jumps IS NOT NULL  -- Include only reachable systems
ORDER BY s1.system_id, s2.system_id; 