# Stakeholder interviews

Hand-out for the capstone day. You spent last week interviewing people at Fernhill Outfitters.
These are your notes. None of this is written down anywhere in the data: the data shows *what*
happened, not how Fernhill counts it. Your agents do not see this file. If you want your factory to
know it, you have to put it there yourself (instructions, a skill, a semantic model, a tool).

Everything below holds for every request, not only for one.

## Who is who

When two people define a term differently, the owner of the term decides.

```mermaid
flowchart TD
    ceo["<b>Hilde Claes</b><br/>CEO"]
    ceo --> fin["<b>Finance</b>"]
    ceo --> retail["<b>Retail operations</b><br/>Marc Dubois, director"]
    ceo --> mkt["<b>Marketing</b>"]
    ceo --> tech["<b>Technology</b>"]
    ceo --> merch["<b>Merchandising</b><br/>Sofie Claes, head"]
    ceo --> cx["<b>Customer experience</b><br/>Elise Martin"]

    fin --> sofie["Sofie Maes<br/>finance controller"]
    retail --> stores["Six store managers<br/>Brussels, Antwerp, Ghent,<br/>Amsterdam, Lille, London"]
    mkt --> lotte["Lotte Janssens<br/>CRM manager"]
    mkt --> pieter["Pieter De Wolf<br/>performance marketing lead"]
    tech --> ana["Ana Costa<br/>data platform"]
    tech --> app["Web shop and app team"]
    tech --> ae["Analytics engineering<br/><i>you: the answers</i>"]

    sofie -.-|owns| t1(["revenue, refunds, currencies"])
    lotte -.-|owns| t2(["customers, consent"])
    retail -.-|owns| t3(["stores, store comparisons"])
    pieter -.-|owns| t4(["marketing spend, campaigns"])
    ana -.-|owns| t5(["raw and staging data"])
```

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

> "Orders land append-only. When ingestion replays a load you get the same order twice, with a later
> `_loaded_at`; the latest load wins."

> "Product categories are typed in by hand in the back office. You'll find every spelling."

> "The export has tables nobody switched off when we migrated. If a table looks too convenient, ask
> yourself who still fills it."
