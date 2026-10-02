from __future__ import annotations

import os
from typing import Any

from neo4j import AsyncGraphDatabase


def _driver():
    uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")
    if not password:
        return None
    return AsyncGraphDatabase.driver(uri, auth=(user, password))


async def upsert_event_graph(*, event_id: str, device_id: str, sender: str | None, urls: list[str]) -> bool:
    driver = _driver()
    if driver is None:
        return False
    try:
        async with driver.session() as session:
            await session.run(
                """
                MERGE (e:SecurityEvent {event_id: $event_id})
                SET e.device_id = $device_id
                WITH e
                FOREACH (_ IN CASE WHEN $sender IS NULL OR $sender = '' THEN [] ELSE [1] END |
                    MERGE (s:Sender {value: $sender})
                    MERGE (s)-[:SENT]->(e))
                WITH e
                UNWIND $urls AS url
                MERGE (u:URL {value: url})
                MERGE (e)-[:CONTAINS]->(u)
                """,
                event_id=event_id,
                device_id=device_id,
                sender=sender,
                urls=urls[:20],
            )
        return True
    except Exception:
        return False
    finally:
        await driver.close()
