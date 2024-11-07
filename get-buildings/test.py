import time
import httpx

url = "https://pkk.rosreestr.ru/api/features/1/25:33:180113:10724"

for attempt in range(5):
    try:
        response = httpx.get(url, verify=False)
        if response.status_code == 200:
            data = response.json()
            print(data)
            break
    except httpx.RequestError as e:
        print(f"Попытка {attempt+1}: {e}")
        time.sleep(5)  # Задержка в 5 секунд перед повторной попыткой