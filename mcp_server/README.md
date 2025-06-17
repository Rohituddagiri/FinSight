### Create a new directory for our project
`uv init sec_edgar_server`

`cd sec_edgar_server`

---

### Create virtual environment and activate it
`uv venv --python 3.11`

`source .venv/bin/activate`

---

### Install dependencies
`uv pip install -r requirements.txt`

---

### Create our server file
`touch main.py`

---

### Inspect the mcp server by running the below command

`npx @modelcontextprotocol/inspector uv run main.py`