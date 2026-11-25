# Capstone slides

A short Slidev deck for the kick-off of the capstone day: the dark factory idea, what each team builds from Thursday afternoon to Friday and how the final challenge works.

| Slide | Content | Clicks |
| --- | --- | --- |
| 1 | Cover | 0 |
| 2 | Who am I, in the layout of Jonny’s intro slide: career lines, photo, timeline | 0 |
| 3 | What a dark factory is: a lit factory floor goes dark, the robots keep working | 2 |
| 4 | The line of agents from issue to data product, then the rework loop | 2 |
| 5 | Thursday afternoon: one agent through benchmark, traces, context, repeat. Friday: as many other agents as the team wants, then the final | 4 |
| 6 | The final as a race: a sealed request, every factory in the same pipeline, hidden grading, the podium, then the 100 points | 4 |

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
