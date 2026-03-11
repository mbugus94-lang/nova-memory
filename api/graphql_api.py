"""
GraphQL API for Nova Memory
Flexible querying with GraphQL
"""

import logging

logger = logging.getLogger(__name__)

try:
    import graphene
    GRAPHENE_AVAILABLE = True
except ImportError:
    GRAPHENE_AVAILABLE = False
    logger.warning("Graphene not available - GraphQL endpoint disabled")


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
        match_type = graphene.String()  # semantic, keyword, etc
    
    class Query(graphene.ObjectType):
        """GraphQL queries"""
        
        # Memory queries
        memory = graphene.Field(
            Memory,
            memory_id=graphene.String(required=True)
        )
        memories = graphene.List(
            Memory,
            agent_id=graphene.String(),
            tags=graphene.List(graphene.String),
            limit=graphene.Int(default_value=100),
        )
        
        # Search queries
        search_semantic = graphene.List(
            SearchResult,
            query=graphene.String(required=True),
            limit=graphene.Int(default_value=5),
        )
        search_keyword = graphene.List(
            SearchResult,
            query=graphene.String(required=True),
            limit=graphene.Int(default_value=10),
        )
        
        # Agent queries
        agent = graphene.Field(
            Agent,
            agent_id=graphene.String(required=True)
        )
        agents = graphene.List(
            Agent,
            status=graphene.String(),
            capability=graphene.String(),
        )
        
        # Stats
        system_stats = graphene.JSONString()
        health_check = graphene.JSONString()
        
        def resolve_memory(self, info, memory_id):
            """Resolve single memory query"""
            # Implementation would call storage backend
            return None
        
        def resolve_memories(self, info, agent_id=None, tags=None, limit=100):
            """Resolve memories query"""
            # Implementation would call storage backend
            return []
        
        def resolve_search_semantic(self, info, query, limit=5):
            """Resolve semantic search"""
            # Implementation would use semantic_search module
            return []
        
        def resolve_agent(self, info, agent_id):
            """Resolve single agent query"""
            # Implementation would call registry
            return None
        
        def resolve_agents(self, info, status=None, capability=None):
            """Resolve agents query"""
            # Implementation would call registry
            return []
    
    class CreateMemory(graphene.Mutation):
        """Mutation to create a memory"""
        class Arguments:
            content = graphene.String(required=True)
            agent_id = graphene.String(required=True)
            tags = graphene.List(graphene.String)
        
        memory = graphene.Field(Memory)
        success = graphene.Boolean()
        
        def mutate(self, info, content, agent_id, tags=None):
            # Implementation would create memory via storage backend
            return CreateMemory(success=False, memory=None)
    
    class UpdateMemory(graphene.Mutation):
        """Mutation to update a memory"""
        class Arguments:
            memory_id = graphene.String(required=True)
            content = graphene.String()
            tags = graphene.List(graphene.String)
        
        memory = graphene.Field(Memory)
        success = graphene.Boolean()
        
        def mutate(self, info, memory_id, content=None, tags=None):
            # Implementation would update memory
            return UpdateMemory(success=False, memory=None)
    
    class DeleteMemory(graphene.Mutation):
        """Mutation to delete a memory"""
        class Arguments:
            memory_id = graphene.String(required=True)
            agent_id = graphene.String(required=True)
        
        success = graphene.Boolean()
        message = graphene.String()
        
        def mutate(self, info, memory_id, agent_id):
            # Implementation would delete memory
            return DeleteMemory(success=False, message="Not implemented")
    
    class Mutation(graphene.ObjectType):
        """GraphQL mutations"""
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
