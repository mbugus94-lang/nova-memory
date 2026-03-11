# OpenClaw + Nova Memory Integration Strategy

**Goal:** Integrate Nova Memory as a distributed memory system for OpenClaw agents WITHOUT modifying OpenClaw source code.

---

## 1. OpenClaw Architecture Deep Dive

### Current Memory System
- **Location:** `~/.openclaw/memory/`
- **Format:** SQLite databases (one per agent/workspace)
- **Examples in your system:**
  - `main.sqlite` - Main agent memory
  - `nova.sqlite` - Nova agent memory
  - `sasha.sqlite` - Sasha agent memory
- **Agent Configuration:** `~/.openclaw/clawdbot.json`
- **Skills Location:** `~/.openclaw/workspace/skills/`
- **Gateway:** WebSocket control plane at `ws://127.0.0.1:18789`

### Current Integration Points
1. **Skills System** - Agents can use SKILL.md files in workspace
2. **Tool System** - Agents have access to predefined tools (browser, canvas, nodes, cron, sessions)
3. **Plugin System** - Extensions via `openclaw.plugin.json` (see: `~/.openclaw/extensions/`)
4. **Workspace Files** - Shared files accessible to agents
5. **Inter-Agent Tools** - `sessions_list`, `sessions_send`, `sessions_history`
6. **Cron System** - Automated task triggers

---

## 2. Integration Approaches (Ranked by Viability)

### ✅ APPROACH A: Skills-Based Integration (★★★★★ Recommended)

**Why:** No infrastructure changes, pure software addition, agents can opt-in per-workspace.

**How:**
1. Create Nova Memory skill files in `~/.openclaw/workspace/skills/nova-memory/`
2. Agents access Nova Memory via `@nova-memory` tool calls
3. Skill provides high-level operations (store, retrieve, search, aggregate)
4. Backed by central Redis + SQLite database

**Files to Create:**
```
~/.openclaw/workspace/skills/nova-memory/
├── SKILL.md                    # Skill documentation + API
├── nova-memory-client.js       # JavaScript client for OpenClaw
├── nova-memory.config.json     # Skill configuration
└── README.md                   # Setup instructions
```

**Example Skill Integration:**
```javascript
// Agents call: @nova-memory:store --key "user:123" --data '{"preference": "verbose"}'
// Returns: { success: true, stored: true }

agent_tool_call("nova_memory:store", {
  key: "user:123",
  data: { preference: "verbose" },
  ttl: 86400  // 24 hours
})
```

---

### ✅ APPROACH B: Memory.db Proxy/Wrapper (★★★★☆ Secondary)

**Why:** Transparent to OpenClaw, intercepts all memory operations automatically.

**How:**
1. Create `~/.openclaw/memory/nova-proxy.js` - Node.js proxy server
2. Patch `sqlite3` require paths to route through Nova Memory
3. Converts SQLite calls → Nova Memory API calls
4. Falls back to local SQLite if Nova Memory unavailable

**Advantages:**
- Completely transparent to agents
- Works with all existing agents automatically
- No code changes needed in agent code

**Challenges:**
- More complex to implement
- Potential performance implications
- Harder to debug

---

### ✅ APPROACH C: Plugin-Based Extension (★★★☆☆ Tertiary)

**Why:** Uses OpenClaw's native extension system.

**How:**
1. Create plugin at `~/.openclaw/extensions/nova-memory-plugin/`
2. Implement `openclaw.plugin.json` with Nova Memory hooks
3. Plugin registers itself as memory provider
4. OpenClaw routes memory calls through plugin

**Configuration:**
```json
{
  "id": "nova-memory-plugin",
  "name": "Nova Memory Provider",
  "configSchema": {
    "properties": {
      "redisUrl": { "type": "string" },
      "databaseUrl": { "type": "string" },
      "enableCaching": { "type": "boolean" }
    }
  }
}
```

---

## 3. Recommended Implementation: Hybrid Approach

### Phase 1: Direct Integration (Immediate)
```
Nova Memory Service (Python)
├── FastAPI @ localhost:8001
├── Redis @ localhost:6379
├── SQLite @ ~/.openclaw/memory/nova-memory.db
└── OpenClaw Skills Interface
```

### Phase 2: Agent Wrapper (1-2 weeks)
```
OpenClaw Agents
├── agents/main
├── agents/sasha
├── agents/wathuge
└── Nova Memory Skills
    ├── nova-memory.store()
    ├── nova-memory.retrieve()
    ├── nova-memory.search()
    └── nova-memory.aggregate()
```

### Phase 3: Transparent Proxy (Optional)
```
Memory Interception Layer
├── Hijack sqlite3 module
├── Route through Nova Memory
└── Fallback to local SQLite
```

---

## 4. Step-by-Step Implementation Plan

### Part A: Setup Nova Memory as OpenClaw Service

