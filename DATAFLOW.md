# Clarity: Data Flow Architecture

This document explains how data flows through the Clarity pipeline, from raw inputs to the final design analysis document.

---

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLARITY PIPELINE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                 │
│   │    task_     │    │    docs/     │    │    src/      │                 │
│   │  context.md  │    │   *.md       │    │   *.py       │                 │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                 │
│          │                   │                   │                          │
│          ▼                   ▼                   ▼                          │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                 │
│   │    Task      │    │    Docs      │    │    Code      │                 │
│   │   Reader     │    │   Reader     │    │   Reader     │                 │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                 │
│          │                   │                   │                          │
│          │    DETERMINISTIC  │   PARSING         │                          │
│          └───────────────────┼───────────────────┘                          │
│                              │                                              │
│                              ▼                                              │
│                    ┌──────────────────┐                                     │
│                    │    Synthesizer   │                                     │
│                    │    (LLM Call)    │                                     │
│                    └────────┬─────────┘                                     │
│                             │                                               │
│                             │  REASONING (ONE PASS)                         │
│                             │                                               │
│                             ▼                                               │
│                    ┌──────────────────┐                                     │
│                    │  Design Analysis │                                     │
│                    │     Writer       │                                     │
│                    └────────┬─────────┘                                     │
│                             │                                               │
│                             │  DETERMINISTIC FORMATTING                     │
│                             │                                               │
│                             ▼                                               │
│                    ┌──────────────────┐                                     │
│                    │ design_analysis  │                                     │
│                    │      .md         │                                     │
│                    └──────────────────┘                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Stage 1: Reading (Deterministic)

The first stage converts raw files into structured data. **No reasoning happens here**—only parsing.

### 1.1 Task Context Reader

**Purpose:** Extract what the developer wants to do and what they believe about the system.

```
┌─────────────────────────────────────┐
│          task_context.md            │
├─────────────────────────────────────┤
│ ## Task                             │
│ Add user authentication             │
│                                     │
│ ## Owned by                         │
│ backend-team                        │
│                                     │
│ ## What I think I need to do        │
│ - Add login endpoint                │
│ - Create session management         │
│                                     │
│ ## What I'm unsure about            │
│ - OAuth provider choice             │
│                                     │
│ ## Constraints I know               │
│ - Must use PostgreSQL               │
│                                     │
│ ## Things I'm assuming              │
│ - Users have email addresses        │
└─────────────────────────────────────┘
                  │
                  ▼ read_task_context()
                  │
┌─────────────────────────────────────┐
│           Python Dict               │
├─────────────────────────────────────┤
│ {                                   │
│   "task": "Add user authentication",│
│   "owned_by": "backend-team",       │
│   "planned_approach": [             │
│     "Add login endpoint",           │
│     "Create session management"     │
│   ],                                │
│   "unknowns": [                     │
│     "OAuth provider choice"         │
│   ],                                │
│   "constraints": [                  │
│     "Must use PostgreSQL"           │
│   ],                                │
│   "assumptions": [                  │
│     "Users have email addresses"    │
│   ]                                 │
│ }                                   │
└─────────────────────────────────────┘
```

**Key Behavior:**
- Parses markdown headers to extract sections
- Preserves bullet points as lists
- Raises exception if required sections are missing
- **Does NOT interpret or improve content**

---

### 1.2 Documentation Reader

**Purpose:** Extract structured sections from documentation files for citation.

```
┌─────────────────────────────────────┐
│            docs/api.md              │
├─────────────────────────────────────┤
│ # API Reference                     │  ← Line 1
│                                     │
│ This API handles user operations.   │  ← Line 3
│                                     │
│ ## Authentication                   │  ← Line 5
│                                     │
│ All requests require Bearer token.  │  ← Line 7
│                                     │
│ ## Endpoints                        │  ← Line 9
│                                     │
│ POST /users - Create user           │  ← Line 11
└─────────────────────────────────────┘
                  │
                  ▼ read_docs()
                  │
┌─────────────────────────────────────┐
│           Python Dict               │
├─────────────────────────────────────┤
│ {                                   │
│   "documents": [                    │
│     {                               │
│       "path": "/full/path/api.md",  │
│       "sections": [                 │
│         {                           │
│           "heading": "API Reference"│
│           "level": 1,               │
│           "content": "This API...", │
│           "line_start": 1,          │
│           "line_end": 4             │
│         },                          │
│         {                           │
│           "heading": "Authentication│
│           "level": 2,               │
│           "content": "All requests..│
│           "line_start": 5,          │
│           "line_end": 8             │
│         },                          │
│         ...                         │
│       ]                             │
│     }                               │
│   ]                                 │
│ }                                   │
└─────────────────────────────────────┘
```

