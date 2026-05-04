# OpenAyane RDE paper build helper
#
# Targets:
#   make              Build PNG figures and the Japanese PDF paper.
#   make figures      Convert SVG figures into PNG files used by LaTeX.
#   make paper        Build the PDF. This depends on PNG figure generation.
#   make clean        Remove LaTeX intermediate files.
#   make distclean    Remove generated PNG/PDF outputs as well.

SHELL := /bin/sh

PAPER_DIR := paper
FIG_DIR := $(PAPER_DIR)/figures

TEX := $(PAPER_DIR)/openayane_implementation_plan_final_ja.tex
PDF := $(PAPER_DIR)/openayane_implementation_plan_final_ja.pdf

FLOW_SVG := $(FIG_DIR)/openayane_implementation_flow.svg
FLOW_PNG := $(FIG_DIR)/openayane_implementation_flow.png

LATEX := xelatex
LATEXFLAGS := -interaction=nonstopmode -halt-on-error -output-directory=$(PAPER_DIR)
PNG_WIDTH := 2400

.PHONY: all figures paper clean distclean check-tools

all: paper

# PNG assets consumed by LaTeX.
figures: $(FLOW_PNG)

# Build the PNG from SVG. LaTeX includes the PNG, not the SVG.
$(FLOW_PNG): $(FLOW_SVG)
	@mkdir -p $(FIG_DIR)
	@if command -v inkscape >/dev/null 2>&1; then \
		echo "[figures] inkscape: $< -> $@"; \
		inkscape "$<" --export-type=png --export-filename="$@" --export-width=$(PNG_WIDTH); \
	elif command -v rsvg-convert >/dev/null 2>&1; then \
		echo "[figures] rsvg-convert: $< -> $@"; \
		rsvg-convert -w $(PNG_WIDTH) -o "$@" "$<"; \
	else \
		echo "[figures] python/cairosvg: $< -> $@"; \
		python3 -c "import cairosvg; cairosvg.svg2png(url='$(FLOW_SVG)', write_to='$(FLOW_PNG)', output_width=$(PNG_WIDTH))"; \
	fi

# The PDF explicitly depends on the PNG figure so the paper always embeds the generated PNG.
$(PDF): $(TEX) $(FLOW_PNG)
	$(LATEX) $(LATEXFLAGS) $(TEX)
	$(LATEX) $(LATEXFLAGS) $(TEX)

paper: $(PDF)

check-tools:
	@echo "LaTeX: $$($(LATEX) --version 2>/dev/null | head -n 1 || echo 'missing')"
	@echo "inkscape: $$(command -v inkscape || echo 'missing')"
	@echo "rsvg-convert: $$(command -v rsvg-convert || echo 'missing')"
	@python3 -c "import cairosvg; print('cairosvg: available')" 2>/dev/null || echo "cairosvg: missing"

clean:
	rm -f $(PAPER_DIR)/*.aux \
	      $(PAPER_DIR)/*.log \
	      $(PAPER_DIR)/*.out \
	      $(PAPER_DIR)/*.toc \
	      $(PAPER_DIR)/*.lof \
	      $(PAPER_DIR)/*.lot \
	      $(PAPER_DIR)/*.fls \
	      $(PAPER_DIR)/*.fdb_latexmk \
	      $(PAPER_DIR)/*.synctex.gz

# Remove generated figure and compiled PDF, but keep source SVG and TeX.
distclean: clean
	rm -f $(FLOW_PNG) $(PDF)
