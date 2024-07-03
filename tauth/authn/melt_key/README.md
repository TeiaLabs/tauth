# MELT API Key

## Migration

1. Query all `melt-key` client names
    - For each key, get `client_name` and retrieve the root organization
    - e.g., `/teialabs/athena` -> `/teialabs`; `/osf/allai/chat` -> `/osf`
2. Create organization entities based on client names from step 1
3. Add `melt-key` authprovider for each organization entity
4. Migrate `tokens` collection to `melt_keys` collection
