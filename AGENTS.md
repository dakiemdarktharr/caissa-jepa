# Project collaboration preferences

- Commit completed project changes after appropriate verification.
- When the user requests "lên github", commit pending project changes and push to the configured GitHub remote. This is standing authorization for that workflow; respect explicit negations, quoted text, and narrower instructions in the request.
- Verify the destination and push result. Do not force-push or overwrite remote history without explicit authorization.
- Preserve the existing exclusions for generated datasets, caches, checkpoints, environments, and logs. Report what was excluded when publishing the project; obtain a storage plan before uploading large generated artifacts separately.
- Keep application UI text in English.
- Do not create agents/subagents on your own unless the user has approved the exact model and reasoning effort first. Workers the user creates and configures are exempt. For every agent you create, preserve that approved model/effort; do not silently fall back.
