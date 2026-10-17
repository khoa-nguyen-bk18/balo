## Codebase Exploration & Intelligence (CodeGraph)

This repository is indexed with CodeGraph (`.codegraph/` exists at the repo root).

**ALWAYS reach for CodeGraph FIRST instead of using `grep`, `ripgrep`, `find`, or sequential file-reading loops.**

- **MCP Tool**: `codegraph_explore` provides verbatim, line-numbered source code plus caller/callee graphs and blast-radius summaries in one call.
- **CLI Commands**:
  - `codegraph explore "<symbol or query>"`: Source + call paths in one shot.
  - `codegraph query "<search>"`: Fast symbol lookup.
  - `codegraph node "<symbol or file>"`: Detailed symbol source + caller/callee trail.
  - `codegraph callers "<symbol>"` / `codegraph callees "<symbol>"`: Trace call graphs.
  - `codegraph impact "<symbol>"`: Blast radius analysis.
  - `codegraph context "<task>"`: Context for tasks.
  - `codegraph sync`: Sync index with recent changes.

Do not use `grep` or manual file browsing unless CodeGraph is unavailable or querying non-indexed assets.

## Project Management
This project uses Markplane for project management. Key files:
- `.markplane/INDEX.md` - Navigation entry point
- `.markplane/.context/summary.md` - Current project state
- `.markplane/backlog/INDEX.md` - All work items
- `.markplane/plans/INDEX.md` - Implementation plans
When working on a task, read the relevant task item and its linked plan first.
