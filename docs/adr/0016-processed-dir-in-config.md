# ADR 16: The output folder is added to config.py
Status: accepted
Context: The export step writes the mart to a folder. config.py is shared by every step, so a change to it is recorded in an ADR.
Decision: config.py gets one getter, processed_dir(), which reads PROCESSED_DIR through require_env with no default in code. .env.example lists data/processed.
Consequences: The export path comes only from an environment variable, never from code. A missing variable raises at the first use. No existing function changes.
