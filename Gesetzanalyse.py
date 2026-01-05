import re
from pathlib import Path
import os
import PyPDF2
import networkx as nx

# Dateipfade definieren

GRAPHVIZ_BIN = r"Beispielpfad"

PDF_FOLDER = Path(
    r"Beispielpfad"
)

OUTPUT_FIGURE_DIR = Path(
    r"Beispielpfad"
)

OUTPUT_FIGURE = OUTPUT_FIGURE_DIR / "gesetzesnetzwerk_graphviz.svg"

OUTPUT_MATRIX_DIR = Path(
    r"Beispielpfad"
)

OUTPUT_MATRIX = OUTPUT_MATRIX_DIR / "matrix_gesetzesnetzwerk2.csv"

os.add_dll_directory(GRAPHVIZ_BIN)
os.environ["PATH"] = GRAPHVIZ_BIN + os.pathsep + os.environ.get("PATH", "")

from networkx.drawing.nx_agraph import to_agraph

# Konfiguration

OUTPUT_FIGURE_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_MATRIX_DIR.mkdir(parents=True, exist_ok=True)

MAX_LABEL_CHARS = 15

NODE_EDGE_COLOR = "#3D6A93"
EDGE_COLOR = "#3D6A93"
NODE_FILL_COLOR = "white"
FONT_FAMILY = "Calibri"
FONT_SIZE = 10

# Hilfsfunktionen definieren

