#!/bin/bash
# 🔒 Скрипт очистки Git истории от чувствительных данных
# Использует git-filter-repo для безопасного удаления секретов

set -e

echo "🚨 ВНИМАНИЕ: Скрипт очистки Git истории"
echo "Это действие изменит историю репозитория и потребует force push!"
echo ""
read -p "Продолжить? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Операция отменена."
    exit 1
fi

# Проверяем наличие git-filter-repo
if ! command -v git-filter-repo &> /dev/null; then
    echo "❌ git-filter-repo не найден."
    echo "Установите его: pip install git-filter-repo"
    exit 1
fi

# Создаем backup
echo "📦 Создание backup..."
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="backup_${TIMESTAMP}"
mkdir -p "$BACKUP_DIR"
cp -r .git "$BACKUP_DIR/"
echo "✅ Backup создан: $BACKUP_DIR"

# Паттерны для удаления
echo "🔍 Удаление чувствительных данных..."

# 1. Удаляем файлы с секретами
echo "📂 Удаление конфигурационных файлов с секретами..."
git filter-repo --path config.ini --invert-paths --force

# 2. Удаляем строки с webhook
echo "🔗 Удаление строк с webhook URL..."
git filter-repo --replace-text <(echo "https://softway.bitrix24.ru/rest/12/kt17hzrauafyfem0/==>https://your-portal.bitrix24.ru/rest/***/***/") --force

# 3. Удаляем токены
echo "🔑 Удаление токенов..."
git filter-repo --replace-text <(echo "kt17hzrauafyfem0==>***SECRET_TOKEN***") --force

# 4. Удаляем упоминания портала
echo "🏢 Удаление упоминаний реального портала..."
git filter-repo --replace-text <(echo "softway.bitrix24.ru==>your-portal.bitrix24.ru") --force

# 5. Удаляем большие файлы (если есть)
echo "📦 Проверка больших файлов..."
git filter-repo --strip-blobs-bigger-than 1M --force

# Очистка и сжатие
echo "🧹 Очистка и сжатие репозитория..."
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Проверка результата
echo "🔍 Проверка результата очистки..."
if python scripts/security_check.py --quiet; then
    echo "✅ Очистка прошла успешно! Утечки не обнаружены."
else
    echo "⚠️ Найдены потенциальные проблемы. Проверьте отчет."
fi

# Статистика
echo ""
echo "📊 Статистика очистки:"
echo "Размер до: $(du -sh $BACKUP_DIR/.git | cut -f1)"
echo "Размер после: $(du -sh .git | cut -f1)"
echo "Количество коммитов: $(git rev-list --all --count)"
echo ""

echo "🎯 СЛЕДУЮЩИЕ ШАГИ:"
echo "1. Проверьте репозиторий: git log --oneline"
echo "2. Убедитесь что все работает: python run_report.py"
echo "3. Force push в GitHub: git push origin --force --all"
echo "4. Удалите backup: rm -rf $BACKUP_DIR (после проверки)"
echo ""
echo "⚠️ ВАЖНО: Уведомите команду о изменении истории!"
echo "Все должны будут сделать: git clone <repo> (заново)"

echo "✅ Очистка Git истории завершена!"