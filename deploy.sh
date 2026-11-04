#!/bin/sh
# Поэтапное обновление трех реплик приложения.
set -eu

: "${APP_IMAGE:?Укажите APP_IMAGE с тегом нового образа}"
export APP_IMAGE

OLD_FILE=$(mktemp)
NEW_FILE=$(mktemp)
trap 'rm -f "$OLD_FILE" "$NEW_FILE"' EXIT

docker compose ps -q app > "$OLD_FILE"

OLD_COUNT=$(wc -l < "$OLD_FILE")

if [ "$OLD_COUNT" -ne 3 ]; then
    echo "Ошибка: ожидались 3 работающие старые реплики, найдено $OLD_COUNT"
    exit 1
fi

echo "==> Новая версия: $APP_IMAGE"
echo "==> Запускаем три новые реплики, не трогая старые"

docker compose up -d \
    --no-deps \
    --no-recreate \
    --no-build \
    --pull never \
    --scale app=6 app

docker compose ps -q app | grep -Fvx -f "$OLD_FILE" > "$NEW_FILE" || true

NEW_COUNT=$(wc -l < "$NEW_FILE")

if [ "$NEW_COUNT" -ne 3 ]; then
    echo "Ошибка: создано $NEW_COUNT новых реплик вместо 3"
    echo "Старые реплики не остановлены"
    exit 1
fi

echo "==> Проверяем новые реплики"

while IFS= read -r container; do
    actual_image=$(docker inspect -f '{{.Config.Image}}' "$container")

    if [ "$actual_image" != "$APP_IMAGE" ]; then
        echo "Ошибка: реплика использует неверный образ"
        docker rm -f $(cat "$NEW_FILE") >/dev/null
        exit 1
    fi

    attempt=0

    while [ "$(docker inspect -f '{{.State.Health.Status}}' "$container")" != "healthy" ]; do
        attempt=$((attempt + 1))

        if [ "$attempt" -ge 60 ]; then
            echo "Новая реплика не прошла healthcheck"
            echo "Оставляем старую версию"
            docker rm -f $(cat "$NEW_FILE") >/dev/null
            exit 1
        fi

        sleep 1
    done

    echo "Новая реплика готова: $(echo "$container" | cut -c1-12)"
done < "$NEW_FILE"

echo "==> Новые реплики здоровы. Убираем старые"

while IFS= read -r container; do
    docker stop "$container" >/dev/null
    docker rm "$container" >/dev/null
    echo "Старая реплика удалена: $(echo "$container" | cut -c1-12)"
    sleep 2
done < "$OLD_FILE"

echo "==> Обновление завершено: $APP_IMAGE"
