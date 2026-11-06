# Развертывание сервиса

Сервис использует постгрю 16. Данные хранятся в докер volume `pg_data`.

# Команды для запуска сервиса
```bash
git clone https://github.com/fedyaslonn/erip-tz.git
docker compose -f erip-tz/docker-compose.yml up --build 
```
