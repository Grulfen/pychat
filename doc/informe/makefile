all: informe.pdf

informe.pdf: informe.tex
	pdflatex informe.tex
	pdflatex informe.tex
	pdflatex informe.tex

clean:
	rm -f informe.log informe.aux informe.lot informe.lof informe.toc

cleanall: clean
	rm -f informe.pdf	
