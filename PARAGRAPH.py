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
    Estrae l'introduzione e i paragrafi relativi ai piatti da un PDF.
    Restituisce una lista di stringhe, una per l'introduzione e una per ogni piatto.
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
                # Raggruppa caratteri in righe basate su 'top' e 'x'
                chars = pagina.chars
                lines = {}
                for char in chars:
                    line_top = round(char['top'])  # Round to avoid minor differences
                    if line_top not in lines:
                        lines[line_top] = []
                    lines[line_top].append(char)

                # Ricostruisci le righe ordinate per posizione 'x'
                for top in sorted(lines.keys()):
                    line_chars = sorted(lines[top], key=lambda c: c['x'])
                    line_text = ''.join(c['text'] for c in line_chars)
                    testo_completo += line_text + "\n"

            # Debug: Mostra l'anteprima del testo ricostruito
            print("Testo ricostruito:\n", testo_completo[:500])

        # Estrarre l'introduzione
        introduzione_match = re.search(
            r'(Ristorante .*? Chef .*?)(?=\nMenu)',
            testo_completo,
            re.DOTALL
        )
        introduzione_testo = ""
        if introduzione_match:
            introduzione_testo = introduzione_match.group(1).strip()
            paragrafi.append(f"Introduzione:\n\n{introduzione_testo}")
            print("Introduzione trovata.")
        else:
            print("Avviso: Introduzione non trovata nel testo estratto.")

        # Estrarre i piatti con ingredienti e tecniche
        pattern_piatto = re.compile(
            r'(?<=Menu)\n+([^\\n]+)\n+Ingredienti:\n((?:[^\n]+\n?)+?)\n+Tecniche:\n((?:[^\n]+\n?)+?)',
            re.DOTALL
        )
        matches = pattern_piatto.finditer(testo_completo)

        for match in matches:
            titolo = match.group(1).strip()
            ingredienti = match.group(2).strip()
            tecniche = match.group(3).strip()

            paragrafo = (
                f"{introduzione_testo}\n\n"
                f"Titolo: {titolo}\n\n"
                f"Ingredienti:\n{ingredienti}\n\n"
                f"Tecniche:\n{tecniche}"
            )
            paragrafi.append(paragrafo)

        if len(paragrafi) <= 1:
            print("Errore: Nessun piatto trovato. Verifica il formato del PDF e le regex.")
        else:
            print(f"Trovati {len(paragrafi) - 1} paragrafi di piatti (esclusa l'introduzione).")

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