**Key Behavior:**
- Tracks line numbers for precise citations
- Preserves content verbatim
- Keeps documents separate (no merging)
- **Does NOT summarize**

---

### 1.3 Code Reader

**Purpose:** Extract structural information from Python source files.

```
┌─────────────────────────────────────┐
│          src/auth.py                │
├─────────────────────────────────────┤
│ """Authentication module."""        │  ← Line 1
│                                     │
│ from typing import Optional         │  ← Line 3
│                                     │
│ class AuthService:                  │  ← Line 5
│     """Handles authentication."""   │
│                                     │
│     def login(self, user, pwd):     │  ← Line 8
│         """Authenticate user."""    │
│         ...                         │
│                                     │
│     def logout(self, token):        │  ← Line 15
│         """End session."""          │
│         ...                         │
└─────────────────────────────────────┘
                  │
                  ▼ read_code()
                  │
┌─────────────────────────────────────┐
│           Python Dict               │
├─────────────────────────────────────┤
│ {                                   │
│   "files": [                        │
│     {                               │
│       "path": "/full/path/auth.py", │
│       "imports": [                  │
│         "from typing import Optional│
│       ],                            │
│       "classes": [                  │
│         {                           │
│           "name": "AuthService",    │
│           "signature": "class Auth..│
│           "docstring": "Handles..." │
│           "line_start": 5,          │
│           "line_end": 20,           │
│           "methods": [              │
│             {                       │
│               "name": "login",      │
│               "signature": "def log.│
│               "line_start": 8,      │
│               "line_end": 14        │
│             },                      │
│             ...                     │
│           ]                         │
│         }                           │
│       ],                            │
│       "functions": []               │
│     }                               │
│   ]                                 │
│ }                                   │
└─────────────────────────────────────┘
```

**Key Behavior:**
- Uses Python AST for accurate parsing
- Extracts signatures, docstrings, line ranges
- Tracks imports for dependency understanding
- **Does NOT execute or interpret code**

---

## Stage 2: Synthesis (LLM-Powered)

The synthesizer is the **only component that reasons**. It makes exactly **one LLM call**.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SYNTHESIZER INPUT                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐               │
│  │ Task Context│   │Documentation│   │    Code     │               │
│  │    Dict     │   │    Dict     │   │    Dict     │               │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘               │
│         │                 │                 │                       │
│         └────────────────┬┴─────────────────┘                       │
│                          │                                          │
│                          ▼                                          │
│              ┌───────────────────────┐                              │
│              │   Format as Prompt    │                              │
│              │   (Markdown Text)     │                              │
│              └───────────┬───────────┘                              │
│                          │                                          │
└──────────────────────────┼──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          LLM CALL                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  System Prompt (synthesizer.txt):                                   │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ You are a technical analyst synthesizing information...     │    │
│  │                                                             │    │
│  │ Evidence Hierarchy:                                         │    │
│  │ 1. Documentation (declared intent)                          │    │
│  │ 2. Code (observed reality)                                  │    │
│  │ 3. Task assumptions (may be wrong)                          │    │
│  │                                                             │    │
│  │ Rules:                                                      │    │
│  │ - NEVER invent information                                  │    │
│  │ - ALWAYS cite files and lines                               │    │
│  │ - Do NOT propose solutions                                  │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  + User Content (formatted inputs)                                  │
│                                                                     │
│                          │                                          │
│                          ▼                                          │
│                   ┌─────────────┐                                   │
│                   │   LLM API   │                                   │
│                   └──────┬──────┘                                   │
│                          │                                          │
└──────────────────────────┼──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SYNTHESIZER OUTPUT                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  {                                                                  │
│    "system_intent": {                                               │
│      "summary": "System provides user authentication via OAuth2",   │
│      "key_points": ["OAuth2 support", "Session management"],        │
│      "citations": ["docs/api.md:5-8", "README.md:10-15"]           │
│    },                                                               │
│                                                                     │
│    "observed_reality": {                                            │
│      "summary": "AuthService class handles login/logout",           │
│      "relevant_code": [                                             │
│        {                                                            │
│          "path": "src/auth.py",                                     │
│          "element": "AuthService",                                  │
│          "lines": "5-20",                                           │
│          "relevance": "Main authentication logic"                   │
│        }                                                            │
│      ],                                                             │
│      "patterns_found": ["Service pattern", "Token-based auth"]      │
│    },                                                               │
│                                                                     │
│    "feature_fit": {                                                 │
│      "alignments": [...],                                           │
│      "conflicts": [...]                                             │
│    },                                                               │
│                                                                     │
│    "assumptions_and_risks": [...],                                  │
│    "open_decisions": [...],                                         │
│    "documentation_gaps": [...],                                     │
│                                                                     │
│    "confidence_assessment": {                                       │
│      "overall": "medium",                                           │
│      "limiting_factors": ["No OAuth config found"],                 │
│      "sufficient_to_proceed": true                                  │
│    }                                                                │
│  }                                                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Key Behavior:**
- Single LLM call (deterministic cost)
- Reasons from evidence only
- Cites specific files and line numbers
- Reports conflicts between docs and code
- Flags risky assumptions
- **Does NOT propose solutions or architecture**

