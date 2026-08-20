# Trace screenshot

After a real multi-agent run:

```powershell
python -m multi_agent_research_lab.cli multi-agent --query "When is multi-agent research justified?"
```

Open the newest file under `reports/traces/*.html` in a browser and capture a screenshot that clearly shows:

- query
- `researcher → analyst → writer → critic → done` route history
- event cards
- token count

Submit that screenshot or the trace HTML/link according to the course instructions.
