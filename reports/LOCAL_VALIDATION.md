# Local Validation

- pytest: **6 passed**
- Python compileall: **PASS**
- single-agent offline smoke: **PASS**
- multi-agent offline smoke: **PASS**
- 6-query offline benchmark: **PASS**
- trace JSON + HTML generation: **PASS**
- core `TODO(student)` markers under `src/` and `tests/`: **0**

The benchmark currently records `LLM_PROVIDER=offline`, therefore it is a deterministic
engineering validation and **not** the final provider benchmark. Before submission, fill
`.env` with Groq or OpenAI and run:

```powershell
python scripts/run_submission.py
```

That gate refuses offline mode and regenerates benchmark metrics using the real provider.
