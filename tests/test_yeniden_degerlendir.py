#!/usr/bin/env python3
"""yeniden_degerlendir.py testleri — LLM çağrısı taklit edilir, ağ yok.

En kritik test: model bozuk çıktı verdiğinde iddia METNİ DEĞİŞMEMELİ. Yarım
anlaşılmış bir çıktıyla tezi yeniden yazmak, bayat yorumdan daha kötüdür.
"""

import os
import sys
import unittest
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import yeniden_degerlendir as yd  # noqa: E402

AN = datetime(2026, 9, 28, 15, 0, tzinfo=timezone.utc)
ESKI_METIN = "HBM talebi fiyatı 941.62 üstünde tutuyor."


def tezler():
    return {"MU": {"tez_ozeti": "Bellek süper döngüsü", "iddialar": [
        {"id": "MU-1", "metin": ESKI_METIN, "durum": "gecerli",
         "kosullar": [{"tip": "fiyat_alti", "deger": 941.62, "siddet": "iddia"}],
         "son_guncelleme": "2026-09-26T00:00Z", "tetikleyici": None}]}}


def ihlaller(siddet="iddia"):
    return {
        "seans_ici": True,
        "veri": {"MU": {"fiyat": 905.40, "onceki_kapanis": 1082.28,
                        "veri_kaynagi": "seans_ici_5m", "bilanco_tarihi": "2026-09-30"}},
        "tetiklenen": [{"sembol": "MU", "iddia_id": "MU-1", "siddet": siddet,
                        "kosul_tipi": "fiyat_alti", "olcum": 905.40, "esik": 941.62,
                        "tetikleyici": "fiyat 905.40", "cooldown_anahtari": "MU-1"}],
    }


PF = {"nakit_usd": 16421.0, "pozisyonlar": [
    {"sembol": "MU", "adet": 33.6072, "giris_fiyati": 892.67, "maliyet_usd": 30000.0,
     "stop_haftalik_kapanis": 730, "sonraki_bilanco": "2026-09-30"}]}


class JsonAyiklamaTesti(unittest.TestCase):
    def test_duz_json(self):
        self.assertEqual(yd.json_ayikla('{"durum": "gecerli"}'), {"durum": "gecerli"})

    def test_kod_blogu_icindeki_json(self):
        self.assertEqual(
            yd.json_ayikla('```json\n{"durum": "zayifladi"}\n```'),
            {"durum": "zayifladi"})

    def test_aciklama_ile_sarilmis_json(self):
        ham = 'Elbette, işte değerlendirme:\n{"durum": "gecersiz"}\nUmarım yardımcı olur.'
        self.assertEqual(yd.json_ayikla(ham), {"durum": "gecersiz"})

    def test_parse_edilemeyen_girdiler_none_doner(self):
        for bozuk in (None, "", "JSON yok", "{bozuk:", "```json\n{yarim\n```"):
            self.assertIsNone(yd.json_ayikla(bozuk), repr(bozuk))


class ButceTesti(unittest.TestCase):
    def test_yeni_hafta_sayaci_sifirlar(self):
        yol = os.path.join(BASE, "yok", "llm_sayac.json")
        sayac, sinir = yd.butce_durumu(yol, AN)
        self.assertEqual(sayac, {"hafta": yd.hafta_etiketi(AN), "cagri": 0})
        self.assertEqual(sinir, yd.VARSAYILAN_BUTCE)

    def test_env_sinirini_okur_ve_striplenir(self):
        os.environ["MAX_LLM_CAGRI_HAFTA"] = "  25 \n"
        try:
            _, sinir = yd.butce_durumu("/yok/llm_sayac.json", AN)
        finally:
            del os.environ["MAX_LLM_CAGRI_HAFTA"]
        self.assertEqual(sinir, 25)

    def test_bozuk_env_varsayilana_duser(self):
        os.environ["MAX_LLM_CAGRI_HAFTA"] = "altmış"
        try:
            _, sinir = yd.butce_durumu("/yok/llm_sayac.json", AN)
        finally:
            del os.environ["MAX_LLM_CAGRI_HAFTA"]
        self.assertEqual(sinir, yd.VARSAYILAN_BUTCE)


