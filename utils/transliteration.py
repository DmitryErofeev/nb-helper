from transliterate import get_available_language_codes, translit, slugify
from transliterate.base import TranslitLanguagePack, registry
from functools import lru_cache


class Gost2006RuLangPack(TranslitLanguagePack):
    """Russian language pack like GOST R 52535.1-2006 for NetBox.
    """
    language_code = "ru-gost"
    language_name = "Russian like GOST R 52535.1-2006"
    mapping = (
        u"abvgdeeziiklmnoprstufhcyeABVGDEEZIIKLMNOPRSTUFHCYE",
        u"абвгдеёзийклмнопрстуфхцыэАБВГДЕЁЗИЙКЛМНОПРСТУФХЦЫЭ",
    )

    reversed_specific_mapping = (
        u"еЕёЁэЭиИйЙ",
        u"eEeEeEiIiI"
    )

    pre_processor_mapping = {
        u"zh": u"ж",
        # u"kh": u"х",
        # u"tc": u"ц",
        u"ch": u"ч",
        u"sh": u"ш",
        u"shch": u"щ",
        # u"iu": u"ю",
        # u"ia": u"я",
        u"yu": u"ю",
        u"ya": u"я",
        u"Zh": u"Ж",
        # u"Kh": u"Х",
        # u"Tc": u"Ц",
        u"Ch": u"Ч",
        u"Sh": u"Ш",
        u"Shch": u"Щ",
        # u"Iu": u"Ю",
        # u"Ia": u"Я",
        u"Yu": u"Ю",
        u"Ya": u"Я",
    }

    reversed_specific_pre_processor_mapping = {
        u"ъ": u"",
        u"ь": u"",
        u"Ъ": u"",
        u"Ь": u""
    }


registry.register(Gost2006RuLangPack, force=True)

LANG_PADDING = max([len(lang) for lang in get_available_language_codes()])


@lru_cache
def transliterate(text, lang='ru-gost', reversed=True):
    trans = translit(text, lang, reversed)
    print(f"translit[{lang:{LANG_PADDING}}]: {text} => {trans}")

    if trans.isascii():
        return trans
    else:
        for i in trans:
            if not i.isascii():
                print(i, i.isascii())
        raise ValueError(f"Incorrect transliteration table for '{lang}' language")


if __name__ == "__main__":
    print("get_available_language_codes:", get_available_language_codes())

    text = '40 лет Октября, 1 Maya 34.2'
    test_text = 'Съешь ещё этих мягких французских булок, да выпей же чаю.'

    print(f"slugify: {text} => {slugify(text)}")
    # print(f"slugify:", " => ".join([test_text, slugify(test_text)]))

    result = [transliterate(test_text, lang) for lang in get_available_language_codes()]
    result = [transliterate(test_text.lower(), lang) for lang in get_available_language_codes()]
    result = [transliterate(test_text.upper(), lang) for lang in get_available_language_codes()]
    print()

    trans_list = [
        'Электродный',
        'Коммунистическая',
        'Текстильщиков',
        '40 лет Октября',
        'Егорьевская',
        'Дзержинского',
        'Барышникова',
        'Совхозная',
        'Строителей 1-й',
        'Юбилейный',
        'Красноармейский',
        'Центральный'
        ]

    result = [transliterate(addr, 'ru') for addr in trans_list]
    print(result)

    # result = [transliterate(addr, 'example', reversed=False) for addr in trans_list]
    # print()

    result = [transliterate(addr) for addr in trans_list]
    print()
