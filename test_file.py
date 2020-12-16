# Преобразует ответ из кладра в короткий вариант
def replace_answer_fias(data):
    prefixes = {'проезд': 'пр', 'б-р': 'бр'}
    return prefixes.get(data, data)


def test_replace_answer_fias():
    assert replace_answer_fias('д') == 'д'
    assert replace_answer_fias('проезд') == 'пр'
    assert replace_answer_fias('б-р') == 'бр'
    assert replace_answer_fias('ул') == 'ул'
    assert replace_answer_fias('ш') == 'ш'
    assert replace_answer_fias('площадь') == 'площадь'

