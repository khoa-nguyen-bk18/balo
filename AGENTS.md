# Project Guidelines

## Codebase Exploration & Intelligence (CodeGraph)

This repository is indexed with [CodeGraph](https://github.com/colbymchenry/codegraph) (`.codegraph/` exists at the repo root).

### Mandatory Navigation Rule:
**ALWAYS reach for CodeGraph FIRST instead of using `grep`, `ripgrep`, `find`, or sequential file-reading loops when exploring, searching, or understanding code.**

CodeGraph maintains a semantic graph of symbols, call hierarchies, and references across languages (Kotlin, Python, XML, etc.). It delivers verbatim, line-numbered source code together with caller/callee graphs and blast-radius summaries in a single round-trip.

### How to Explore:
1. **MCP Tool (Preferred)**:
   - Call `codegraph_explore` with a query or symbol name (e.g., `codegraph_explore(query="BackupEngine")`).
2. **CLI Fallback (Terminal)**:
   - `codegraph explore "<symbol or question>"`: Verbatim source + call paths in one shot.
   - `codegraph query "<search>"`: Fast symbol lookup.
   - `codegraph node "<symbol or file>"`: Detailed symbol source + caller/callee trail, or file with line numbers & dependents.
   - `codegraph callers "<symbol>"`: Trace all callers of a method/function.
   - `codegraph callees "<symbol>"`: Trace all functions/methods called by a symbol.
   - `codegraph impact "<symbol>"`: Analyze blast radius and code affected by modifying a symbol.
   - `codegraph context "<task>"`: Gather all relevant symbols and relationships for a specific task.
   - `codegraph sync`: Update the index if significant code changes have been made.

Do **NOT** use `grep` or manual file browsing unless CodeGraph is unavailable or the content is unindexed (e.g. raw logs, binary files).