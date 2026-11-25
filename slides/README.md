# Capstone slides

A short Slidev deck for the kick-off of the capstone day: the dark factory idea, what each team builds from Thursday afternoon to Friday and how the final challenge works.

| Slide | Content | Clicks |
| --- | --- | --- |
| 1 | Cover | 0 |
| 2 | The line of agents from issue to data product, the rework loop, then contracts, baselines and the benchmark | 3 |
| 3 | Thursday afternoon to Friday 14:00: an Agno agent, skills, MCP, a benchmark, improving the factory, then the final | 5 |
| 4 | The final challenge, then how the product is scored | 4 |

Speaker notes are in the HTML comments under each slide; every `[click]` in the notes is one click on the slide. The content follows [docs/capstone-day.md](../docs/capstone-day.md); update the slides when the day plan changes.

## Preview and export

```sh
cd slides
npm install
npm run dev     # hot reload, press "p" for presenter mode
npm run pdf     # export capstone.pdf
```

## Theme

The deck uses the Dataminded academy theme shared by the other AI Engineering Bootcamp decks, copied unchanged from [agentic-ai-in-production](https://github.com/datamindedacademy/agentic-ai-in-production) at commit `00df418`. Diagrams are inline SVG with the `.dg` classes from `theme/styles/dm-components.css`; icons come from the Phosphor set (`i-ph-*`).
