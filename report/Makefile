# Configuration
LATEXMK = latexmk
MAIN = report

# Règle par défaut : génère le fichier PDF
compile: $(MAIN).pdf

# Compilation avec latexmk
$(MAIN).pdf: $(MAIN).tex
	$(LATEXMK) -pdf $(MAIN).tex  # Compile en PDF

# Nettoyage des fichiers temporaires générés par la compilation
clean:
	find . -type f \( \
		-name "*.aux" -o -name "*.log" -o -name "*.out" -o -name "*.toc" \
		-o -name "*.lof" -o -name "*.lot" -o -name "*.bbl" -o -name "*.blg" \
		-o -name "*.maf" -o -name "*.mtc*" -o -name "*.thm" -o -name "*.synctex.gz" \
		-o -name "*.ptc*" -o -name "*.fls" -o -name "*.fdb_latexmk" \
	\) -delete

# Nettoyage complet : enlève le PDF et les fichiers temporaires
cleanall: clean
	rm -f $(MAIN).pdf

# Si tu veux utiliser latexmk en mode "continu" (pour recompiler automatiquement en cas de modification)
watch:
	$(LATEXMK) -pdf -pvc $(MAIN).tex

view: $(MAIN).pdf
	open $(MAIN).pdf

help:
	@echo "Makefile commands:"
	@echo "  compile      - Compile the main PDF"
	@echo "  clean        - Remove auxiliary files"
	@echo "  cleanall     - Remove auxiliary files and PDF"
	@echo "  view         - Open the PDF"
	@echo "  bib          - Run bibtex"

