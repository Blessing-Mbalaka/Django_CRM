# Marketing & Advertising

Open `index.html` directly in a modern browser, or use VS Code Live Server from the parent folder. No installation or build is needed.

## Scope

This is a front-end sample workspace for a local South African retailer. Changes remain in memory and reset on refresh. There are no APIs, database, authentication, payments or external integrations. Email sending, sharing, downloads and CRM transfers are labelled demo interactions. Scheduling adds items only to this page's calendar; it does not arrange a future send.

Image uploads are read locally for preview, accept PNG/JPG/WebP/GIF, and are limited to 5 MB. Images and brand details are not uploaded or saved outside the current page.

## Editing

- `index.html`: sidebar, header, modal and module entry point.
- `../inventory/css/style.css`: shared platform design, imported without changing Inventory.
- `css/style.css`: Marketing layouts, calendar, poster templates and preview styles.
- `js/data.js`: realistic sample campaigns, adverts, leads, opportunities, brand and report results.
- `js/components.js`: buttons, tables, charts, formatting, escaping and brand previews.
- `js/views.js`: the nine main pages and Advertising Opportunities.
- `js/forms.js`: field schemas and email template copy.
- `js/app.js`: navigation, in-memory edits, image validation and demo actions.

Keep CSS declarations on separate lines. JavaScript templates contain literal HTML: do not run a formatter that changes text inside template strings.

## Sample reporting

The report snapshot contains R4,850 spend, 4,250 people reached, 320 enquiries, 70 leads, 16 customers and R36,500 sales. Channel rows add up to these totals. The dashboard starts with 4 active campaigns, 3 live adverts, 38 new leads and 16 converted customers.

The advertising page reports only the sample adverts listed there; the wider report includes other channels. Analytics is a labelled historical sample snapshot. Period switches show illustrative totals, not live reporting. New adverts start with zero results; recording a budget does not generate customers. Lead status changes update the operational lead cards and dashboard, not the historical report snapshot.

Cost per lead in advert details uses enquiries as the lead count. Return on advertising spend is sales divided by spending. Zero denominators display helpful text rather than invalid numbers.

## Brand Kit

Saved Brand Kit changes are reused immediately in poster and email previews. Document examples show how the brand could appear on invoices, quotations and a business profile; existing modules and documents remain untouched.

## Checks

Validate navigation, search/status/date filters, all forms, start/end date ordering, future scheduling, templates, image size/type checks, lead status changes and both sidebar widths after editing. Tables and calendars scroll horizontally on narrow screens. The charts are SVG and do not require a chart library.
