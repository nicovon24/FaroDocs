# Local passage search

Search uses PostgreSQL full-text matching with the `simple` dictionary. It covers extracted passages from ready current versions of visible local-owner documents. During a replacement upload, the last ready version remains current and searchable until a newer replacement succeeds; a failed replacement leaves it available. Search returns at most 20 passages ordered by lexical rank, then stable passage ID. No vector embeddings or retrieval-quality results are claimed.

Run the Compose stack, then query:

```powershell
$term = [uri]::EscapeDataString('review date')
Invoke-RestMethod "http://127.0.0.1:8000/search?q=$term"
```

Each result includes `passage_id`, `document_id`, `version_id`, `version_number`, `title`, a bounded `text_content` excerpt with matched words enclosed in `« »`, `locator`, and `rank`. The web Search view opens the original version; PDF page locators add `#page=N`. Empty or whitespace-only queries return HTTP 422. This search matches words, so synonyms, paraphrases, and some inflections can be missed. Search is restricted to the fixed local owner and must not be exposed for shared use before identity and authorization are implemented.
