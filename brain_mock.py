import datetime

JOKES = [
    "Сэр, я бы пошутил про нейросети, но у меня нет веских аргументов — только веса.",
    "Программист ставит на ночь два стакана: полный — если захочет пить, пустой — если не захочет.",
    "Мой любимый вид отдыха — выключить и включить заново.",
]

def smalltalk(topic):
    hour = datetime.datetime.now().hour
    if topic == "greeting":
        if hour < 6: return "Доброй ночи, сэр."
        if hour < 12: return "Доброе утро, сэр."
        if hour < 18: return "Добрый день, сэр."
        return "Добрый вечер, сэр."
    if topic == "how_are_you":
        return "Все системы в норме, сэр. Готов к работе."
    if topic == "joke":
        import random
        return random.choice(JOKES)
    return None
