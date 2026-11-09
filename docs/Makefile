# namelint documentation - Zensical build

ZENSICAL := uv run zensical

.PHONY: help preprocess build serve deploy clean

help:
	@echo "namelint documentation (Zensical)"
	@echo ""
	@echo "  make build    - Build the site into site/"
	@echo "  make serve    - Start the local development server"
	@echo "  make deploy   - Build, then deploy with hop3"
	@echo "  make clean    - Remove the site and the copied pages"

# The check pages are the files `namelint explain` prints, and the changelog
# is CHANGES.md: copied, not duplicated, so the site cannot drift from them.
preprocess:
	mkdir -p src/checks
	cp ../src/namelint/data/explain/*.md src/checks/
	cp ../CHANGES.md src/changelog.md

build: preprocess
	$(ZENSICAL) build

serve: preprocess
	$(ZENSICAL) serve --open

deploy: build
	hop3 deploy

clean:
	rm -rf site/ src/checks/ src/changelog.md
