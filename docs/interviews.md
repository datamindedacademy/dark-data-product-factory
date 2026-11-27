# Stakeholder interviews

Last week you interviewed five people at Fernhill Outfitters. The recording of those interviews is
handed out at the kick-off: a five-minute video. The slides in it show the headlines below; what
people say in between is where the detail is. None of it is written down anywhere in the data: the
data shows *what* happened, not how Fernhill counts it.

Your agents don't watch videos. If you want your factory to know what was said, you have to put it
there yourself (instructions, a skill, a semantic model, a tool). Everything holds for every request,
not only for one.

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

## The headlines

| Who | On the slide |
|---|---|
| Sofie Maes, finance controller | Revenue is what has left the building · Everything we report is in euro · Revenue is mine to define |
| Lotte Janssens, CRM manager | Our testers are not customers · A customer starts with a real first order · One account is one customer |
| Marc Dubois, retail operations director | My managers trust the till report · Compare the stores fairly |
| Pieter De Wolf, performance marketing lead | Does social pay off? · Spend is in euro already |
| Ana Costa, data platform | Orders land append-only · Not every table is still filled |
