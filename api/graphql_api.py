"""
GraphQL API for Nova Memory
Flexible querying with GraphQL
"""

import logging
import os
import json
import sqlite3

logger = logging.getLogger(__name__)

try:
    import graphene
    GRAPHENE_AVAILABLE = True
except ImportError:
    GRAPHENE_AVAILABLE = False
    logger.warning("Graphene not available - GraphQL endpoint disabled")


def _get_db_path() -> str:
    return os.getenv("DATABASE_PATH", "nova_memory_v2.db")


def _get_conn():
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


if GRAPHENE_AVAILABLE:

    class Memory(graphene.ObjectType):
        """Memory object in GraphQL"""
        id = graphene.String()
        content = graphene.String()
        agent_id = graphene.String()
        tags = graphene.List(graphene.String)
        created_at = graphene.String()
        updated_at = graphene.String()
        version = graphene.Int()
        access_count = graphene.Int()

    class Agent(graphene.ObjectType):
        """Agent object in GraphQL"""
        agent_id = graphene.String()
        name = graphene.String()
        status = graphene.String()
        capabilities = graphene.List(graphene.String)
        version = graphene.String()

    class SearchResult(graphene.ObjectType):
        """Search result with relevance score"""
        memory = graphene.Field(Memory)
        score = graphene.Float()
        match_type = graphene.String()

    class Query(graphene.ObjectType):
        """GraphQL queries"""

        memory = graphene.Field(Memory, memory_id=graphene.String(required=True))
        memories = graphene.List(
            Memory,
            agent_id=graphene.String(),
            tags=graphene.List(graphene.String),
            limit=graphene.Int(default_value=100),
        )
        search_keyword = graphene.List(
            SearchResult,
            query=graphene.String(required=True),
            limit=graphene.Int(default_value=10),
        )
        agent = graphene.Field(Agent, agent_id=graphene.String(required=True))
        agents = graphene.List(Agent, status=graphene.String())
        system_stats = graphene.JSONString()
        health_check = graphene.JSONString()

        def resolve_memory(self, info, memory_id):
            try:
                conn = _get_conn()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM agents WHERE id = ?", (memory_id,))
                row = cursor.fetchone()
                conn.close()
                if not row:
                    return None
                caps = json.loads(row["capabilities"]) if row["capabilities"] else []
                return Agent(
                    agent_id=row["id"],
                    name=row["name"],
                    status=row["status"],
                    capabilities=caps,
                )
            except Exception:
                return None

        def resolve_memories(self, info, agent_id=None, tags=None, limit=100):
            try:
                conn = _get_conn()
                cursor = conn.cursor()
                sql = "SELECT * FROM memories ORDER BY created_at DESC LIMIT ?"
                cursor.execute(sql, (limit,))
                rows = cursor.fetchall()
                conn.close()
                results = []
                for row in rows:
                    row_tags = json.loads(row["tags"]) if row["tags"] else []
                    if tags and not all(t in row_tags for t in tags):
                        continue
                    results.append(Memory(
                        id=row["id"],
                        content=row["content"],
                        agent_id=row["author"],
                        tags=row_tags,
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        version=row["version"],
                        access_count=row["access_count"],
                    ))
                return results
            except Exception as e:
                logger.error("GraphQL resolve_memories error: %s", e)
                return []

        def resolve_search_keyword(self, info, query, limit=10):
            try:
                conn = _get_conn()
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT m.id, m.content, m.metadata, m.tags, m.author,
                           m.access_count, m.created_at, m.version
                    FROM memories m
                    JOIN memories_fts f ON f.memory_id = m.id
                    WHERE memories_fts MATCH ?
                    ORDER BY rank LIMIT ?
                    """,
                    (query, limit),
                )
                rows = cursor.fetchall()
                conn.close()
                results = []
                for row in rows:
                    row_tags = json.loads(row["tags"]) if row["tags"] else []
                    mem = Memory(
                        id=row["id"],
                        content=row["content"],
                        agent_id=row["author"],
                        tags=row_tags,
                        created_at=row["created_at"],
                        version=row["version"],
                        access_count=row["access_count"],
                    )
                    results.append(SearchResult(memory=mem, score=1.0, match_type="keyword"))
                return results
            except Exception as e:
                logger.error("GraphQL search error: %s", e)
                return []

        def resolve_agent(self, info, agent_id):
            try:
                conn = _get_conn()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
                row = cursor.fetchone()
                conn.close()
                if not row:
                    return None
                caps = json.loads(row["capabilities"]) if row["capabilities"] else []
                return Agent(
                    agent_id=row["id"],
                    name=row["name"],
                    status=row["status"],
                    capabilities=caps,
                )
            except Exception:
                return None

        def resolve_agents(self, info, status=None):
            try:
                conn = _get_conn()
                cursor = conn.cursor()
                if status:
                    cursor.execute("SELECT * FROM agents WHERE status = ?", (status,))
                else:
                    cursor.execute("SELECT * FROM agents")
                rows = cursor.fetchall()
                conn.close()
                results = []
                for row in rows:
                    caps = json.loads(row["capabilities"]) if row["capabilities"] else []
                    results.append(Agent(
                        agent_id=row["id"],
                        name=row["name"],
                        status=row["status"],
                        capabilities=caps,
                    ))
                return results
            except Exception:
                return []

    class CreateMemory(graphene.Mutation):
        class Arguments:
            content = graphene.String(required=True)
            agent_id = graphene.String(required=True)
            tags = graphene.List(graphene.String)

        memory = graphene.Field(Memory)
        success = graphene.Boolean()

        def mutate(self, info, content, agent_id, tags=None):
            import uuid
            import zlib
            mid = str(uuid.uuid4())
            compressed = zlib.compress(content.encode("utf-8"), level=6)
            tags_str = " ".join(tags) if tags else ""

            try:
                conn = _get_conn()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO memories (id, content, compressed, compressed_size, original_size, metadata, tags, author) VALUES (?, ?, 1, ?, ?, NULL, ?, ?)",
                    (mid, compressed.hex(), len(compressed), len(content.encode("utf-8")), json.dumps(tags) if tags else None, agent_id),
                )
                cursor.execute(
                    "INSERT INTO memory_versions (memory_id, version, content) VALUES (?, 1, ?)",
                    (mid, content),
                )
                cursor.execute(
                    "INSERT INTO memories_fts (memory_id, content, tags) VALUES (?, ?, ?)",
                    (mid, content, tags_str),
                )
                conn.commit()
                conn.close()
                return CreateMemory(
                    success=True,
                    memory=Memory(
                        id=mid, content=content, agent_id=agent_id,
                        tags=tags or [], version=1, access_count=0,
                    ),
                )
            except Exception as e:
                logger.error("GraphQL create_memory error: %s", e)
                return CreateMemory(success=False, memory=None)

    class UpdateMemory(graphene.Mutation):
        class Arguments:
            memory_id = graphene.String(required=True)
            content = graphene.String()
            tags = graphene.List(graphene.String)

        memory = graphene.Field(Memory)
        success = graphene.Boolean()

        def mutate(self, info, memory_id, content=None, tags=None):
            try:
                conn = _get_conn()
                cursor = conn.cursor()
                cursor.execute("SELECT version FROM memories WHERE id = ?", (memory_id,))
                row = cursor.fetchone()
                if not row:
                    return UpdateMemory(success=False, memory=None)

                new_version = row["version"] + 1
                updates = ["version = ?", "updated_at = CURRENT_TIMESTAMP"]
                params = [new_version]

                if content is not None:
                    import zlib
                    compressed = zlib.compress(content.encode("utf-8"), level=6)
                    updates.extend(["content = ?", "compressed = 1", "compressed_size = ?", "original_size = ?"])
                    params.extend([compressed.hex(), len(compressed), len(content.encode("utf-8"))])

                if tags is not None:
                    updates.append("tags = ?")
                    params.append(json.dumps(tags))

                params.append(memory_id)
                cursor.execute(f"UPDATE memories SET {', '.join(updates)} WHERE id = ?", params)
                conn.commit()
                conn.close()
                return UpdateMemory(success=True, memory=Memory(id=memory_id, version=new_version))
            except Exception as e:
                logger.error("GraphQL update_memory error: %s", e)
                return UpdateMemory(success=False, memory=None)

    class DeleteMemory(graphene.Mutation):
        class Arguments:
            memory_id = graphene.String(required=True)

        success = graphene.Boolean()
        message = graphene.String()

        def mutate(self, info, memory_id):
            try:
                conn = _get_conn()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM memory_versions WHERE memory_id = ?", (memory_id,))
                cursor.execute("DELETE FROM memories_fts WHERE memory_id = ?", (memory_id,))
                cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
                deleted = cursor.rowcount
                conn.commit()
                conn.close()
                if deleted:
                    return DeleteMemory(success=True, message="Memory deleted")
                return DeleteMemory(success=False, message="Memory not found")
            except Exception as e:
                logger.error("GraphQL delete_memory error: %s", e)
                return DeleteMemory(success=False, message=str(e))

    class Mutation(graphene.ObjectType):
        create_memory = CreateMemory.Field()
        update_memory = UpdateMemory.Field()
        delete_memory = DeleteMemory.Field()

    schema = graphene.Schema(query=Query, mutation=Mutation)

else:
    schema = None


def get_graphql_schema():
    """Get the GraphQL schema"""
    if not GRAPHENE_AVAILABLE:
        logger.warning("GraphQL not available")
        return None
    return schema
