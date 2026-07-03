"""
Step 2: Seed data chain.

Takes the entity list produced by schema_chain and generates 5-10
realistic records per entity. Realistic-looking data (real names,
plausible prices, valid-looking emails) sells the live demo far more
than placeholder strings like "test1", "test2".
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from app.models.schemas import EntitySpec, SeedDataWrapper

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.6,  # a bit higher than schema_chain: variety helps realism here
    api_key=os.environ.get("GROQ_API_KEY"),
)

structured_llm = llm.with_structured_output(SeedDataWrapper)

seed_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You generate realistic seed data for a REST API. You will be given "
     "a list of entities with their exact field names — you must generate "
     "data ONLY for those entities, using ONLY those field names. Never "
     "invent extra entities or fields that were not given to you.\n\n"
     "For each entity, produce 5 to 10 records as JSON objects. Use "
     "plausible real-world values: real-sounding names, realistic prices, "
     "valid-looking emails and dates.\n\n"
     "Any field ending in _id is a foreign key — its value must reference "
     "an id that actually exists among the records you generate for the "
     "related entity.\n\n"
     "For any free-text field (titles, body text, descriptions, comments, "
     "reviews), write genuinely varied, specific content a real person "
     "would write for that entity. Never use lorem ipsum, never use "
     "meta-commentary like 'this is a sample post' or 'please disregard', "
     "and never use generic placeholders like 'Example content 1' or "
     "'Foo Bar'. Every piece of text should read like something an actual "
     "person wrote about a real topic. Vary sentence structure and topic "
     "across records so they don't all follow the same template."),
    ("human", "Generate seed data only for these exact entities:\n{entities}"),
])

seed_chain = seed_prompt | structured_llm


def generate_seed_data(entities: list[EntitySpec]):
    """Run the seed chain and return {entity_name: [records]}.

    Retries once on failure — Groq's structured output occasionally
    fails to parse its own function call on longer completions, even
    when the underlying data is fine. A single retry catches most of
    these without masking a real, repeated problem.
    """
    entities_text = "\n".join(e.model_dump_json() for e in entities)

    last_error = None
    for attempt in range(2):
        try:
            result = seed_chain.invoke({"entities": entities_text})
            return {record.entity: record.records for record in result.data}
        except Exception as exc:
            last_error = exc
            print(f"  seed generation attempt {attempt + 1} failed, retrying...")

    raise last_error


if __name__ == "__main__":
    from app.chains.schema_chain import generate_entities

    test_prompt = "A blog platform with posts, authors, and comments"
    entities = generate_entities(test_prompt)
    seed = generate_seed_data(entities)
    for entity_name, records in seed.items():
        print(f"--- {entity_name} ({len(records)} records) ---")
        for r in records[:3]:
            print(r)