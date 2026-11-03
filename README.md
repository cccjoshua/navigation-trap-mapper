# Navigation Trap Mapper

A `nanoagent.plugin/v0001` plugin. An agent explores a simulated website one page at a time and
reports every trap page: a page it can reach from the start from which the target can never be
reached. A deterministic verifier compares the answer with reachability computed on the hidden graph.

Each site is built from an integer seed alone (SHA-256 of the seed and a counter): 15 to 26 pages,
2 to 4 trap clusters (a two-page loop, a three-page ring, a page with no links, a funnel page that
leads only into a loop of its own) and a few pages nothing links to. Every reachable page is at most 6
links from the start, so an agent can explore the site in a handful of calls. No network is used.

## Tools

| Tool | Does | Code |
|---|---|---|
| `start_site` | Gives the start page and the target page | `src/plugin/tools.py` |
| `list_links` | Shows up to 40 pages at once, each with its title and links and the page each link leads to | `src/plugin/tools.py` |
| `map_graph` | The whole graph and its trap pages: the task's reference, never shown to the agent | `src/plugin/tools.py` |

The site itself is built in `src/plugin/site.py`.

### Tasks

| Task | Does | Runner |
|---|---|---|
| `find-trap-pages` | Report every page reachable from the start that cannot reach the target | `agent`, with `start_site` and `list_links`; reference `map_graph` |

The verifier (`verifier/find.py`) searches forward from the start and backward from the target on the
reference graph; the trap pages are those reached forward and not backward. The answer is valid only
when it is exactly that set, with no unknown or repeated page. Its score is the Jaccard similarity.

## Layout

```text
.
├── nanoagent.yaml   # manifest: id, runtime, permissions, tools, tasks
├── contract.py      # each tool's and task's typed input and output
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── .gitignore
├── .env             # environment variable NAMEs this plugin needs (none)
├── src/plugin/      # the MCP server, the site generator and the tools
├── tests/           # tests of the site, the tools and the verifier
├── ui/              # outputs are drawn from their JSON Schema
├── product/         # the product page: product.yaml and icon.svg
└── verifier/        # deterministic verifier package
```

## Develop and run

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
```

Publishing checks every plugin rule: push the plugin to a public GitHub repository and submit its
URL on RUSH Lab.
