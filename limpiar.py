import pdfplumber
import re
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
import unicodedata


def normalizar(s: str) -> str:
    """Quita tildes y pone minúsculas para comparar texto."""
    s = unicodedata.normalize("NFD", s)
    s = s.encode("ascii", "ignore").decode("utf-8")
    return s.lower().strip()


def limpiar_pdf(entrada, salida, recorte_inferior=0.10):
    """
    Limpia un PDF eliminando pies de página, números de página,
    índices y espacios innecesarios.
    recorte_inferior: porcentaje del alto a recortar (para eliminar pies).
    """
    texto_total = ""

    with pdfplumber.open(entrada) as pdf:
        total_paginas = len(pdf.pages)
        for i, page in enumerate(pdf.pages, start=1):
            width = page.width
            height = page.height

            # Recorta parte inferior (para quitar pies de página)
            crop_y = height * recorte_inferior
            area_util = page.crop((0, crop_y, width, height))

            texto = area_util.extract_text(layout=True) or ""
            texto_total += texto + "\n\n"
            print(f"✅ Página {i}/{total_paginas} procesada...")

    # --- LIMPIEZA DE TEXTO ---
    t = texto_total

    # 1. Eliminar encabezados o pies con nombre del libro/autor
    patron_footer = (
        r"(?im)^(.*cien\s*años\s*de\s*soledad.*|.*gabriel\s*garcia\s*marquez.*)$"
    )
    t = re.sub(patron_footer, "", t)

    # 2. Eliminar líneas que son solo números de página (ej. 170)
    t = re.sub(r"(?m)^\s*\d+\s*$", "", t)

    # 3. Eliminar índice/tablas de contenido tipo "I....3", "XV....121", etc.
    patron_indice = r"(?mi)^\s*[xivlcdm]+\s*\.*\s*\d+\s*$"
    t = re.sub(patron_indice, "", t)

    # 4. Cortar si detecta gran bloque de puntos y números (índice largo)
    corte_indice = re.search(r"(\.{5,}\s*\d+\s*){5,}", t)
    if corte_indice:
        t = t[: corte_indice.start()]

    # 5. Quitar guiones de fin de línea y espacios extra
    t = re.sub(r"-\n", "", t)
    t = re.sub(r"\s+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = t.strip()

    # --- Generar PDF limpio ---
    c = canvas.Canvas(salida, pagesize=LETTER)
    width, height = LETTER
    x, y = 50, height - 50

    for linea in t.split("\n"):
        if not linea.strip():
            y -= 20
        else:
            c.drawString(x, y, linea)
            y -= 12
        if y < 50:
            c.showPage()
            y = height - 50

    c.save()
    print(f"\n🎉 PDF limpio generado sin pies, índices ni números de página: {salida}")


# --- Ejecutar ---
if __name__ == "__main__":
    limpiar_pdf(
        "cien_soledad.pdf", "cien_anos_de_soledad_limpio.pdf", recorte_inferior=0.10
    )
