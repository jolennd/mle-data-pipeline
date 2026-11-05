# ADR 12: Download settings are added to config.py
Status: accepted
Context: Step 1 of phase 2 needs a base URL, a file name pattern, the months and a staging folder. config.py is shared, so a change needs an ADR and approval.
Decision: config.py gets four getters (source_base_url, source_file_pattern, partitions, staging_dir). Each reads one environment variable through require_env and has no default in code. .env.example lists the values.
Consequences: Links are built from config (R3). A missing variable raises at the first use. No threshold or existing function changes.
