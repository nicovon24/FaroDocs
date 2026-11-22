# Local source conversations

Status: local single-owner preview. Groq live requests are not verified without a user-provided key. The fake-provider checks use synthetic passages and do not measure answer quality.

## Use

Start Compose and open the Conversations view. Enter your own Groq API key, choose `openai/gpt-oss-20b` (default) or `openai/gpt-oss-120b`, then ask a question whose words occur in ready current document passages. The key remains only in React memory while the page is open; it is sent with each question through the same-origin proxy to FastAPI, which calls Groq's fixed HTTPS chat-completions endpoint. It is never saved in PostgreSQL, returned by an API, or placed in browser storage. Reloading requires re-entry. Do not use a private document in this unfinished local preview.

The application sends at most six retrieved passages (up to 1200 characters each) and the recent turns to Groq. This transfers those passages to an external provider. The server accepts only numbered citations to those six passages. An answer without valid numbered citations is replaced by an abstention. This checks IDs, not whether a claim is truly supported. If lexical search finds no passage, the app abstains without calling Groq. The current search can miss synonyms or paraphrases, and no answer-quality evaluation has been run.

## API

`GET /conversations` lists local history. `POST /conversations` creates an empty thread. `GET /conversations/{id}` returns messages and source metadata. `DELETE /conversations/{id}` removes a thread. `POST /conversations/{id}/messages` accepts JSON:

```json
{
  "question": "When is the review date?",
  "api_key": "<your Groq key; do not save this example with a real value>",
  "model": "openai/gpt-oss-20b",
  "language": "en"
}
```

The model is allowlisted; the provider URL cannot be supplied by a client. Questions are capped at 1000 characters, retrieval at six passages, and completion at 1024 tokens with low reasoning effort. The API does not store the key. Do not put a real key into shell history or test fixtures. When a document is deleted, conversations citing its passages disappear immediately; the cleanup worker then removes the passages and original file.

The browser can reopen history, display citation text and source links, and delete a thread. PDF export, account-bound history, encrypted key persistence, shared permissions, and streaming remain separate stages. This local API binds to localhost and does not establish user isolation.

Provider references: [Groq chat completion API](https://console.groq.com/docs/api-reference), [supported models](https://console.groq.com/docs/models).
