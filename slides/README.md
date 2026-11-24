# Capstone slides

A short Slidev deck for the kick-off of the capstone day. It explains the dark factory idea, what each team builds during the day and how the final challenge works.

| Slide | Content |
| --- | --- |
| 1 | Cover |
| 2 | The dark factory: the line of agents, contracts, baseline agents and the benchmark |
| 3 | The team's day: an Agno agent, skills, MCP, a benchmark, improving the factory |
| 4 | The final challenge and how the product is scored |

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

## Theme

`theme/` holds the shared Dataminded Slidev theme, copied unchanged from [playground-agentic-slides](https://github.com/datamindedbe/playground-agentic-slides) at commit `16b64517127a0d34a4d6367bc5f93e16d3492184`. It provides the layouts (`cover`, `default`, `cards`, `statement`, ...) and the `Dm*` components used in `slides.md`.