**1. Create Nova Memory skill wrapper:**
```bash
mkdir -p ~/.openclaw/workspace/skills/nova-memory
touch ~/.openclaw/workspace/skills/nova-memory/SKILL.md
touch ~/.openclaw/workspace/skills/nova-memory/nova-client.js
touch ~/.openclaw/workspace/skills/nova-memory/nova-memory.config.json
```

**2. SKILL.md content:**
```markdown
# Nova Memory - Distributed Agent Memory System

Provides centralized, distributed memory management for multi-agent systems.

## Installation
Already included in your OpenClaw setup.

## Usage

### Store Memory
@nova-memory --action store --key "agent:session:123" --value '{"data": "..."}' --ttl 86400

### Retrieve Memory  
@nova-memory --action retrieve --key "agent:session:123"

### Search Memory
@nova-memory --action search --query "user preferences" --agent-filter "main"

### List All Keys
@nova-memory --action list --pattern "agent:*"

## Features
- Distributed caching (Redis)
- Persistent storage (SQLite)
- Inter-agent memory sharing
- Semantic search capability
```

**3. NodeJS Client (nova-client.js):**
```javascript
// Simple HTTP client for Nova Memory API
class NovaMemoryClient {
  constructor(apiUrl = 'http://localhost:8001') {
    this.apiUrl = apiUrl;
  }

  async store(key, value, ttl = 86400) {
    const res = await fetch(`${this.apiUrl}/api/v2/memory/store`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key, value, ttl })
    });
    return res.json();
  }

  async retrieve(key) {
    const res = await fetch(`${this.apiUrl}/api/v2/memory/retrieve/${key}`);
    return res.json();
  }

  async search(query, filters = {}) {
    const res = await fetch(`${this.apiUrl}/api/v2/memory/search`, {
      method: 'POST',
      body: JSON.stringify({ query, filters })
    });
    return res.json();
  }
}

module.exports = NovaMemoryClient;
```

### Part B: Create Tool Interface

**Create `~/.openclaw/workspace/tools/nova-memory-tool/`:**

```typescript
// Tool definition for OpenClaw to use Nova Memory
export const novaMemoryTool = {
  id: "nova_memory",
  name: "Nova Memory",
  description: "Store and retrieve distributed agent memory",
  
  inputs: {
    action: {
      type: "enum",
      values: ["store", "retrieve", "search", "list"],
      description: "Memory operation to perform"
    },
    key: {
      type: "string",
      description: "Memory key (format: category:agent:id)"
    },
    value: {
      type: "object",
      description: "Data to store (for store action)"
    }
  },
  
  execute: async (inputs) => {
    const client = new NovaMemoryClient();
    
    switch(inputs.action) {
      case 'store':
        return await client.store(inputs.key, inputs.value);
      case 'retrieve':
        return await client.retrieve(inputs.key);
      case 'search':
        return await client.search(inputs.key);
      case 'list':
        return await client.list(inputs.key);
    }
  }
};
```

### Part C: Agent Configuration

**Update agent configs to include Nova Memory:**

In each agent's workspace, add to `TOOLS.md`:
```markdown
# Nova Memory Integration

## Memory Persistence
All agent memories stored in distributed Nova Memory system.

### Key Patterns
- `agent:{agent_id}:session:{session_id}` - Session data
- `agent:{agent_id}:user:{user_id}` - User preferences
- `agent:{agent_id}:context:{context_id}` - Context windows
- `shared:all_agents:{resource}` - Cross-agent resources

### Example Usage
When persisting user context:
```
STORE IN MEMORY:
Key: agent:main:user:user_123:preferences
Value: {
  "verbose": true,
  "language": "en",
  "timezone": "UTC"
}
```

When retrieving for next session:
```
RETRIEVE FROM MEMORY:
Key: agent:main:user:user_123:preferences
→ Returns { "verbose": true, "language": "en", "timezone": "UTC" }
```
```

---

## 5. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenClaw Agents                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Agent: main  │  │ Agent: sasha  │  │ Agent: wath  │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                 │                │
│         └─────────────────┼─────────────────┘                │
│                           │                                  │
│         ┌─────────────────▼──────────────────┐               │
│         │  OpenClaw Gateway (WS)             │               │
│         │  ws://127.0.0.1:18789              │               │
│         └─────────────────┬──────────────────┘               │
│                           │                                  │
└───────────────────────────┼──────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │     Nova Memory Skill Layer           │
        │  ~/.openclaw/workspace/skills/        │
        │  nova-memory/                         │
        └───────────────┬───────────────────────┘
                        │
        ┌───────────────┴───────────────────┐
        │                                   │
        ▼                                   ▼
   ┌──────────────┐              ┌─────────────────┐
   │   Redis      │              │   SQLite        │
   │ 127.0.0.1    │              │  nova_memory    │
   │ :6379        │              │  .db            │
   └──────────────┘              └─────────────────┘
```

---

## 6. Configuration Files to Create

### File 1: ~/.openclaw/workspace/skills/nova-memory/SKILL.md
```markdown
# Nova Memory Distributed Agent Memory

Provides centralized memory management for coordinated multi-agent systems.

