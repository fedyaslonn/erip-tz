# Развертывание сервиса

Сервис использует постгрю 16. Данные хранятся в докер volume `pg_data`.

# Команды для запуска сервиса
```bash
git clone https://github.com/fedyaslonn/erip-tz.git
docker compose -f erip-tz/docker-compose.yml up --build 
```

# Дока по эндпоинтам

# /api/exchange/quote
Создает ожидаемую сделку, возвращая id сделки для ее последующего подтверждения.

![img.png](img.png)
![img_1.png](img_1.png)

# /api/exchange/confirm
Апрувает сделку или реджектит.

![img_2.png](img_2.png)
![img_3.png](img_3.png)

# /api/exchange/pending
Получить список сделок в ожидании.

![img_4.png](img_4.png)

# /api/exchange/stats
Просмотреть статистику по сделкам (за какой-то период)

![img_5.png](img_5.png)
