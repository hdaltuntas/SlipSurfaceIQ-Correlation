"""
Every text of SlipSurface IQ Correlation, in English and Turkish.

Each entry is written once as ``key: (English, Turkish)`` so the two languages
cannot drift apart: a key without its translation is a syntax error, not a
blank on the screen. `TRANSLATIONS[lang][key]` is how the rest of the program
reads them.

The correlations themselves are cited by author and year, and their formulas
are written in symbols, so they read the same in both languages and live in
`slipsurface.correlation.correlations`.
"""

from __future__ import annotations

ENTRIES = {
    # ------------------------------------------------------------------ input errors
    "err_no_layers": ("The soil profile has no layer with a thickness.",
                      "Zemin profilinde kalınlığı girilmiş tabaka yok."),
    "err_water": ("The depth of the water table cannot be negative.",
                  "Su tablası derinliği negatif olamaz."),
    "err_gamma_w": ("The unit weight of water must be between 9 and 11 kN/m³.",
                    "Suyun birim hacim ağırlığı 9 ile 11 kN/m³ arasında olmalıdır."),
    "err_area_ratio": ("The cone's net area ratio a must be greater than 0 and at most 1.",
                       "Koninin net alan oranı a, 0'dan büyük ve en çok 1 olmalıdır."),
    "err_factor": ("{name} must be greater than zero.", "{name} sıfırdan büyük olmalıdır."),
    "err_negative": ("Layer '{name}': {field} cannot be negative.",
                     "'{name}' tabakası: {field} negatif olamaz."),
    "err_fractions": ("Layer '{name}': gravel and fines together exceed 100 %.",
                      "'{name}' tabakası: çakıl ve ince dane oranlarının toplamı %100'ü aşıyor."),
    "err_nu": ("Poisson's ratio must be between 0 and 0.5.",
               "Poisson oranı 0 ile 0.5 arasında olmalıdır."),

    # ------------------------------------------------------------------ warnings
    "warn_gamma_typical": ("Layer '{name}': no unit weight was entered or could be estimated; "
                           "a typical value was used.",
                           "'{name}' tabakası: birim hacim ağırlığı girilmedi ve tahmin "
                           "edilemedi; tipik bir değer kullanıldı."),
    "warn_test_outside": ("A {test} result at {depth:.2f} m lies outside the soil profile and "
                          "was left out.",
                          "{depth:.2f} m'deki {test} sonucu zemin profilinin dışında kaldığından "
                          "hesaba katılmadı."),
    "warn_refusal": ("SPT at {depth:.2f} m: N ≥ 50 is refusal; the correlations stretch beyond "
                     "the data they were fitted to.",
                     "{depth:.2f} m'deki SPT: N ≥ 50 çakma direncidir (refü); korelasyonlar "
                     "türetildikleri veri aralığının dışında kalır."),
    "warn_cpt_skipped": ("{n} CPT reading(s) could not be normalised (qt ≤ σv0 or fs ≤ 0) and "
                         "were left out.",
                         "{n} CPT okuması normalize edilemedi (qt ≤ σv0 ya da fs ≤ 0) ve hesaba "
                         "katılmadı."),
    "warn_method_missing": ("Layer '{name}': the chosen correlation for {param} ({method}) has "
                            "no data here; the correlations were combined instead.",
                            "'{name}' tabakası: {param} için seçilen korelasyonun ({method}) "
                            "burada verisi yok; korelasyonlar birleştirildi."),
    "warn_ocr_low": ("Layer '{name}': the correlations give OCR = {ocr:.2f} < 1; an "
                     "under-consolidated clay, or a spread of the correlations — check it.",
                     "'{name}' tabakası: korelasyonlar OCR = {ocr:.2f} < 1 veriyor; eksik "
                     "konsolide kil ya da korelasyon saçılması olabilir — kontrol edin."),
    "warn_ic_clay": ("Layer '{name}' is entered as granular, but the CPT reads it as clay-like "
                     "(mean Ic = {ic:.2f}).",
                     "'{name}' tabakası granüler girildi, fakat CPT onu kil benzeri okuyor "
                     "(ortalama Ic = {ic:.2f})."),
    "warn_ic_sand": ("Layer '{name}' is entered as cohesive, but the CPT reads it as sand-like "
                     "(mean Ic = {ic:.2f}).",
                     "'{name}' tabakası kohezyonlu girildi, fakat CPT onu kum benzeri okuyor "
                     "(ortalama Ic = {ic:.2f})."),
    "warn_no_data": ("Layer '{name}' has no test result a correlation can use.",
                     "'{name}' tabakasında korelasyonların kullanabileceği deney sonucu yok."),

    # ------------------------------------------------------------------ choice labels
    "behaviour_granular": ("Granular", "Granüler"),
    "behaviour_cohesive": ("Cohesive", "Kohezyonlu"),
    "sampler_standard": ("Standard (with liners)", "Standart (gömlekli)"),
    "sampler_no_liner": ("Without liners", "Gömleksiz"),
    "cn_liao_whitman": ("Liao & Whitman (1986)", "Liao & Whitman (1986)"),
    "cn_skempton": ("Skempton (1986)", "Skempton (1986)"),
    "combine_median": ("Median of the correlations", "Korelasyonların medyanı"),
    "combine_mean": ("Mean of the correlations", "Korelasyonların ortalaması"),
    "combine_cautious": ("Cautious estimate (mean ∓ 0.5·s)",
                         "İhtiyatlı tahmin (ortalama ∓ 0.5·s)"),
    "method_auto": ("All — combined", "Tümü — birleştirilmiş"),
    "how_combined": ("combined", "birleştirilmiş"),
    "how_input": ("entered", "girilen"),
    "how_typical": ("typical value", "tipik değer"),

    # ------------------------------------------------------------------ parameters
    "param_gamma": ("Unit weight γ", "Birim hacim ağırlık γ"),
    "param_gamma_sat": ("Saturated unit weight γsat", "Doygun birim hacim ağırlık γdoy"),
    "param_e0": ("Void ratio e0", "Boşluk oranı e0"),
    "param_Dr": ("Relative density Dr", "Rölatif sıkılık Dr"),
    "param_phi": ("Friction angle φ'", "İçsel sürtünme açısı φ'"),
    "param_cu": ("Undrained shear strength cu", "Drenajsız kayma dayanımı cu"),
    "param_sigma_p": ("Preconsolidation pressure σ'p", "Önkonsolidasyon basıncı σ'p"),
    "param_OCR": ("Overconsolidation ratio OCR", "Aşırı konsolidasyon oranı OCR"),
    "param_K0": ("Earth pressure at rest K0", "Sükûnetteki toprak basıncı K0"),
    "param_E": ("Drained modulus E'", "Drenajlı elastisite modülü E'"),
    "param_Eu": ("Undrained modulus Eu", "Drenajsız elastisite modülü Eu"),
    "param_M": ("Constrained modulus M", "Ödometrik modül M"),
    "param_Cc": ("Compression index Cc", "Sıkışma indisi Cc"),
    "param_Cr": ("Recompression index Cr", "Yeniden sıkışma indisi Cr"),
    "param_Calpha": ("Secondary compression index Cα", "İkincil sıkışma indisi Cα"),
    "param_cv": ("Coefficient of consolidation cv", "Konsolidasyon katsayısı cv"),
    "param_Vs": ("Shear wave velocity Vs", "Kayma dalgası hızı Vs"),
    "param_G0": ("Small-strain shear modulus G0", "Küçük birim deformasyon kayma modülü G0"),
    "param_k": ("Hydraulic conductivity k", "Permeabilite katsayısı k"),
    "sym_gamma": ("γ", "γ"), "sym_gamma_sat": ("γsat", "γdoy"), "sym_e0": ("e0", "e0"),
    "sym_Dr": ("Dr", "Dr"), "sym_phi": ("φ'", "φ'"), "sym_cu": ("cu", "cu"),
    "sym_sigma_p": ("σ'p", "σ'p"), "sym_OCR": ("OCR", "OCR"), "sym_K0": ("K0", "K0"),
    "sym_E": ("E'", "E'"), "sym_Eu": ("Eu", "Eu"), "sym_M": ("M", "M"), "sym_Cc": ("Cc", "Cc"),
    "sym_Cr": ("Cr", "Cr"), "sym_Calpha": ("Cα", "Cα"), "sym_cv": ("cv", "cv"),
    "sym_Vs": ("Vs", "Vs"), "sym_G0": ("G0", "G0"), "sym_k": ("k", "k"),
    "unit_m2yr": ("m²/yr", "m²/yıl"),

    # ------------------------------------------------------------------ non-literature sources
    "ref_phase": ("Phase relations", "Faz bağıntıları"),
    "ref_phase_sat": ("Phase relations (S = 1)", "Faz bağıntıları (S = 1)"),
    "ref_lab": ("Laboratory", "Laboratuvar"),
    "ref_qu": ("Unconfined compression", "Serbest basınç"),
    "ref_definition": ("Definition", "Tanım"),
    "ref_nc": ("Normally consolidated (assumed)", "Normal konsolide (kabul)"),
    "ref_cv": ("Terzaghi (k and M from the CPT)", "Terzaghi (k ve M CPT'den)"),
    "ref_measured": ("Measured (seismic)", "Ölçülen (sismik)"),
    "ref_elastic": ("Elasticity", "Elastisite"),

    # ------------------------------------------------------------------ test sources
    "source_spt": ("SPT", "SPT"),
    "source_cpt": ("CPT", "CPT"),
    "source_lab": ("Laboratory", "Laboratuvar"),
    "source_vs": ("Seismic", "Sismik"),
    "source_derived": ("Derived", "Türetilmiş"),

    # ------------------------------------------------------------------ SBT zones
    "zone_2": ("Organic soils – clay", "Organik zemin – kil"),
    "zone_3": ("Clay – silty clay", "Kil – siltli kil"),
    "zone_4": ("Silt mixtures", "Silt karışımları"),
    "zone_5": ("Sand mixtures", "Kum karışımları"),
    "zone_6": ("Sands – clean to silty", "Kum – temiz ile siltli"),
    "zone_7": ("Gravelly sand – dense sand", "Çakıllı kum – sıkı kum"),

    # ------------------------------------------------------------------ groups and fields
    "group_project": ("Project", "Proje"),
    "title_label": ("Title", "Başlık"),
    "analyst_label": ("Analyst", "Hazırlayan"),
    "group_water": ("Groundwater", "Yeraltı suyu"),
    "water_depth_label": ("Depth of the water table", "Su tablası derinliği"),
    "gamma_w_label": ("Unit weight of water γw", "Suyun birim hacim ağırlığı γw"),
    "group_spt": ("SPT corrections", "SPT düzeltmeleri"),
    "er_label": ("Hammer energy ratio ER", "Tokmak enerji oranı ER"),
    "borehole_label": ("Borehole diameter", "Sondaj çapı"),
    "sampler_label": ("Sampler", "Numune alıcı"),
    "stickup_label": ("Rod above the ground", "Zemin üstündeki tij boyu"),
    "cn_method_label": ("Overburden correction CN", "Örtü yükü düzeltmesi CN"),
    "cn_max_label": ("Upper limit of CN", "CN üst sınırı"),
    "spt_note": ("N60 = N·(ER/60)·CB·CS·CR; (N1)60 = CN·N60. Safety hammers deliver about 60 %, "
                 "donut hammers about 45 %, automatic trip hammers 80 % or more.",
                 "N60 = N·(ER/60)·CB·CS·CR; (N1)60 = CN·N60. Emniyetli tokmak yaklaşık %60, "
                 "halka (donut) tokmak yaklaşık %45, otomatik tokmak %80 ve üzeri enerji "
                 "aktarır."),
    "group_cpt": ("CPT(u)", "CPT(u)"),
    "area_ratio_label": ("Net area ratio of the cone a", "Koninin net alan oranı a"),
    "nkt_label": ("Cone factor Nkt", "Koni faktörü Nkt"),
    "ndu_label": ("Pore pressure factor NΔu", "Boşluk suyu faktörü NΔu"),
    "cpt_note": ("qt = qc + u2·(1 − a). Nkt is typically 10 – 20 (14 on average) and NΔu 4 – 10; "
                 "calibrate them against laboratory or vane tests where you can.",
                 "qt = qc + u2·(1 − a). Nkt genellikle 10 – 20 (ortalama 14), NΔu 4 – 10 "
                 "arasındadır; mümkünse laboratuvar veya veyn deneyiyle kalibre edin."),
    "group_options": ("Selection", "Seçim"),
    "combine_label": ("Combine the correlations by", "Korelasyonları birleştirme"),
    "eu_ratio_label": ("Eu / cu", "Eu / cu"),
    "nu_granular_label": ("ν of granular layers (export)", "Granüler tabaka ν (aktarım)"),
    "nu_cohesive_label": ("ν of cohesive layers (export)", "Kohezyonlu tabaka ν (aktarım)"),
    "options_note": ("Every parameter comes from the correlation chosen below, or from all of "
                     "those that apply, combined. A cautious estimate takes the mean less half a "
                     "standard deviation for a strength or a stiffness, and plus it for a "
                     "compressibility (Schneider 1997).",
                     "Her parametre aşağıda seçilen korelasyondan ya da uygulanabilen tüm "
                     "korelasyonların birleşiminden elde edilir. İhtiyatlı tahmin, dayanım ve "
                     "rijitlikte ortalamadan yarım standart sapma çıkarır, sıkışabilirlikte ekler "
                     "(Schneider 1997)."),
    "group_methods": ("Correlation for each parameter", "Her parametre için korelasyon"),
    "soil_note": ("Zero means not measured: the program estimates what it can. Fines (< 0.075 mm) "
                  "and gravel (> 4.75 mm) in %, w in %, D10 in mm, qu the unconfined "
                  "compressive strength.",
                  "Sıfır, ölçülmedi demektir: program tahmin edebildiğini tahmin eder. İnce dane "
                  "(< 0.075 mm) ve çakıl (> 4.75 mm) % olarak, w %, D10 mm, qu serbest basınç "
                  "dayanımı."),
    "tests_note": ("Depths are below the ground surface. Paste a column block copied from a "
                   "spreadsheet with the Paste button.",
                   "Derinlikler zemin yüzeyinden ölçülür. Hesap tablosundan kopyalanan sütunları "
                   "Yapıştır düğmesiyle ekleyebilirsiniz."),

    # ------------------------------------------------------------------ table columns
    "col_name": ("Layer", "Tabaka"),
    "col_thickness": ("Thickness (m)", "Kalınlık (m)"),
    "col_behaviour": ("Behaviour", "Davranış"),
    "col_gravel": ("Gravel (%)", "Çakıl (%)"),
    "col_fines": ("Fines (%)", "İnce (%)"),
    "col_LL": ("LL (%)", "LL (%)"),
    "col_PL": ("PL (%)", "PL (%)"),
    "col_w": ("w (%)", "w (%)"),
    "col_Gs": ("Gs", "Gs"),
    "col_gamma": ("γ (kN/m³)", "γ (kN/m³)"),
    "col_gamma_sat": ("γsat (kN/m³)", "γdoy (kN/m³)"),
    "col_e0": ("e0", "e0"),
    "col_D10": ("D10 (mm)", "D10 (mm)"),
    "col_qu": ("qu (kPa)", "qu (kPa)"),
    "col_depth": ("Depth (m)", "Derinlik (m)"),
    "col_N": ("N (blows/30 cm)", "N (darbe/30 cm)"),
    "col_qc": ("qc (MPa)", "qc (MPa)"),
    "col_fs": ("fs (kPa)", "fs (kPa)"),
    "col_u2": ("u2 (kPa)", "u2 (kPa)"),
    "col_Vs": ("Vs (m/s)", "Vs (m/s)"),

    # ------------------------------------------------------------------ interface actions
    "run_analysis_button": ("Derive the parameters", "Parametreleri üret"),
    "running_analysis": ("Evaluating the correlations…", "Korelasyonlar hesaplanıyor…"),
    "analysis_complete": ("Done.", "Tamamlandı."),
    "report_action": ("Report", "Rapor"),
    "report_running": ("Writing the report…", "Rapor yazılıyor…"),
    "warnings_title": ("Warnings", "Uyarılar"),
    "export_settle": ("→ SlipSurface IQ Settle", "→ SlipSurface IQ Settle"),
    "export_bearing": ("→ SlipSurface IQ Bearing", "→ SlipSurface IQ Bearing"),
    "export_csv": ("Parameters (CSV)", "Parametreler (CSV)"),
    "export_note": ("The parameters of every layer can be sent on as a SlipSurface IQ Settle or SlipSurface IQ "
                    "Bearing project file; open it there and add the foundation.",
                    "Tüm tabakaların parametreleri SlipSurface IQ Settle veya SlipSurface IQ Bearing proje "
                    "dosyası olarak aktarılabilir; dosyayı o programda açıp temeli ekleyin."),

    # ------------------------------------------------------------------ summary cards
    "card_layers": ("Layers", "Tabakalar"),
    "card_spt": ("SPT results", "SPT sonuçları"),
    "card_cpt": ("CPT readings", "CPT okumaları"),
    "card_vs": ("Vs measurements", "Vs ölçümleri"),
    "card_methods": ("Correlations used", "Kullanılan korelasyon"),
    "card_params": ("Parameters derived", "Üretilen parametre"),
    "card_combine": ("Selection", "Seçim"),
    "card_warnings": ("Warnings", "Uyarılar"),
    "card_depth": ("{d:.1f} m deep", "{d:.1f} m derinlik"),
    "card_none": ("none", "yok"),
    "card_ok": ("none", "yok"),

    # ------------------------------------------------------------------ results text
    "res_title": ("SOIL PARAMETERS FROM CORRELATIONS", "KORELASYONLARLA ZEMİN PARAMETRELERİ"),
    "res_site": ("Water table {zw:.2f} m below the ground, γw = {gw:.2f} kN/m³; profile {d:.2f} m "
                 "deep in {n} layer(s).",
                 "Su tablası zeminden {zw:.2f} m derinde, γw = {gw:.2f} kN/m³; {n} tabakalı, "
                 "{d:.2f} m derinliğinde profil."),
    "res_tests": ("Tests: {spt} SPT, {cpt} CPT readings, {vs} Vs measurements.",
                  "Deneyler: {spt} SPT, {cpt} CPT okuması, {vs} Vs ölçümü."),
    "res_spt": ("SPT: ER = {er:.0f} %, CB = {cb:.2f}, CS = {cs:.2f}, CN after {cn}, CN ≤ {cnmax:.2f}.",
                "SPT: ER = %{er:.0f}, CB = {cb:.2f}, CS = {cs:.2f}, CN {cn} ile, CN ≤ {cnmax:.2f}."),
    "res_cpt": ("CPT: a = {a:.2f}, Nkt = {nkt:.1f}, NΔu = {ndu:.1f}.",
                "CPT: a = {a:.2f}, Nkt = {nkt:.1f}, NΔu = {ndu:.1f}."),
    "res_combine": ("Selection: {how}.", "Seçim: {how}."),
    "res_layer": ("Layer {i}: {name} ({behaviour}, {top:.2f} – {bottom:.2f} m, USCS {uscs})",
                  "Tabaka {i}: {name} ({behaviour}, {top:.2f} – {bottom:.2f} m, USCS {uscs})"),
    "res_layer_stress": ("σv0 = {sv:.1f} kPa, u0 = {u0:.1f} kPa, σ'v0 = {se:.1f} kPa at "
                         "mid-depth {z:.2f} m",
                         "Orta derinlik {z:.2f} m'de σv0 = {sv:.1f} kPa, u0 = {u0:.1f} kPa, "
                         "σ'v0 = {se:.1f} kPa"),
    "res_layer_tests": ("{spt} SPT (N60 = {n60}, (N1)60 = {n160}), {cpt} CPT (Ic = {ic}, {zone}), "
                        "{vs} Vs",
                        "{spt} SPT (N60 = {n60}, (N1)60 = {n160}), {cpt} CPT (Ic = {ic}, {zone}), "
                        "{vs} Vs"),
    "res_index": ("LL = {LL}, PL = {PL}, PI = {PI}, w = {w}, LI = {LI}",
                  "LL = {LL}, PL = {PL}, PI = {PI}, w = {w}, LI = {LI}"),
    "res_summary_title": ("SELECTED PARAMETERS", "SEÇİLEN PARAMETRELER"),
    "head_param": ("Parameter", "Parametre"),
    "head_value": ("Value", "Değer"),
    "head_unit": ("Unit", "Birim"),
    "head_method": ("From", "Kaynak"),
    "head_range": ("Range of the correlations", "Korelasyon aralığı"),
    "head_n": ("n", "n"),
    "head_layer": ("Layer", "Tabaka"),
    "head_source": ("Test", "Deney"),
    "head_ref": ("Correlation", "Korelasyon"),
    "head_formula": ("Formula", "Formül"),
    "head_depth": ("z (m)", "z (m)"),
    "head_zone": ("SBT", "ZDT"),

    # ------------------------------------------------------------------ figures
    "fig_profile": ("Soil profile and selected parameters", "Zemin profili ve seçilen parametreler"),
    "fig_spt": ("SPT blow counts with depth", "Derinlikle SPT darbe sayıları"),
    "fig_cpt": ("CPT(u) sounding", "CPT(u) sondajı"),
    "fig_sbt": ("Soil behaviour type chart (Robertson 2009)",
                "Zemin davranış türü abağı (Robertson 2009)"),
    "fig_strength": ("Strength with depth", "Derinlikle dayanım"),
    "fig_stiffness": ("Stiffness with depth", "Derinlikle rijitlik"),
    "fig_state": ("Density and stress history with depth", "Derinlikle sıkılık ve gerilme geçmişi"),
    "fig_plasticity": ("Plasticity chart (Casagrande)", "Plastisite kartı (Casagrande)"),
    "fig_comparison": ("The correlations compared, layer by layer",
                       "Korelasyonların tabaka tabaka karşılaştırması"),
    "ax_depth": ("Depth (m)", "Derinlik (m)"),
    "ax_N": ("Blow count", "Darbe sayısı"),
    "ax_qt": ("qt (MPa)", "qt (MPa)"),
    "ax_fs": ("fs (kPa)", "fs (kPa)"),
    "ax_u": ("u2, u0 (kPa)", "u2, u0 (kPa)"),
    "ax_ic": ("Ic", "Ic"),
    "ax_fr": ("Normalised friction ratio Fr (%)", "Normalize sürtünme oranı Fr (%)"),
    "ax_qtn": ("Normalised cone resistance Qtn", "Normalize uç direnci Qtn"),
    "ax_LL": ("Liquid limit LL (%)", "Likit limit LL (%)"),
    "ax_PI": ("Plasticity index PI (%)", "Plastisite indisi PI (%)"),
    "lg_water": ("Water table", "Su tablası"),
    "lg_selected": ("Selected (layer)", "Seçilen (tabaka)"),
    "lg_measured": ("Measured", "Ölçülen"),
    "lg_a_line": ("A-line", "A-çizgisi"),
    "lg_u_line": ("U-line", "U-çizgisi"),
    "lg_u0": ("u0 (hydrostatic)", "u0 (hidrostatik)"),
    "lg_n": ("N (field)", "N (arazi)"),
    "lg_n60": ("N60", "N60"),
    "lg_n160": ("(N1)60", "(N1)60"),
    "no_data": ("No data for this figure.", "Bu şekil için veri yok."),
}

TRANSLATIONS = {
    "en": {key: pair[0] for key, pair in ENTRIES.items()},
    "tr": {key: pair[1] for key, pair in ENTRIES.items()},
}


def t(lang: str, key: str, **params) -> str:
    """One text in one language, formatted; the key itself if it is unknown."""
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
    return text.format(**params) if params else text


def warning_text(lang: str, warning) -> str:
    """An engine warning, (key, params), as a sentence."""
    key, params = warning
    params = dict(params)
    if "param" in params:          # a parameter key reads as its name
        params["param"] = t(lang, f"param_{params['param']}")
    if "method" in params:         # a correlation key reads as its citation
        from .correlations import reference
        params["method"] = reference(params["method"], lang)
    return t(lang, key, **params)
