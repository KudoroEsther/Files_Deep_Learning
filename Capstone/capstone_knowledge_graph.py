import re
from pathlib import Path
from docx import Document

WEEK_RE = re.compile(r"\bWEEK\s*(ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|\d+)\b", re.IGNORECASE)

WORD_TO_NUM = {
    "ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5,
    "SIX": 6, "SEVEN": 7, "EIGHT": 8, "NINE": 9, "TEN": 10
}

def normalize_week(token: str) -> int:
    token = token.strip().upper()
    if token.isdigit():
        return int(token)
    return WORD_TO_NUM.get(token, -1)

def slug(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s_]", "", s)
    s = re.sub(r"\s+", "_", s).strip("_")
    return s[:80] if s else "unknown"

def extract_weeks_topics(docx_path: Path):
    doc = Document(docx_path)
    lines = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
    results = []
    i = 0
    while i < len(lines):
        m = WEEK_RE.search(lines[i])
        if not m:
            i += 1
            continue

        week_num = normalize_week(m.group(1))
        # Heuristic: topic is usually on same line after WEEK, or in next 1–3 lines
        topic = lines[i]
        topic = re.sub(WEEK_RE.pattern, "", topic, flags=re.IGNORECASE).strip(" :-–—\t")
        if not topic:
            # look ahead
            for j in range(i+1, min(i+4, len(lines))):
                cand = lines[j]
                # stop if next week begins
                if WEEK_RE.search(cand):
                    break
                if len(cand) >= 3:
                    topic = cand
                    break

        if week_num > 0 and topic:
            results.append({"week": week_num, "topic": topic})
        i += 1

    # De-duplicate by week, keep first
    seen = set()
    clean = []
    for r in results:
        if r["week"] in seen:
            continue
        seen.add(r["week"])
        clean.append(r)
    clean.sort(key=lambda x: x["week"])
    return clean

def generate_cypher(resource_id: str, title: str, subject: str, term: str, class_level: str, week_topics):
    cy = []
    cy.append("CREATE CONSTRAINT resource_id_unique IF NOT EXISTS FOR (r:Resource) REQUIRE r.resource_id IS UNIQUE;")
    cy.append("CREATE CONSTRAINT week_id_unique IF NOT EXISTS FOR (w:Week) REQUIRE w.week_id IS UNIQUE;")
    cy.append("CREATE CONSTRAINT concept_id_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.concept_id IS UNIQUE;")
    cy.append("CREATE INDEX concept_name_idx IF NOT EXISTS FOR (c:Concept) ON (c.name);")
    cy.append("")
    cy.append(f"MERGE (r:Resource {{resource_id: '{resource_id}'}})")
    cy.append(f"SET r.title = '{title}', r.subject='{subject}', r.term='{term}', r.class='{class_level}';")
    cy.append("")

    # Weeks + concepts + teaches
    for wt in week_topics:
        week = wt["week"]
        topic = wt["topic"].replace("'", "\\'")
        week_id = f"{resource_id}_w{week}"
        concept_id = f"{resource_id}_c_{slug(topic)}"
        cy.append(f"MERGE (w:Week {{week_id:'{week_id}'}}) SET w.week_number={week};")
        cy.append(f"MATCH (r:Resource {{resource_id:'{resource_id}'}}) MERGE (r)-[:HAS_WEEK]->(w);")
        cy.append(f"MERGE (c:Concept {{concept_id:'{concept_id}'}})")
        cy.append(f"SET c.name='{topic}', c.subject='{subject}', c.term='{term}', c.class='{class_level}';")
        cy.append(f"MERGE (w)-[:TEACHES]->(c);")
        cy.append("")

    # Prerequisites by week order
    cy.append("// Prerequisites inferred from week order")
    cy.append(f"MATCH (r:Resource {{resource_id:'{resource_id}'}})-[:HAS_WEEK]->(w1:Week)-[:TEACHES]->(c1:Concept)")
    cy.append(f"MATCH (r)-[:HAS_WEEK]->(w2:Week)-[:TEACHES]->(c2:Concept)")
    cy.append("WHERE w2.week_number = w1.week_number + 1")
    cy.append("MERGE (c1)-[rel:PREREQUISITE_OF]->(c2)")
    cy.append("SET rel.method='inferred', rel.evidence='Week ordering in scheme of work';")
    return "\n".join(cy)

if __name__ == "__main__":
    docx_path = Path("1ST TERM J1 BASIC SCIENCE.docx")  # change if needed
    week_topics = extract_weeks_topics(docx_path)

    # You can tweak these metadata fields once; everything else auto-extracts
    resource_id = "jss1_basic_science_term1"
    title = "JSS1 Basic Science - First Term"
    subject = "Basic Science"
    term = "First Term"
    class_level = "JSS1"

    cypher = generate_cypher(resource_id, title, subject, term, class_level, week_topics)
    out = Path("basic_science_curriculum_load.cypher")
    out.write_text(cypher, encoding="utf-8")
    print(f"Wrote {out} with {len(week_topics)} weeks/topics extracted.")