class Kod10Testi(unittest.TestCase):
    def setUp(self):
        self._gercek = yd.llm_cagir

    def tearDown(self):
        yd.llm_cagir = self._gercek

    def kos(self, yanit, t=None, tam=False, sayac=None):
        yd.llm_cagir = lambda *a, **k: yanit
        t = t if t is not None else tezler()
        sayac = sayac or {"hafta": "2026-W40", "cagri": 0}
        guncellenen, sayac = yd.kod10_akisi(t, ihlaller(), PF, AN, "test-model",
                                           "anahtar", sayac, 60, False, tam)
        return t["MU"]["iddialar"][0], guncellenen, sayac

    def test_gecerli_cikti_iddiayi_yeniden_yazar(self):
        iddia, guncellenen, sayac = self.kos(
            '{"metin": "Fiyat 905.40 ile 50g ortalamanın altına sarktı.",'
            ' "durum": "zayifladi"}')
        self.assertEqual(guncellenen, ["MU-1"])
        self.assertEqual(iddia["durum"], "zayifladi")
        self.assertIn("905.40", iddia["metin"])
        self.assertEqual(iddia["son_guncelleme"], yd.iso(AN))
        self.assertIn("tetikleyici: fiyat 905.40", iddia["tetikleyici"])
        self.assertEqual(sayac["cagri"], 1)

    def test_bozuk_json_iddia_metnini_degistirmez(self):
        iddia, guncellenen, _ = self.kos("model saçmaladı, JSON yok")
        self.assertEqual(iddia["metin"], ESKI_METIN)
        self.assertEqual(iddia["durum"], "degerlendirilemedi")
        self.assertEqual(guncellenen, ["MU-1"])

    def test_gecersiz_durum_degeri_reddedilir(self):
        iddia, _, _ = self.kos('{"metin": "yeni metin", "durum": "harika"}')
        self.assertEqual(iddia["metin"], ESKI_METIN)
        self.assertEqual(iddia["durum"], "degerlendirilemedi")

    def test_bos_metin_reddedilir(self):
        iddia, _, _ = self.kos('{"metin": "   ", "durum": "gecerli"}')
        self.assertEqual(iddia["metin"], ESKI_METIN)
        self.assertEqual(iddia["durum"], "degerlendirilemedi")

    def test_butce_dolunca_cagri_yapilmaz(self):
        iddia, guncellenen, _ = self.kos(
            '{"metin": "yeni", "durum": "gecerli"}',
            sayac={"hafta": "2026-W40", "cagri": 60})
        self.assertEqual(guncellenen, [])
        self.assertEqual(iddia["metin"], ESKI_METIN)

    def test_tam_yenileme_tetiklenmeyen_iddiayi_da_kapsar(self):
        t = tezler()
        t["MU"]["iddialar"].append({
            "id": "MU-2", "metin": "ikinci iddia", "durum": "gecerli",
            "kosullar": [], "son_guncelleme": None, "tetikleyici": None})
        yd.llm_cagir = lambda *a, **k: '{"metin": "tazelendi", "durum": "gecerli"}'
        guncellenen, _ = yd.kod10_akisi(t, ihlaller(), PF, AN, "m", "a",
                                        {"hafta": "x", "cagri": 0}, 60, False, True)
        self.assertEqual(sorted(guncellenen), ["MU-1", "MU-2"])

    def test_tam_yenileme_disinda_sadece_tetiklenen_islenir(self):
        t = tezler()
        t["MU"]["iddialar"].append({
            "id": "MU-2", "metin": "ikinci iddia", "durum": "gecerli",
            "kosullar": [], "son_guncelleme": None, "tetikleyici": None})
        yd.llm_cagir = lambda *a, **k: '{"metin": "tazelendi", "durum": "gecerli"}'
        guncellenen, _ = yd.kod10_akisi(t, ihlaller(), PF, AN, "m", "a",
                                        {"hafta": "x", "cagri": 0}, 60, False, False)
        self.assertEqual(guncellenen, ["MU-1"])
        self.assertEqual(t["MU"]["iddialar"][1]["metin"], "ikinci iddia")


