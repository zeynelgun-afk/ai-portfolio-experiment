#!/usr/bin/env python3
"""sayi_denetimi.py testleri — kaynaksız rakam kapısı.

En önemli test: tur #7'nin gerçek halüsinasyonu (NVDA'ya hafızadan "%80-90 pazar payı")
yakalanmalı. Aynı ölçüde önemlisi, meşru türetilmiş yüzdeler (talimat yüzdeyi tabanıyla
yazmayı zorunlu kılıyor) yanlış yere işaretlenMEmeli.
"""

import os
import sys
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import sayi_denetimi as sd  # noqa: E402

# Gerçek bir iddia prompt'unun veri bloğu (yeniden_degerlendir.iddia_promptu biçimi)
PROMPT = """Zaman (UTC): 2026-09-28T15:00Z
Sembol: MU
TETİKLEYEN VERİ:
  ölçüm: 905.4 · eşik: 941.62
GÜNCEL VERİ:
  fiyat: 905.4 $ (kaynak: seans_ici_5m)
  önceki kapanış: 1082.28 $
  bilanço tarihi: 2026-09-30
  hacim / 20g ortalama: 3.65x
  giriş fiyatı: 892.67 $
  adet: 33.6072
  stop_haftalik_kapanis: 730 $
"""


class AyiklamaTesti(unittest.TestCase):
    def test_nokta_ondalik(self):
        self.assertIn(905.4, [d for _, d in sd.sayilari_ayikla("fiyat 905.4 $")])

    def test_binlik_virgul(self):
        self.assertIn(30428.36, [d for _, d in sd.sayilari_ayikla("tutar 30,428.36 $")])

    def test_binlik_nokta_turkce(self):
        self.assertIn(1082.28, [d for _, d in sd.sayilari_ayikla("fiyat 1.082,28 $")])

    def test_yuzde_ve_isaret(self):
        degerler = [d for _, d in sd.sayilari_ayikla("%+14.9 ve %-16.3")]
        self.assertIn(14.9, degerler)
        self.assertIn(16.3, degerler)

    def test_carpan(self):
        self.assertIn(3.65, [d for _, d in sd.sayilari_ayikla("hacim 3.65x")])

    def test_rakamsiz_metin_bos_doner(self):
        self.assertEqual(sd.sayilari_ayikla("tez rakamsız kuruldu"), [])


class KaynaksizRakamTesti(unittest.TestCase):
    def kontrol(self, cikti, prompt=PROMPT):
        return [ham for ham, _ in sd.kaynaksiz_rakamlar(cikti, prompt)]

    def test_promptta_gecen_rakam_temiz(self):
        self.assertEqual(self.kontrol(
            "Fiyat 905.4 $ ile 941.62 eşiğinin altına indi; stop 730 $."), [])

    def test_turetilmis_yuzde_temiz(self):
        # (905.4 / 941.62 - 1) * 100 = -3.85 — prompt'ta yok ama türetilebilir
        self.assertEqual(self.kontrol(
            "Fiyat 50g eşiğinin %-3.8 altında (905.4 vs 941.62)."), [])

    def test_girise_gore_getiri_temiz(self):
        # (905.4 / 892.67 - 1) * 100 = 1.43
        self.assertEqual(self.kontrol(
            "Girişe göre %+1.4 (giriş 892.67 $, şimdi 905.4 $)."), [])

    def test_stop_mesafesi_temiz(self):
        # (905.4 / 730 - 1) * 100 = 24.03
        self.assertEqual(self.kontrol("Stop mesafesi %+24.0, 730 $ stop'a rahat."), [])

    def test_tur_7_halusinasyonu_yakalanir(self):
        """Gerçek vaka: NVDA tezine hafızadan pazar payı yazıldı."""
        kaynaksiz = self.kontrol(
            "NVDA AI hızlandırıcıda %80-90 pazar payıyla lider konumda.")
        self.assertTrue(kaynaksiz, "pazar payı uydurması yakalanmalıydı")
        self.assertIn("80", kaynaksiz)
        self.assertIn("90", kaynaksiz)

    def test_uydurma_analist_hedefi_yakalanir(self):
        kaynaksiz = self.kontrol("Analist ortalama hedefi 1350 $ seviyesinde.")
        self.assertEqual(kaynaksiz, ["1350"])

    def test_uydurma_fk_orani_yakalanir(self):
        self.assertEqual(self.kontrol("F/K 18.4 ile sektör ortalamasının altında."),
                         ["18.4"])

    def test_sayim_sayilari_serbest(self):
        # "iki turdur", "3 gün", "2 ardışık kontrol" — uydurma oran taşıyamaz
        self.assertEqual(self.kontrol(
            "Bu 3. turdur aynı etiket; 2 ardışık kontrolde teyit edildi."), [])

    def test_promptta_gecen_tarih_temiz(self):
        self.assertEqual(self.kontrol("Bilanço 2026-09-30 tarihinde."), [])

    def test_promptta_gecmeyen_tarih_yakalanir(self):
        kaynaksiz = self.kontrol("Bir sonraki bilanço 2027-03-15 civarında.")
        self.assertTrue(any(h == "2027" for h in kaynaksiz), kaynaksiz)

    def test_ayni_rakam_bir_kez_bildirilir(self):
        kaynaksiz = self.kontrol("Hedef 1350 $, yani 1350 $ seviyesine kadar.")
        self.assertEqual(kaynaksiz, ["1350"])

    def test_birden_fazla_kaynak_birlestirilir(self):
        # ikinci kaynak: iddianın eski metni — oradaki rakamlar da meşru
        self.assertEqual(sd.kaynaksiz_rakamlar(
            "Ortalamanın %+14.9 üzerindeki duruş bozuldu.",
            PROMPT, "25 Eyl kapanışı 1082.28 $ ile ortalamanın %+14.9 üzerinde."), [])

    def test_tolerans_yuvarlamayi_affeder(self):
        # 905.4 → "905.40" ve 3.65 → "3.6" yazımları kabul edilmeli
        self.assertEqual(self.kontrol("Fiyat 905.40 $, hacim 3.6x."), [])


class GeriBeslemeTesti(unittest.TestCase):
    def test_metin_kaynaksiz_rakamlari_sayar(self):
        metin = sd.geri_besleme_metni([("1350", 1350.0), ("18.4", 18.4)])
        self.assertIn("1350", metin)
        self.assertIn("18.4", metin)
        self.assertIn("rakamsız", metin)
        self.assertIn("JSON", metin)


if __name__ == "__main__":
    unittest.main(verbosity=2)
