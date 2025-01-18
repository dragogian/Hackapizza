import os

import pikepdf

def clean_pdf(input_pdf: str, output_pdf: str):
    with pikepdf.Pdf.open(input_pdf) as pdf:
        # Itera sulle pagine del PDF
        for page in pdf.pages:
            # Ottiene le risorse della pagina
            resources = page.Resources

            # Verifica se esiste la sezione XObject (dove sono conservate immagini e altri oggetti esterni)
            xobjects = resources.get("/XObject", {})

            # Rimuove tutte le immagini (XObject) trovate
            for xobj_name in list(xobjects.keys()):
                del xobjects[xobj_name]

        # Salva il risultato
        pdf.save(output_pdf)

    print("PDF salvato senza immagini in:", output_pdf)

    # Rimuove il file PDF di input
    os.remove(input_pdf)
    print(f"File di input {input_pdf} rimosso.")
