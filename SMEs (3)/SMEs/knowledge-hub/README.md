# Business Knowledge Hub

Open `index.html` in a modern browser or use VS Code Live Server from the parent folder. No installation or build is required.

## Scope

A front-end sample resource centre with courses, guides, video previews, resource layouts, funding education, compliance introductions, glossary, bookmarks and learning progress. Edits reset on refresh. There is no backend, authentication, storage, streaming, AI, real download or certificate generation.

The separate SME Academy links to this resource centre from its Business Tools page.

## Files

- `index.html`: the shared platform shell.
- `../inventory/css/style.css`: existing design system, loaded unchanged.
- `css/style.css`: learning layouts shared with Academy.
- `js/data.js`: content, quiz questions, source links and session state.
- `js/components.js`: cards, search helpers and shared controls.
- `js/views.js`: pages, guide reader and course player.
- `js/app.js`: navigation, search, bookmarks, quiz and completion interactions.

Guide content has an overview, rationale, steps, example, checklist and takeaway. Courses use five sample lesson stages. Templates show the proposed document fields; no real document is downloaded. Videos show a static preview and learning summary.

## Learning state

Summary cards are calculated from the current state. Started-course progress is averaged for the dashboard. Completion is idempotent. The five-question quiz records first-attempt scores; retrying an answer gives feedback without inflating that score. Completing all lessons unlocks a sample certificate, not an accredited qualification. Checklists are educational and do not establish compliance or funding eligibility.

## Official educational references

Compliance introductions link to these official sources. No tax rates, eligibility thresholds or filing deadlines are embedded in the sample lessons.

- [CIPC FAQs](https://www.cipc.co.za/?page_id=4160)
- [SARS small business information](https://www.sars.gov.za/businesses-and-employers/small-businesses-taxpayers/)
- [SARS small businesses and VAT](https://www.sars.gov.za/businesses-and-employers/small-businesses-taxpayers/small-businesses-and-vat/)
- [Information Regulator POPIA resources](https://inforegulator.org.za/popia/)
- [Department of Employment and Labour: Compensation Fund](https://www.labour.gov.za/DocumentCenter/Pages/COID_How_To_Register_with_the_Compensation_Fund.aspx)

The material is educational, not legal, tax or financial advice. Check the relevant authority for current requirements.

## Validation

Syntax and generated HTML checks covered the pages, guides and lesson views. Interaction checks covered search, bookmarks, quiz scoring, completion gates and sample certificate availability. Visual browser testing was not performed.
