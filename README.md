# OpenAyane RDE

OpenAyane RDE is a research and implementation repository for OpenAyane, a relational control mechanism built around the RDE (Resonant Deviation Evaluator) evaluation layer.

RDE evaluates semantic change (ΔM) produced by generative or agentic systems. OpenAyane integrates RDE with task contracts, structural diff, semantic delta estimation, policy bridging, safe execution, audit logs, relation-store updates, and historical feedback loops.

## Repository layout

```text
paper/
  openayane_implementation_plan_final_ja.tex
  openayane_implementation_plan_final_ja.pdf
  figures/
    openayane_implementation_flow.svg
    openayane_implementation_flow.png
Makefile
```

## Build

```bash
make figures
make paper
```

`make figures` converts SVG figures into PNG assets. `make paper` builds the Japanese LaTeX paper with XeLaTeX.

## Licensing

Paper and documentation are licensed under CC BY 4.0 unless otherwise noted. Code and build scripts are licensed under the MIT License.
