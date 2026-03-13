/**
 * Пользовательские JavaScript функции для ROI Marketing Dashboard
 * Проверка наличия статических файлов в CI/CD
 */

// Функция для форматирования чисел с разделителями
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

// Функция для обновления времени последнего обновления
function updateLastUpdateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });

    const element = document.getElementById('last-update-time');
    if (element) {
        element.textContent = `Последнее обновление: ${timeString}`;
    }
}

// Автоматическое обновление каждую минуту
setInterval(updateLastUpdateTime, 60000);

// Анимация для карточек метрик при загрузке
document.addEventListener('DOMContentLoaded', function() {
    console.log('ROI Marketing Dashboard загружен');
    updateLastUpdateTime();

    // Добавляем класс для анимации появления
    const cards = document.querySelectorAll('.metric-card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
});

// Обработка ошибок графов
function handleGraphError(error) {
    console.error('Ошибка загрузки графика:', error);
    const container = document.getElementById('error-container');
    if (container) {
        container.innerHTML = `
            <div class="alert alert-danger">
                <strong>Ошибка!</strong> Не удалось загрузить данные для графика.
                Пожалуйста, обновите страницу или попробуйте позже.
            </div>
        `;
    }
}

// Экспорт данных в CSV
function exportToCSV(data, filename) {
    const csv = data.map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}