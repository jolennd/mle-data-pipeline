# ADR 12: Download settings are added to config.py
Status: accepted
Context: The download step needs a base URL, a file name pattern, the months and a staging folder. config.py is shared by every step, so a change to it is recorded in an ADR.
Decision: config.py gets four getters (source_base_url, source_file_pattern, partitions, staging_dir). Each reads one environment variable through require_env and has no default in code. .env.example lists the values.
Consequences: Links are built from config (R3). A missing variable raises at the first use. No threshold or existing function changes.
