# Repository-level convenience Makefile.
#
# The actual paper build logic lives in paper/Makefile so figure paths remain
# local to the LaTeX source directory.

.PHONY: all paper figures clean distclean check-tools

all: paper

paper:
	$(MAKE) -C paper paper

figures:
	$(MAKE) -C paper figures

check-tools:
	$(MAKE) -C paper check-tools

clean:
	$(MAKE) -C paper clean

distclean:
	$(MAKE) -C paper distclean