class Kod20Testi(unittest.TestCase):
    def setUp(self):
        self._gercek = yd.llm_cagir
        self.gecici = os.path.join(BASE, "tests", "_gecici")
        os.makedirs(self.gecici, exist_ok=True)
        self.notlar = os.path.join(self.gecici, "bekleyen_notlar.md")
        self.karar = os.path.join(self.gecici, "bekleyen_karar.json")
        for y in (self.notlar, self.karar):
            if os.path.exists(y):
                os.remove(y)

    def tearDown(self):
        yd.llm_cagir = self._gercek
        for y in (self.notlar, self.karar):
            if os.path.exists(y):
                os.remove(y)
        os.rmdir(self.gecici)

    def kos(self, yanit, t=None):
        yd.llm_cagir = lambda *a, **k: yanit
        t = t if t is not None else tezler()
        kararlar, sayac = yd.kod20_akisi(t, ihlaller("tez"), PF, AN, "derin-model",
                                         "anahtar", {"hafta": "x", "cagri": 0},
                                         False, self.notlar, self.karar)
        return t, kararlar, sayac

    def test_tez_degerlendirmesi_karar_uretir_ve_not_yazar(self):
        t, kararlar, _ = self.kos(
            '{"tez_degerlendirmesi": "50g kaybedildi, tez zayıfladı.",'
            ' "yeni_tez_ozeti": "Süper döngü tezi 50g altında sorgulanıyor.",'
            ' "iddia_durumlari": {"MU-1": "zayifladi"},'
            ' "karar": {"islem": "KIRP", "adet": 8.5, "tutar_usd": null,'
            ' "yeni_stop": 820, "gerekce": "50g kaybı", "carpitma_isareti": "941 üstü"},'
            ' "cumartesi_notu": "Bilanço sonrası yeniden bak."}')
        self.assertEqual(len(kararlar), 1)
        self.assertEqual(kararlar[0]["islem"], "KIRP")
        self.assertEqual(kararlar[0]["adet"], 8.5)
        self.assertEqual(t["MU"]["iddialar"][0]["durum"], "zayifladi")
        self.assertIn("50g altında", t["MU"]["tez_ozeti"])
        self.assertTrue(os.path.exists(self.karar))
        with open(self.notlar, encoding="utf-8") as f:
            notlar = f.read()
        self.assertIn("TEZ SEVİYESİ", notlar)
        self.assertIn("Bilanço sonrası yeniden bak", notlar)

    def test_tut_karari_da_kayda_gecer(self):
        _, kararlar, _ = self.kos(
            '{"tez_degerlendirmesi": "Tez ayakta.", "iddia_durumlari": {},'
            ' "karar": {"islem": "TUT", "adet": null, "tutar_usd": null,'
            ' "gerekce": "stop çok uzak", "carpitma_isareti": "800 altı"}}')
        self.assertEqual(kararlar[0]["islem"], "TUT")

    def test_gecersiz_islem_karar_uretmez_ama_not_yazilir(self):
        t, kararlar, _ = self.kos(
            '{"tez_degerlendirmesi": "Belirsiz.", "iddia_durumlari": {"MU-1": "zayifladi"},'
            ' "karar": {"islem": "SAVUR", "gerekce": "?"}}')
        self.assertEqual(kararlar, [])
        self.assertEqual(t["MU"]["iddialar"][0]["durum"], "zayifladi")
        self.assertTrue(os.path.exists(self.notlar))
        self.assertFalse(os.path.exists(self.karar))

    def test_bozuk_cikti_iddiayi_degistirmez_ve_notu_isaretler(self):
        t, kararlar, _ = self.kos("JSON değil bu")
        iddia = t["MU"]["iddialar"][0]
        self.assertEqual(kararlar, [])
        self.assertEqual(iddia["metin"], ESKI_METIN)
        self.assertEqual(iddia["durum"], "degerlendirilemedi")
        with open(self.notlar, encoding="utf-8") as f:
            self.assertIn("DEĞERLENDİRİLEMEDİ", f.read())

    def test_tez_seviyesi_tetikleyici_yoksa_hicbir_sey_yapmaz(self):
        yd.llm_cagir = lambda *a, **k: "çağrılmamalıydı"
        t = tezler()
        kararlar, _ = yd.kod20_akisi(t, ihlaller("iddia"), PF, AN, "m", "a",
                                     {"hafta": "x", "cagri": 0}, False,
                                     self.notlar, self.karar)
        self.assertEqual(kararlar, [])
        self.assertEqual(t["MU"]["iddialar"][0]["metin"], ESKI_METIN)


class PromptTesti(unittest.TestCase):
    def test_iddia_promptu_veriyi_ve_tetikleyiciyi_icerir(self):
        t = tezler()
        p = yd.iddia_promptu("MU", t["MU"], t["MU"]["iddialar"][0],
                            ihlaller()["tetiklenen"][0], ihlaller()["veri"],
                            PF["pozisyonlar"][0], AN)
        for beklenen in ("905.4", "941.62", "seans_ici_5m", "MU-1", "730"):
            self.assertIn(str(beklenen), p)

    def test_tez_promptu_nakit_sinirini_yazar(self):
        t = tezler()
        p = yd.tez_promptu("MU", t["MU"], ihlaller("tez")["tetiklenen"],
                          ihlaller()["veri"], PF["pozisyonlar"][0], PF["nakit_usd"], AN)
        self.assertIn("NAKİT: 16421.0", p)
        self.assertIn("tutar_usd bunu aşamaz", p)

    def test_sistem_promptlari_rakam_uydurmayi_yasaklar(self):
        for sistem in (yd.SISTEM_IDDIA, yd.SISTEM_TEZ):
            self.assertIn("RAKAM UYDURMA", sistem)


if __name__ == "__main__":
    unittest.main(verbosity=2)
