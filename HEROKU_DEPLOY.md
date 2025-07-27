# Cosmolabs Backend - Heroku Deployment Guide

## Подготовка к деплою

Ваш Django проект готов к деплою на Heroku! Все необходимые файлы созданы.

## Шаги для деплоя:

### 1. Установите Heroku CLI
Скачайте и установите [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)

### 2. Войдите в Heroku
```bash
heroku login
```

### 3. Создайте Heroku приложение
```bash
heroku create your-app-name
```

### 4. Установите переменные окружения
```bash
heroku config:set SECRET_KEY="your-secret-key-here"
heroku config:set DEBUG=False
heroku config:set GEMINI_API_KEY="your-gemini-api-key"
```

### 5. Инициализируйте Git (если еще не сделано)
```bash
git init
git add .
git commit -m "Initial commit for Heroku deployment"
```

### 6. Добавьте Heroku remote
```bash
heroku git:remote -a your-app-name
```

### 7. Деплой на Heroku
```bash
git push heroku main
```

### 8. Запустите миграции (если нужно)
```bash
heroku run python manage.py migrate
```

### 9. Создайте суперпользователя (опционально)
```bash
heroku run python manage.py createsuperuser
```

## Важные заметки:

1. **Безопасность**: Убедитесь, что файл `.env` не попадает в Git
2. **CORS**: Настроен для разрешения всех доменов (CORS_ALLOW_ALL_ORIGINS = True)
3. **Статические файлы**: Используется WhiteNoise для обслуживания статических файлов
4. **База данных**: Используется SQLite (файл db.sqlite3)
5. **ML модели**: Большие модели добавлены в .gitignore - загрузите их отдельно если нужно

## Структура файлов для деплоя:

- `Procfile` - команды для запуска приложения
- `runtime.txt` - версия Python
- `requirements.txt` - зависимости Python
- `app.json` - конфигурация Heroku приложения
- `release-tasks.sh` - задачи релиза (миграции, статические файлы)
- `.gitignore` - файлы для исключения из Git

## Мониторинг:

Просмотр логов:
```bash
heroku logs --tail
```

Проверка статуса:
```bash
heroku ps
```

## Обновления:

Для обновления приложения:
```bash
git add .
git commit -m "Update description"
git push heroku main
```

Ваше приложение будет доступно по адресу: `https://your-app-name.herokuapp.com`