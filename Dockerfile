FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir -e ".[llm]"
COPY . .
CMD ["python", "-m", "multi_agent_research_lab.cli", "--help"]
