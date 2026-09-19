FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Safe default: paper trading. Override with -e POLYBOT_DRY_RUN=false to go live.
ENV POLYBOT_DRY_RUN=true \
    PYTHONUNBUFFERED=1

CMD ["python", "-m", "polybot.cli", "run"]
