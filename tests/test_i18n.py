from fratelanza.core.i18n import Localizer, normalize_locale


def test_localizer_loads_arabic_and_marks_rtl() -> None:
    localizer = Localizer("ar")

    assert localizer.locale.is_rtl
    assert localizer.gettext("module.sales.title") == "المبيعات"


def test_unknown_locale_falls_back_to_english() -> None:
    assert normalize_locale("fr") == "en"
    assert Localizer("fr").gettext("module.sales.title") == "Sales"