## What It Does
- Stores agent context, user preferences, and session data
- Shares memory across agents without direct access to each agent's database
- Enables semantic search across all agent memory
- Provides memory encryption and access control

## Getting Started

### Basic Store
```
@nova-memory --action store \
  --key "agent:main:session:abc123" \
  --value '{"user_id": 42, "context": "verbose"}' \
  --ttl 86400
```

### Retrieve Memory
```
@nova-memory --action retrieve \
  --key "agent:main:session:abc123"
```

### Search All Memory
```
@nova-memory --action search \
  --query "user preferences" \
  --agent "main"
```

## Key Naming Convention
`{category}:{agent_id}:{entity}:{entity_id}`

Examples:
- `agent:main:session:sess_123`
- `agent:sasha:user:user_456`
- `shared:all:conversation:conv_789`

## Behavior
- Stored in both Redis (cache) and SQLite (persistent)
- TTL default: 24 hours
- Automatic cleanup of expired entries
- Inter-agent access control via policies
```

### File 2: ~/.openclaw/workspace/skills/nova-memory/nova-memory.config.json
```json
{
  "enabled": true,
  "name": "Nova Memory",
  "description": "Distributed agent memory system",
  "version": "2.0.0",
  "api": {
    "baseUrl": "http://127.0.0.1:8001",
    "timeout": 5000,
    "retries": 3
  },
  "features": {
    "caching": true,
    "persistence": true,
    "semanticSearch": false,
    "encryptionEnabled": true
  },
  "defaultTtl": 86400,
  "maxKeySize": 256,
  "maxValueSize": 1048576
}
```

---

## 7. Integration Checklist

### Week 1: Foundation
- [ ] Remove demo Nova Memory agents (agent_001-003)
- [ ] Start Nova Memory on port 8001 with Redis
- [ ] Create `~/.openclaw/workspace/skills/nova-memory/` directory
- [ ] Create SKILL.md and config files
- [ ] Test API endpoints manually

### Week 2: Agent Onboarding
- [ ] Update agent TOOLS.md to document Nova Memory
- [ ] Create example prompts for using Nova Memory
- [ ] Test with one agent (main) first
- [ ] Document key naming conventions

### Week 3: Cross-Agent Testing
- [ ] Test memory sharing between main + sasha
- [ ] Test memory sharing between sasha + wathuge
- [ ] Create integration tests
- [ ] Document any edge cases

### Week 4: Production Ready
- [ ] Set up monitoring/logging
- [ ] Document troubleshooting steps
- [ ] Create backup/recovery procedures
- [ ] Performance test at scale

---

## 8. Implementation Files Needed

### Create These Files:
1. `C:\Users\DAVID\.openclaw\workspace\skills\nova-memory\SKILL.md`
2. `C:\Users\DAVID\.openclaw\workspace\skills\nova-memory\nova-client.js`
3. `C:\Users\DAVID\.openclaw\workspace\skills\nova-memory\nova-memory.config.json`
4. `C:\Users\DAVID\.openclaw\workspace\skills\nova-memory\README.md`
5. `C:\Users\DAVID\.openclaw\workspace\tools\nova-memory-tool.ts`

### Modify These Files:
1. `C:\Users\DAVID\.openclaw\workspace\TOOLS.md` - Add Nova Memory documentation
2. Agent-specific `TOOLS.md` in each workspace

---

## 9. How Users Will Use It (From Agent Perspective)

### Example 1: Agent Storing User Preferences
```
Agent (main): The user prefers verbose responses and wants English.

[Stores in Nova Memory]
Key: agent:main:user:user_456:preferences
Value: { "verbose": true, "language": "en" }

[Next conversation with same user]
Key: agent:main:user:user_456:preferences
Retrieved: { "verbose": true, "language": "en" }
```

### Example 2: Cross-Agent Memory Sharing
```
Agent (sasha): Need to know what main learned about user
→ Query Nova Memory for agent:main:user:user_456:*
→ Gets all stored information about this user
→ Uses it to provide consistent context
```

### Example 3: On-Demand Search
```
Agent (wathuge): What topics have users asked about?
→ Search Nova Memory for "topic:*"
→ Gets semantic results across all conversation history
→ Identifies trending topics
```

---

## 10. Success Criteria

- [ ] All 3 OpenClaw agents can store memory to Nova Memory
- [ ] All 3 agents can retrieve each other's memories (with permissions)
- [ ] Memory persists across agent restarts
- [ ] Agents can search memories semantically
- [ ] Performance is <100ms for store/retrieve operations
- [ ] Documentation is clear for new users
- [ ] No OpenClaw source code was modified
- [ ] Works with existing OpenClaw workflows

---

## Next Steps

1. Shut down demo agents
2. Create `~/.openclaw/workspace/skills/nova-memory/` directory structure
3. Create SKILL.md and configuration files
4. Test Nova Memory API connectivity
5. Update agent TOOLS.md documentation
6. Run first integration test with main agent

---

**Created:** March 11, 2026
**Status:** Ready for Implementation
**Scope:** Non-invasive OpenClaw integration
