# OpenAyane RDE paper-local build helper
#
# This Makefile is intentionally placed under paper/ so LaTeX resolves
# relative figure paths such as figures/openayane_implementation_flow.png.
#
# Targets:
#   make              Build PNG figures and the PDF paper.
#   make figures      Convert SVG figures into PNG files used by LaTeX.
#   make paper        Build the PDF. This depends on PNG figure generation.
#   make clean        Remove LaTeX intermediate files.
#   make distclean    Remove generated PNG/PDF outputs as well.

SHELL := /bin/sh

FIG_DIR := figures

TEX_NAME := openayane_implementation_plan_final_ja.tex
PDF_NAME := openayane_implementation_plan_final_ja.pdf

FLOW_SVG := $(FIG_DIR)/openayane_implementation_flow.svg
FLOW_PNG := $(FIG_DIR)/openayane_implementation_flow.png

LATEX := xelatex
LATEXFLAGS := -interaction=nonstopmode -halt-on-error
PNG_WIDTH := 2400

.PHONY: all figures paper clean distclean check-tools

all: paper

figures: $(FLOW_PNG)

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

# The PDF explicitly depends on the generated PNG figure.
$(PDF_NAME): $(TEX_NAME) $(FLOW_PNG)
	$(LATEX) $(LATEXFLAGS) $(TEX_NAME)
	$(LATEX) $(LATEXFLAGS) $(TEX_NAME)

paper: $(PDF_NAME)

check-tools:
	@echo "LaTeX: $$($(LATEX) --version 2>/dev/null | head -n 1 || echo 'missing')"
	@echo "inkscape: $$(command -v inkscape || echo 'missing')"
	@echo "rsvg-convert: $$(command -v rsvg-convert || echo 'missing')"
	@python3 -c "import cairosvg; print('cairosvg: available')" 2>/dev/null || echo "cairosvg: missing"

clean:
	rm -f *.aux \
	      *.log \
	      *.out \
	      *.toc \
	      *.lof \
	      *.lot \
	      *.fls \
	      *.fdb_latexmk \
	      *.synctex.gz

distclean: clean
	rm -f $(FLOW_PNG) $(PDF_NAME)
