import pdfplumber
import re
import textwrap
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from pathlib import Path

# Nome del file PDF originale
pdf_file = "resources_cleaned/Anima Cosmica_cleaned.pdf"

def estrai_paragrafi(file_pdf):
    """
    Estrae i piatti, ingredienti e tecniche da un PDF.
    Restituisce una lista di stringhe, una per ogni piatto.
    """
    paragrafi = []

    file_path = Path(file_pdf)
    if not file_path.is_file():
        print(f"Errore: Il file '{file_pdf}' non esiste.")
        return paragrafi

    try:
        # Apri il PDF con pdfplumber
        with pdfplumber.open(file_path) as pdf:
            testo_completo = ""
            for pagina in pdf.pages:
                testo_pagina = pagina.extract_text()
                if testo_pagina:
                    testo_completo += testo_pagina + "\n"

            # Verifica che il testo estratto non sia vuoto
            if not testo_completo.strip():
                print("Errore: Il PDF non contiene testo leggibile.")
                return paragrafi

            print("Testo estratto dal PDF con successo.")

        # Trova i blocchi di testo che corrispondono ai piatti
        pattern_piatto = re.compile(
            r'(?P<titolo>^[^\n]+?)\n+Ingredienti:?\n(?P<ingredienti>.+?)\n+Tecniche:?\n(?P<tecniche>.+?)(?=\n[^\n]|\Z)',
            re.DOTALL | re.MULTILINE
        )
        matches = pattern_piatto.finditer(testo_completo)

        for match in matches:
            titolo = match.group("titolo").strip()
            ingredienti = match.group("ingredienti").strip()
            tecniche = match.group("tecniche").strip()

            # Costruisco il paragrafo
            paragrafo = (
                f"Titolo: {titolo}\n\n"
                f"Ingredienti:\n{ingredienti}\n\n"
                f"Tecniche:\n{tecniche}"
            )
            paragrafi.append(paragrafo)

        if not paragrafi:
            print("Errore: Nessun piatto trovato.")
        else:
            print(f"Trovati {len(paragrafi)} paragrafi di piatti.")

    except Exception as e:
        print(f"Errore durante l'estrazione del testo: {e}")

    return paragrafi

def crea_pdf(paragrafo, nome_file, max_line_width=90):
    """
    Crea un PDF a partire da un blocco di testo 'paragrafo'.
    Esegue un word-wrap di base per evitare che le righe siano troppo lunghe.
    """
    try:
        pdf = canvas.Canvas(str(nome_file), pagesize=letter)
        pdf.setFont("Helvetica", 10)

        # Margini e spaziatura
        x_margin, y_margin = 50, 750
        line_spacing = 12

        # Word wrapping
        text_lines = []
        for line in paragrafo.split("\n"):
            if not line.strip():
                text_lines.append("")
                continue
            wrapped = textwrap.wrap(line, width=max_line_width)
            if wrapped:
                text_lines.extend(wrapped)
            else:
                text_lines.append("")

        # Scrittura riga per riga, con gestione del cambio pagina
        for line in text_lines:
            pdf.drawString(x_margin, y_margin, line)
            y_margin -= line_spacing
            if y_margin < 50:
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y_margin = 750

        pdf.save()
        print(f"Creato PDF: {nome_file}")
    except Exception as e:
        print(f"Errore nella creazione del file {nome_file}: {e}")

# ----------------------------------------------------------------------
# SCRIPT PRINCIPALE
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Estrae i paragrafi dal PDF di origine
    paragrafi_estratti = estrai_paragrafi(pdf_file)

    # Crea la directory di output se non esiste
    output_dir = Path("output_pdfs")
    output_dir.mkdir(exist_ok=True)

    # Se abbiamo estratto dei paragrafi, creiamo un PDF per ciascuno
    if paragrafi_estratti:
        for i, paragrafo in enumerate(paragrafi_estratti, start=1):
            nome_file_pdf = output_dir / f"{Path(pdf_file).stem}_{i}.pdf"
            crea_pdf(paragrafo, nome_file_pdf)
    else:
        print("Nessun PDF da creare (nessun paragrafo trovato).")