---

## Stage 3: Writing (Deterministic)

The writer converts the synthesis output to markdown. **No reasoning happens here**—only formatting.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         WRITER INPUT                                │
│                    (Synthesis Output Dict)                          │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼ write_design_analysis()
                             │
┌─────────────────────────────────────────────────────────────────────┐
│                      design_analysis.md                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  # Design Analysis                                                  │
│                                                                     │
│  **Confidence:** medium | **Status:** Ready to proceed              │
│                                                                     │
│  **Limiting Factors:**                                              │
│  - No OAuth config found                                            │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  ## 1. System Intent                                                │
│                                                                     │
│  System provides user authentication via OAuth2                     │
│                                                                     │
│  **Key Points:**                                                    │
│  - OAuth2 support                                                   │
│  - Session management                                               │
│                                                                     │
│  **Sources:**                                                       │
│  - `docs/api.md:5-8`                                                │
│  - `README.md:10-15`                                                │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  ## 2. Observed Code Reality                                        │
│                                                                     │
│  AuthService class handles login/logout                             │
│                                                                     │
│  **Relevant Code:**                                                 │
│  - **`src/auth.py`**                                                │
│    - Element: `AuthService`                                         │
│    - Lines: 5-20                                                    │
│    - Relevance: Main authentication logic                           │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  ## 3. Feature Fit Analysis                                         │
│  ## 4. Assumptions & Risks                                          │
│  ## 5. Open Decisions                                               │
│  ## 6. Documentation Gaps                                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Key Behavior:**
- Fixed section order (1-6, always)
- Empty sections explicitly marked
- All content from synthesis preserved
- **Does NOT interpret or add content**

---

## Complete Data Flow Example

```
                    HUMAN CREATES
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
   ┌──────────┐    ┌──────────┐    ┌──────────┐
   │  task_   │    │  docs/   │    │  src/    │
   │context.md│    │  *.md    │    │  *.py    │
   └────┬─────┘    └────┬─────┘    └────┬─────┘
        │               │               │
        │ PARSE         │ PARSE         │ PARSE
        │ (no reasoning)│               │
        ▼               ▼               ▼
   ┌──────────┐    ┌──────────┐    ┌──────────┐
   │  dict:   │    │  dict:   │    │  dict:   │
   │  task,   │    │ sections,│    │ classes, │
   │ unknowns,│    │  lines,  │    │functions,│
   │ assumes  │    │  paths   │    │  lines   │
   └────┬─────┘    └────┬─────┘    └────┬─────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
                        ▼
              ┌───────────────────┐
              │    SYNTHESIZER    │
              │                   │
              │  ┌─────────────┐  │
              │  │  LLM CALL   │  │
              │  │  (1 call)   │  │
              │  └─────────────┘  │
              │                   │
              │  Evidence:        │
              │  Docs > Code >    │
              │  Assumptions      │
              └─────────┬─────────┘
                        │
                        │ REASONING
                        │ (grounded in evidence)
                        ▼
              ┌───────────────────┐
              │   dict:           │
              │   system_intent,  │
              │   observed_reality│
              │   feature_fit,    │
              │   risks,          │
              │   decisions,      │
              │   gaps            │
              └─────────┬─────────┘
                        │
                        │ FORMAT
                        │ (no reasoning)
                        ▼
              ┌───────────────────┐
              │ design_analysis.md│
              │                   │
              │ Sections 1-6      │
              │ with citations    │
              └───────────────────┘
                        │
                        ▼
                  HUMAN REVIEWS
```

