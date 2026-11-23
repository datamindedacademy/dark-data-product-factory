# Stakeholder interviews

Hand-out for the capstone day. You spent last week interviewing people at Fernhill Outfitters.
These are your notes. None of this is written down anywhere in the warehouse: the data shows *what*
happened, not how Fernhill counts it. Your agents do not see this file. If you want your factory to
know it, you have to put it there yourself (a skill, a CLAUDE.md, a semantic model, a tool).

Everything below holds for every data product, not only for one.

## Sofie Maes, finance controller

> "Revenue is recognised when we ship. An order that is *placed* has not been paid or picked yet,
> so it is not revenue, and a cancelled order never is. Shipped and delivered, that's it."

> "Everything we report is in euro. The UK pays in pounds; we convert at the rate of the order day,
> refunds too. A refund belongs to the order it refunds, not to the day the parcel came back."

> "Revenue is after discounts and without shipping fees. Shipping is a cost recovery, not sales."

> "Refunds for damaged goods are not lost money: we claim those back from the carrier. Every other
> refund - wrong size, changed mind, not as described - is real lost revenue."

## Lotte Janssens, CRM manager

> "The app team tests checkout in production with accounts on `fernhill.test`. They are not
> customers. Leave them out of anything that counts customers or revenue."

> "When I say customer value or anything 'per customer', I mean the last full calendar year. Two-year
> totals punish everyone who joined recently."

> "The first-purchase channel is where someone *really* became a customer: their first order that
> we actually shipped, over their whole history."

> "Legal is strict: we may only contact customers who opted in to marketing. A list of people to
> invite that includes anyone without opt-in is a GDPR incident, not a list."

> "We never merge accounts. One account is one customer, even if two accounts look alike."

## Marc Dubois, retail operations director

> "London opened in June 2024. When we compare stores, a fair comparison starts in July 2024."

> "Store orders are store revenue, wherever the customer lives."

## Pieter De Wolf, performance marketing lead

> "Marketing spend is booked in euro already, no conversion needed."

> "BF25 is our Black Friday code. Those orders are normal revenue, we don't strip them out."

## Ana Costa, data platform

> "Raw orders are append-only. When ingestion replays a load you get the same order twice; the
> latest load wins. Staging already handles that, so build on staging or core, never on raw."

> "Product categories are typed in by hand. `stg_products` cleans them up; use that."
