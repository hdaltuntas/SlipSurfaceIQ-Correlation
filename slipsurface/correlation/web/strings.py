"""
Text of the interface shell.

Nothing is written into the page: the browser fetches this dictionary from
`/api/meta`, so changing the language is handled in one place and the wording
sits beside the rest of the program's translations. Whatever `i18n` already
says is reused; only what the web shell adds of its own is spelled out here.
"""

from __future__ import annotations

from ..i18n import TRANSLATIONS

#: Text the web shell needs and the rest of the program does not.
#: key -> (English, Turkish)
SHELL = {
    "tagline": ("soil parameters from laboratory and field tests",
                "laboratuvar ve arazi deneylerinden zemin parametreleri"),
    "language": ("Language", "Dil"),
    "open": ("Open…", "Aç…"),
    "save": ("Save", "Kaydet"),
    "theme": ("Theme", "Tema"),
    "ready": ("Ready.", "Hazır."),
    "tab_inputs": ("1 · Layers and laboratory", "1 · Tabakalar ve laboratuvar"),
    "tab_tests": ("2 · Field tests", "2 · Arazi deneyleri"),
    "tab_options": ("3 · Correlations", "3 · Korelasyonlar"),
    "add_row": ("+ Add row", "+ Satır ekle"),
    "del_row": ("− Remove row", "− Satır sil"),
    "paste": ("Paste…", "Yapıştır…"),
    "clear": ("Clear", "Temizle"),
    "paste_title": ("Paste rows", "Satır yapıştır"),
    "paste_help": ("Paste columns copied from a spreadsheet or a text file, one reading per "
                   "line, in this order: {columns}. Lines that are not numbers (headings) are "
                   "skipped.",
                   "Hesap tablosundan ya da metin dosyasından kopyaladığınız sütunları, her "
                   "satıra bir okuma gelecek şekilde, şu sırayla yapıştırın: {columns}. Sayı "
                   "olmayan satırlar (başlıklar) atlanır."),
    "paste_replace": ("Replace the table", "Tabloyu değiştir"),
    "paste_append": ("Add to the table", "Tabloya ekle"),
    "paste_cancel": ("Cancel", "Vazgeç"),
    "pasted": ("{n} row(s) read.", "{n} satır okundu."),
    "soil_group": ("Soil profile and laboratory results (from the ground surface down)",
                   "Zemin profili ve laboratuvar sonuçları (yüzeyden aşağı)"),
    "spt_group": ("SPT blow counts", "SPT darbe sayıları"),
    "cpt_group": ("CPT(u) readings", "CPT(u) okumaları"),
    "vs_group": ("Measured shear wave velocities", "Ölçülen kayma dalgası hızları"),
    "export_group": ("Send the parameters on", "Parametreleri aktar"),
    "view_summary": ("Parameters", "Parametreler"),
    "view_methods": ("By correlation", "Korelasyonlara göre"),
    "view_tests": ("Tests", "Deneyler"),
    "view_text": ("Results", "Sonuçlar"),
    "view_figures": ("Figures", "Şekiller"),
    "figure": ("Figure", "Şekil"),
    "report_format": ("Report", "Rapor"),
    "report_pdf": ("PDF report", "PDF rapor"),
    "report_html": ("HTML report", "HTML rapor"),
    "report_docx": ("Word report", "Word rapor"),
    "no_results": ("Derive the parameters first.", "Önce parametreleri üretin."),
    "error": ("Error", "Hata"),
    "saved": ("Saved.", "Kaydedildi."),
    "loaded": ("Project loaded.", "Proje yüklendi."),
    "bad_file": ("That file is not a SlipSurface IQ Correlation project.",
                 "Bu dosya bir SlipSurface IQ Correlation projesi değil."),
    "stop_hint": ("Press Ctrl+C to stop.", "Durdurmak için Ctrl+C."),
    "stopped": ("stopped", "durduruldu"),
}

#: Keys taken straight from the program's translations, under the same name.
REUSED = [
    "run_analysis_button", "running_analysis", "analysis_complete", "report_action",
    "report_running", "warnings_title", "soil_note", "tests_note", "export_settle",
    "export_bearing", "export_csv", "export_note",
]


def shell_strings(lang: str = "en") -> dict:
    """Every string the page needs, in one language."""
    translations = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    strings = {key: (tr if lang == "tr" else en) for key, (en, tr) in SHELL.items()}
    strings.update({key: translations[key] for key in REUSED})
    return strings
