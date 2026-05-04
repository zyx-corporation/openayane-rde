# OpenAyane RDE paper build helper
#
# Main targets:
#   make figures  - render SVG figures to PNG files for LaTeX
#   make paper    - build the Japanese LaTeX paper with XeLaTeX
#   make clean    - remove generated LaTeX intermediates

PAPER_DIR := paper
FIG_DIR := $(PAPER_DIR)/figures
TEX := $(PAPER_DIR)/openayane_implementation_plan_final_ja.tex
PDF := $(PAPER_DIR)/openayane_implementation_plan_final_ja.pdf
FLOW_SVG := $(FIG_DIR)/openayane_implementation_flow.svg
FLOW_PNG := $(FIG_DIR)/openayane_implementation_flow.png

.PHONY: all figures paper clean distclean

all: figures paper

figures: $(FLOW_PNG)

$(FLOW_PNG): $(FLOW_SVG)
	@mkdir -p $(FIG_DIR)
	@if command -v inkscape >/dev/null 2>&1; then \
		inkscape $< --export-type=png --export-filename=$@ --export-width=2400; \
	elif command -v rsvg-convert >/dev/null 2>&1; then \
		rsvg-convert -w 2400 -o $@ $<; \
	else \
		python3 - <<'PY'\
import cairosvg\
cairosvg.svg2png(url='$(FLOW_SVG)', write_to='$(FLOW_PNG)', output_width=2400)\
PY \
	; fi

paper: figures $(TEX)
	xelatex -interaction=nonstopmode -halt-on-error -output-directory=$(PAPER_DIR) $(TEX)
	xelatex -interaction=nonstopmode -halt-on-error -output-directory=$(PAPER_DIR) $(TEX)

clean:
	rm -f $(PAPER_DIR)/*.aux $(PAPER_DIR)/*.log $(PAPER_DIR)/*.out $(PAPER_DIR)/*.toc $(PAPER_DIR)/*.lof $(PAPER_DIR)/*.lot

# Remove generated figure and compiled PDF, but keep source SVG and TeX.
distclean: clean
	rm -f $(FLOW_PNG) $(PDF)
