# Capstone slides

A short Slidev deck for the kick-off of the capstone day. It explains the dark factory idea, what each team builds during the day and how the final challenge works.

| Slide | Content | Clicks |
| --- | --- | --- |
| 1 | Cover | 0 |
| 2 | The dark factory as an animated line of agents, then contracts, baseline agents and the benchmark | 3 |
| 3 | The team's day: an Agno agent, skills, MCP, a benchmark, improving the factory, with a bar that fills up towards the final | 5 |
| 4 | The final challenge, then how the product is scored | 4 |

Speaker notes are in the HTML comments under each slide. The content follows [docs/capstone-day.md](../docs/capstone-day.md); update the slides when the day plan changes.

## Preview and export

Use Node.js 20.12 or later.

```sh
cd slides
npm install
npm run dev
```

Open http://localhost:3030. Use the arrow keys to navigate, `o` for the overview and `p` for presenter mode.

```sh
npm run build                                   # static site in dist/
npm run export -- --output capstone-export.pdf  # PDF, needs Playwright Chromium
```

## Files

| Path | Content |
| --- | --- |
| `slides.md` | The slides, their styles and speaker notes |
| `components/FactoryLine.vue` | The animated factory line on slide 2: a request travels from the issue to the data product, each station lights up as it passes, and the dashed arc is the rework loop |
| `components/ScoreClock.vue` | The 45-minute clock on slide 4 |
| `layouts/dark.vue` | Dark content slide on one of the theme's brand backgrounds, used for slides 2 and 4 |

Icons come from the Material Design Icons set that ships with Slidev (classes like `i-mdi-github`). Browse them on [icones.js.org](https://icones.js.org/collection/mdi).

## Theme

`theme/` holds the shared Dataminded Slidev theme, copied unchanged from [playground-agentic-slides](https://github.com/datamindedbe/playground-agentic-slides) at commit `16b64517127a0d34a4d6367bc5f93e16d3492184`. It provides the layouts (`cover`, `default`, `cards`, `statement`, ...) and the `Dm*` components used in `slides.md`.
