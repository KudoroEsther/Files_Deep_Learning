CREATE CONSTRAINT resource_id_unique IF NOT EXISTS FOR (r:Resource) REQUIRE r.resource_id IS UNIQUE;
CREATE CONSTRAINT week_id_unique IF NOT EXISTS FOR (w:Week) REQUIRE w.week_id IS UNIQUE;
CREATE CONSTRAINT concept_id_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.concept_id IS UNIQUE;
CREATE INDEX concept_name_idx IF NOT EXISTS FOR (c:Concept) ON (c.name);

MERGE (r:Resource {resource_id: 'jss1_basic_science_term1'})
SET r.title = 'JSS1 Basic Science - First Term', r.subject='Basic Science', r.term='First Term', r.class='JSS1';

MERGE (w:Week {week_id:'jss1_basic_science_term1_w1'}) SET w.week_number=1;
MATCH (r:Resource {resource_id:'jss1_basic_science_term1'}) MERGE (r)-[:HAS_WEEK]->(w);
MERGE (c:Concept {concept_id:'jss1_basic_science_term1_c_topic_living_thing_and_non_living_thing_i'})
SET c.name='TOPIC: LIVING THING AND NON LIVING THING (I)', c.subject='Basic Science', c.term='First Term', c.class='JSS1';
MERGE (w)-[:TEACHES]->(c);

MERGE (w:Week {week_id:'jss1_basic_science_term1_w2'}) SET w.week_number=2;
MATCH (r:Resource {resource_id:'jss1_basic_science_term1'}) MERGE (r)-[:HAS_WEEK]->(w);
MERGE (c:Concept {concept_id:'jss1_basic_science_term1_c_topic_living_thing_and_non_living_thing_ii'})
SET c.name='TOPIC: LIVING THING AND NON LIVING THING (II)', c.subject='Basic Science', c.term='First Term', c.class='JSS1';
MERGE (w)-[:TEACHES]->(c);

MERGE (w:Week {week_id:'jss1_basic_science_term1_w3'}) SET w.week_number=3;
MATCH (r:Resource {resource_id:'jss1_basic_science_term1'}) MERGE (r)-[:HAS_WEEK]->(w);
MERGE (c:Concept {concept_id:'jss1_basic_science_term1_c_topic_living_and_non_living_thing_iii'})
SET c.name='TOPIC: LIVING AND NON LIVING THING (III)', c.subject='Basic Science', c.term='First Term', c.class='JSS1';
MERGE (w)-[:TEACHES]->(c);

MERGE (w:Week {week_id:'jss1_basic_science_term1_w4'}) SET w.week_number=4;
MATCH (r:Resource {resource_id:'jss1_basic_science_term1'}) MERGE (r)-[:HAS_WEEK]->(w);
MERGE (c:Concept {concept_id:'jss1_basic_science_term1_c_topic_living_and_non_living_thing_iv'})
SET c.name='TOPIC: LIVING AND NON LIVING THING (IV)', c.subject='Basic Science', c.term='First Term', c.class='JSS1';
MERGE (w)-[:TEACHES]->(c);

MERGE (w:Week {week_id:'jss1_basic_science_term1_w5'}) SET w.week_number=5;
MATCH (r:Resource {resource_id:'jss1_basic_science_term1'}) MERGE (r)-[:HAS_WEEK]->(w);
MERGE (c:Concept {concept_id:'jss1_basic_science_term1_c_topic_human_development'})
SET c.name='TOPIC: HUMAN DEVELOPMENT', c.subject='Basic Science', c.term='First Term', c.class='JSS1';
MERGE (w)-[:TEACHES]->(c);

MERGE (w:Week {week_id:'jss1_basic_science_term1_w6'}) SET w.week_number=6;
MATCH (r:Resource {resource_id:'jss1_basic_science_term1'}) MERGE (r)-[:HAS_WEEK]->(w);
MERGE (c:Concept {concept_id:'jss1_basic_science_term1_c_topic_family_health_sanitation_i'})
SET c.name='TOPIC: FAMILY HEALTH (SANITATION) (I)', c.subject='Basic Science', c.term='First Term', c.class='JSS1';
MERGE (w)-[:TEACHES]->(c);

MERGE (w:Week {week_id:'jss1_basic_science_term1_w7'}) SET w.week_number=7;
MATCH (r:Resource {resource_id:'jss1_basic_science_term1'}) MERGE (r)-[:HAS_WEEK]->(w);
MERGE (c:Concept {concept_id:'jss1_basic_science_term1_c_and_eight'})
SET c.name='AND EIGHT', c.subject='Basic Science', c.term='First Term', c.class='JSS1';
MERGE (w)-[:TEACHES]->(c);

MERGE (w:Week {week_id:'jss1_basic_science_term1_w9'}) SET w.week_number=9;
MATCH (r:Resource {resource_id:'jss1_basic_science_term1'}) MERGE (r)-[:HAS_WEEK]->(w);
MERGE (c:Concept {concept_id:'jss1_basic_science_term1_c_topic_family_health_iii_drug_abuse'})
SET c.name='TOPIC: FAMILY HEALTH (III) DRUG ABUSE', c.subject='Basic Science', c.term='First Term', c.class='JSS1';
MERGE (w)-[:TEACHES]->(c);

// Prerequisites inferred from week order
MATCH (r:Resource {resource_id:'jss1_basic_science_term1'})-[:HAS_WEEK]->(w1:Week)-[:TEACHES]->(c1:Concept)
MATCH (r)-[:HAS_WEEK]->(w2:Week)-[:TEACHES]->(c2:Concept)
WHERE w2.week_number = w1.week_number + 1
MERGE (c1)-[rel:PREREQUISITE_OF]->(c2)
SET rel.method='inferred', rel.evidence='Week ordering in scheme of work';