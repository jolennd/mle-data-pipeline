# ADR 16: The output folder is added to config.py
Status: accepted
Context: Step 10 of phase 2 exports the mart to a folder. config.py is shared, so a change needs an ADR and approval.
Decision: config.py gets one getter, processed_dir(), which reads PROCESSED_DIR through require_env with no default in code. .env.example lists data/processed.
Consequences: The export path comes from the environment (M4). A missing variable raises at the first use. No existing function changes.
