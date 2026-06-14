# starter: fork this and ship your first Claude app

The repo root teaches the moves in five short acts. This `starter/` app is the
minimal, deployable skeleton you fork to build your own product on top of Claude.

It is one small FastAPI service:

- `app.py` is a `/api/chat` endpoint that calls Claude and returns the reply with token usage, a `/health` check, and a `/` route that serves the chat page.
- `static/index.html` is a one-file chat UI with no build step.
- `Dockerfile` builds a container image you can deploy anywhere.

No performance claims live here. The starter is a skeleton. The cost and eval
numbers in the root README are things you measure once your own workload is real.

## Run it locally

```bash
pip install -r starter/requirements.txt
export ANTHROPIC_API_KEY=...        # from console.anthropic.com
uvicorn starter.app:app --reload    # serves http://localhost:8000
```

Open the page and ask Claude something. Without a key the page still loads and
`/api/chat` returns a clear 503 telling you to set the key.

Pick the model with an env var (it defaults to Haiku for fast, cheap replies):

```bash
export CLAUDE_MODEL=claude-sonnet-4-6
```

## Run it in a container

```bash
docker build -f starter/Dockerfile -t claude-starter starter/
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY claude-starter
```

## Deploy it

Any host that runs a container runs this app. Two one-command paths:

- Fly.io: run `fly launch` from `starter/`, then `fly secrets set ANTHROPIC_API_KEY=...` and `fly deploy`.
- Render: new Web Service from your fork, Docker runtime, root directory `starter`, with `ANTHROPIC_API_KEY` added as an environment secret.

## Make it yours

- Edit `SYSTEM` in `app.py` (or set the `CLAUDE_SYSTEM` env var) to your product's voice.
- Give Claude tools the way `02_agent_with_tools.py` does in the repo root.
- Add an eval gate before you ship, the way `eval_lint.py` does. Demos win the trial. Evals win the renewal.
