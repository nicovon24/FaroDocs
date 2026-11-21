# FaroDocs system designs

These original diagrams show the **proposed** system. No application code or end-to-end behavior is implemented yet. They describe the selected Next.js + FastAPI + Python worker architecture and should be updated when implementation or measurements change.

| Diagram | Question it answers |
| --- | --- |
| [Topology](topology.svg) | Which runtime owns UI, authorization, jobs, data, and model calls? |
| [Ingestion](ingestion.svg) | How does an uploaded file become located, versioned passages and embeddings? |
| [Answer path](answer-path.svg) | How does an authorized question lead to cited evidence or abstention? |
| [Access and deletion](access-and-deletion.svg) | Where are document access enforced and derived data removed? |

The diagrams deliberately omit table columns, endpoint names, provider/model choices, and operational limits. Those decisions belong in the [product plan](../docs/product-plan.md), the [identity and provider credential design](../docs/identity-and-provider-keys.md), and stage-specific OpenSpec artifacts. A citation ID check is planned for the chat stage; semantic claim-to-source support verification is a later differentiator. External generation receives only bounded, authorized passages if enabled.

The source of every SVG is the editable node and edge data in [`build.py`](build.py). It generates temporary HTML and exports the SVG files using the installed `diagram-design` SVG exporter (or a path passed with `--exporter`). It does not require application services:

```powershell
py -3 system-design/build.py
```

The project-specific palette is in [STYLE.md](STYLE.md). Open the SVGs directly in a browser or editor; each includes a title and description for accessibility.