def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extrahiert den Text aus einer PDF-Datei und gibt ihn als String zurück

    Liest alle Seiten der PDF ein, extrahiert den Text je Seite
    und fügt die Textblöcke mit Zeilenumbrüchen zusammen

    Args:
        pdf_path (Path): Pfad zur PDF-Datei

    Returns:
        str: Der extrahierte Text der PDF
    """ 
    text_chunks = []
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_chunks.append(page_text)
    return "\n".join(text_chunks)


def wrap_label(text: str, max_chars: int = 15) -> str:
    """
    Fügt in Text einen Zeilenumbruch vor einem Wort ein, mit dem die gesamte Zeilenlänge eine Anzahl an Zeichen überschreitet

    Args:
        text (str): Der umzubrechende Text
        max_chars (int, optional): Maximale Zeichenanzahl pro Zeile

    Returns:
        str: Der Text mit eingefügten Zeilenumbrüchen
    """
    words = text.split()
    if not words:
        return text

    lines = []
    current_line = words[0]

    for w in words[1:]:
        if len(current_line) + 1 + len(w) <= max_chars:
            current_line += " " + w
        else:
            lines.append(current_line)
            current_line = w

    lines.append(current_line)
    return "\n".join(lines)


def normalize_for_search(s: str) -> str:
    """
    Normalisiert einen Text
    - Nur Kleinbuchstaben
    - Entfernen von Zeilenumbrüchen mit Silbentrennung
    - Reduzieren beliebiger Whitespace-Folgen auf ein einzelnes Leerzeichen
    - Entfernen führender und nachgestellter Leerzeichen

    Args:
        s (str): Eingabetext

    Returns:
        str: Normalisierter Text
    """
    s = s.lower()
    s = re.sub(r"-\s+", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

# PDF einlesen und Namen feststellen

pdf_files = sorted(PDF_FOLDER.glob("*.pdf"))

if not pdf_files:
    raise FileNotFoundError(
        f"Im Ordner {PDF_FOLDER} wurden keine PDF-Dateien gefunden."
    )

laws = [pdf_path.stem for pdf_path in pdf_files]

law_to_pdf = {law: pdf_path for law, pdf_path in zip(laws, pdf_files)}

print("Gefundene Gesetze:")
for law in laws:
    print("  -", law)

# Kategorien und Suchwörter definieren

search_clusters = {law: [] for law in laws}

search_clusters = {
    "CSR-RUG": [
        "CSR-RUG",
        "CSR-Richtlinie-Umsetzungsgesetz",
        "German CSR Directive Implementation Act",
        "CSR Richtlinie Umsetzungsgesetz",
    ],
    "CSRD": [
        "CSRD",
        "2022/2464",
        "Corporate Sustainability Reporting Directive",
        "Richtlinie über die Nachhaltigkeitsberichterstattung von Unternehmen",
    ],
    "DIN EN ISO 14064-1": [
        "14064-1",
        "Spezifikation mit Anleitung zur quantitativen Bestimmung und Berichterstattung von Treibhausgasemissionen und Entzug von Treibhausgasen auf Organisationsebene",
        "Specification with guidance at the organization level for quantification and reporting of greenhouse gas emissions and removals",
        "14064 1",
    ],
    "ESRS": [
        "ESRS",
        "Europäische Standards für die Nachhaltigkeitsberichterstattung",
        "European Sustainability Reporting Standards",
        "2023/2772",
    ],
    "GHG Protocol Corporate Standard": [
        "GHG Protocol",
        "THG Protokoll",
        "GHG-Protocol",
        "Greenhouse Gas Protocol",
    ],
    "GHG Protocol Scope 2 Guidance": [
        "GHG Protocol Scope 2",
        "GHG-Protocol Scope 2",
        "Leitlinien für Scope-2-Emissionen",
        "Leitfaden der Greenhouse Gas Protocol Initiative zur Ermittlung von Scope-2-Emissionen"
    ],
    "GHG Protocol Scope 3 Guidance": [
        "GHG Protocol Technical Guidance for Calculating Scope 3 Emissions",
        "GHG Protocol Scope 3 Guidance",
        "THG Protokoll Scope 3 Leitfaden",
        "GHG Protocol Scope 3 Calculation Guidance",
    ],
    "GHG Protocol Scope 3 Standard": [
        "GHG Protocol Scope 3 Standard",
        "Corporate Value Chain (Scope 3)",
        "Corporate Value Chain Standard",
        "Scope-3-Standard",
    ],
    "GRI 1-3 Universal Standards": [
        "GRI 1",
        "GRI-Standards",
        "GRI Universelle Standards",
        "GRI Universal Standards",
    ],
    "GRI 305 Emissionen": [
        "GRI 305",
        "305-",
        "305: Emission",
        "305 Emission",
    ],
    "IFRS S1 & S2": [
        "IFRS S1",
        "IFRS S2",
        "International Financial Reporting Standards Sustainability",
        "global accounting and sustainability disclosure standards",
    ],
    "NFRD": [
        "2014/95",
        "NFRD",
        "Richtlinie über die nichtfinanzielle Berichterstattung",
        "Non-Financial Reporting Directive",
    ],
    "NFRD Leitlinien klimabezogene Berichterstattung": [
        "2019/C 209/01",
        "Leitlinien für die Berichterstatung über nichtfinanzielle Informationen: Nachtrag zur klimabezogenen Berichterstattung",
        "Guidelines on non-financial reporting: Supplement on reporting climate-related information",
        "NFRD Leitlinien klimabezogene Berichterstattung",
    ],
    "NFRD Leitlinien nichtfinanzielle Informationen": [
        "2017/C 215/01",
        "Leitlinien für die Berichterstattung über nichtfinanzielle Informationen (Methode zur Berichterstattung über nichtfinanzielle Informationen)",
        "Guidelines on non-financial reporting (methodology for reporting non-financial information)",
        "NFRD Leitlinien nichtfinanzielle Informationen",
    ],
    "Taxonomy Regulation": [
        "2020/852",
        "Taxonomie",
        "Taxonomy",
        "establishment of a framework to facilitate sustainable investment",
    ],
    "Taxonomy Regulation Delegierte Verordnung Klima": [
        "2021/2139",
        "Taxonomy Climate Delegated Act",
        "festlegung der technischen Bewertungskriterien, anhand deren bestimmt wird, unter welchen Bedingungen davon auszugehen ist, dass eine Wirtschaftstätigkeit einen wesentlichen Beitrag zum Klimaschutz oder zur Anpassung an den Klimawandel leistet, und anhand deren bestimmt wird, ob diese Wirtschaftstätigkeit erhebliche Beeinträchtigungen eines der übrigen Umweltziele vermeidet",
        "establishing the technical screening criteria for determining the conditions under which an economic activity qualifies as contributing substantially to climate change mitigation or climate change adaptation and for determining whether that economic activity causes no significant harm to any of the other environmental objectives",
    ],
    "Taxonomy Regulation Delegierte Verordnung Offenlegung": [
        "2021/2178",
        "Taxonomy Disclosures Delegated Act",
        "Festlegung des Inhalts und der Darstellung der Informationen, die von Unternehmen, die unter Artikel 19a oder Artikel 29a der Richtlinie 2013/34/EU fallen, in Bezug auf ökologisch nachhaltige Wirtschaftstätigkeiten offenzulegen sind, und durch Festlegung der Methode, anhand deren die Einhaltung dieser Offenlegungspflicht zu gewährleisten ist",
        "specifying the content and presentation of information to be disclosed by undertakings subject to Articles 19a or 29a of Directive 2013/34/EU concerning environmentally sustainable economic activities, and specifying the methodology to comply with that disclosure obligation",
    ],
}

for cluster_name in list(search_clusters.keys()):
    if cluster_name not in laws:
        laws.append(cluster_name)

# Text einlesen und normalisieren

print("\nLese Texte aus PDFs ein...")
law_texts = {}
for law, pdf_path in law_to_pdf.items():
    print(f"  - Lese: {pdf_path.name}")
    law_texts[law] = extract_text_from_pdf(pdf_path)

normalized_law_texts = {
    law: normalize_for_search(text)
    for law, text in law_texts.items()
}

prepared_search_clusters = {
    cluster_name: [
        normalize_for_search(kw)
        for kw in keywords
        if kw.strip()
    ]
    for cluster_name, keywords in search_clusters.items()
}

# Graphisches Netzwerk aufbauen 

G = nx.DiGraph()
G.add_nodes_from(laws)

print("\nSuche nach Suchwort-Clustern in den Gesetzestexten...")

for src_law, text_norm in normalized_law_texts.items():
    print(f"  - Durchsuche: {src_law}")
    for target_cluster, kw_norm_list in prepared_search_clusters.items():
        if not kw_norm_list:
            continue
        if src_law == target_cluster:
            continue

        found = False
        for kw_norm in kw_norm_list:
            if kw_norm and kw_norm in text_norm:
                found = True
                break

        if found:
            G.add_edge(src_law, target_cluster)

print("\nGefundene Verweise:")
for u, v in G.edges():
    print(f"  {u}  -->  {v}")

degrees = {node: G.degree(node) for node in G.nodes}
max_deg = max(degrees.values()) if degrees else 1

# Matrix erzeugen

nodes = list(G.nodes())
n = len(nodes)

matrix = []
for src in nodes:
    row = []
    for tgt in nodes:
        row.append(1 if G.has_edge(src, tgt) else 0)
    matrix.append(row)

row_sums = [sum(row) for row in matrix]
col_sums = [sum(matrix[i][j] for i in range(n)) for j in range(n)]
total_edges = sum(row_sums)

with open(OUTPUT_MATRIX, "w", encoding="utf-8") as f:
    f.write(";" + ";".join(nodes) + ";Summe Zeile\n")
    for i, src in enumerate(nodes):
        row_str = [src] + [str(v) for v in matrix[i]] + [str(row_sums[i])]
        f.write(";".join(row_str) + "\n")
    last_row = ["Summe Spalte"] + [str(s) for s in col_sums] + [str(total_edges)]
    f.write(";".join(last_row) + "\n")

print(f"\Matrix mit Summen gespeichert unter: {OUTPUT_MATRIX.resolve()}")

# Knotengröße nach Anzahl eingehender Kanten gewichten

incoming_weights = {node: G.in_degree(node) for node in G.nodes}
max_incoming = max(incoming_weights.values()) if incoming_weights else 0

MIN_WIDTH = 1.5
MAX_WIDTH = 3

MIN_FONT_SIZE = 14
MAX_FONT_SIZE = 28

if max_incoming > 0:
    step = (MAX_WIDTH - MIN_WIDTH) / max_incoming
else:
    step = 0.0

node_widths = {}
for node in G.nodes:
    w = incoming_weights[node]
    width = MIN_WIDTH + step * w
    node_widths[node] = width

# Graphviz Layout und Ausgabe 
A = to_agraph(G)

A.graph_attr.update(
    overlap="prism",
    sep="+3",
    splines="true",
    outputorder="edgesfirst",
    K="0.07",
)

A.node_attr.update(
    shape="circle",
    style="filled",
    fillcolor=NODE_FILL_COLOR,
    color=NODE_EDGE_COLOR,
    fontname=FONT_FAMILY,
    fontsize=str(FONT_SIZE),
    fixedsize="true",
)

A.edge_attr.update(
    color=EDGE_COLOR,
    arrowsize="0.8",
    penwidth="1.1",
)

for node in G.nodes:
    ag_node = A.get_node(node)
    ag_node.attr["label"] = wrap_label(node, max_chars=MAX_LABEL_CHARS)

    width = node_widths[node]
    ag_node.attr["width"] = f"{width:.2f}"
    ag_node.attr["height"] = f"{width:.2f}"

    if MAX_WIDTH > MIN_WIDTH:
        rel = (width - MIN_WIDTH) / (MAX_WIDTH - MIN_WIDTH)
    else:
        rel = 0.0
    font_size = MIN_FONT_SIZE + rel * (MAX_FONT_SIZE - MIN_FONT_SIZE)
    ag_node.attr["fontsize"] = f"{font_size:.1f}"

    min_len = 0.01
    max_len = 0.5

for edge in A.edges():
    u = edge[0]
    v = edge[1]
    d = min(degrees.get(u, 0), degrees.get(v, 0))

    if max_deg > 0:
        rel = d / max_deg
    else:
        rel = 0.0

    len_val = min_len + rel * (max_len - min_len)
    edge.attr["len"] = f"{len_val:.2f}"

A.draw(str(OUTPUT_FIGURE), prog="sfdp")

print(f"\nGrafik (Graphviz) gespeichert unter: {OUTPUT_FIGURE.resolve()}")