---

## Why This Architecture?

### Separation of Concerns

| Stage | Responsibility | Uses LLM? |
|-------|---------------|-----------|
| Reading | Parse files into structured data | No |
| Synthesis | Reason about the data | Yes (1 call) |
| Writing | Format output | No |

**Benefits:**
- Bugs are easy to locate (wrong content = synthesizer, wrong format = writer)
- Readers can be tested without LLM
- Writer can be tested without LLM
- Only synthesis has variable cost

### Evidence Hierarchy

```
┌─────────────────────────────────────┐
│         MOST AUTHORITATIVE          │
├─────────────────────────────────────┤
│                                     │
│  1. DOCUMENTATION                   │
│     "The system SHALL do X"         │
│     → Declared intent               │
│     → Treat as ground truth         │
│                                     │
├─────────────────────────────────────┤
│                                     │
│  2. CODE                            │
│     "The system DOES do Y"          │
│     → Observed reality              │
│     → May differ from docs          │
│                                     │
├─────────────────────────────────────┤
│                                     │
│  3. TASK ASSUMPTIONS                │
│     "I THINK the system does Z"     │
│     → Developer beliefs             │
│     → May be wrong                  │
│                                     │
├─────────────────────────────────────┤
│         LEAST AUTHORITATIVE         │
└─────────────────────────────────────┘
```

When conflicts arise:
- Docs say X, code shows Y → **Report as conflict**
- Task assumes X, docs say Y → **Flag assumption as risky**
- Task assumes X, no evidence → **Mark as unverified assumption**

### Citation Requirements

Every claim must be traceable:

```
BAD:  "The system uses caching"
GOOD: "The system uses caching (see src/cache.py:15-42)"

BAD:  "Authentication is required"
GOOD: "Authentication is required (see docs/api.md:5-8)"
```

This enables:
- Verification by humans
- Debugging incorrect analysis
- Trust in the output

---

## Error Handling Flow

```
┌──────────────────────────────────────────────────────────────┐
│                       ERROR SCENARIOS                        │
└──────────────────────────────────────────────────────────────┘

READER ERRORS (fail fast):
┌─────────────┐
│ File not    │ ──→ FileNotFoundError
│ found       │     "Task context file not found: path"
└─────────────┘

┌─────────────┐
│ Missing     │ ──→ TaskContextParseError
│ section     │     "Missing required sections: Task, Owned by"
└─────────────┘

┌─────────────┐
│ Syntax      │ ──→ CodeReadError
│ error       │     "Syntax error in src/bad.py: ..."
└─────────────┘

SYNTHESIS ERRORS:
┌─────────────┐
│ No LLM      │ ──→ SynthesisError
│ configured  │     "LLM client not configured"
└─────────────┘

┌─────────────┐
│ LLM returns │ ──→ SynthesisError
│ bad JSON    │     "Failed to parse LLM response as JSON"
└─────────────┘

┌─────────────┐
│ Missing     │ ──→ SynthesisError
│ output keys │     "Synthesis output missing required keys: ..."
└─────────────┘

WRITER ERRORS:
┌─────────────┐
│ Cannot      │ ──→ WriteError
│ write file  │     "Failed to write design analysis: ..."
└─────────────┘
```

---

## Summary

| Component | Input | Output | Deterministic? |
|-----------|-------|--------|----------------|
| Task Reader | `task_context.md` | Structured dict | Yes |
| Docs Reader | `docs/*.md` | Structured dict with line numbers | Yes |
| Code Reader | `src/*.py` | Structured dict with AST info | Yes |
| Synthesizer | Three dicts | Mental model dict | No (LLM) |
| Writer | Mental model dict | `design_analysis.md` | Yes |

**The pipeline is designed so that:**
1. Most components are deterministic and testable
2. LLM usage is isolated and bounded (1 call)
3. All outputs are traceable to inputs
4. Errors are caught early and reported clearly
