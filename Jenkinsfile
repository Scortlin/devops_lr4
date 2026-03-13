pipeline {
    agent any

    environment {
        APP_IMAGE = "my-roi-app"
        BUILD_NUMBER = "${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                echo '📦 Клонирование репозитория...'
                checkout scm
            }
        }

        stage('Linting') {
            steps {
                echo '🔍 Проверка стиля кода Python...'
                sh """
                    # Создать виртуальное окружение
                    python3 -m venv venv
                    # Активировать и установить pylint
                    . venv/bin/activate
                    pip install pylint
                    # Запустить проверку
                    pylint --fail-under=5.0 app/*.py || echo "⚠️  Есть замечания, но продолжаем"
                    # Деактивировать
                    deactivate
                """
            }
        }

        stage('Build Image') {
            steps {
                echo '🏗️  Сборка Docker образа...'
                sh """
                    cd app
                    docker build -t ${APP_IMAGE}:${BUILD_NUMBER} .
                    docker tag ${APP_IMAGE}:${BUILD_NUMBER} ${APP_IMAGE}:latest
                """
            }
        }

        // Quality Gate: Проверка наличия статических файлов (ТЗ)
        stage('Check Static Assets') {
            steps {
                echo '🔍 Проверка статических файлов (CSS/JS)...'
                sh """
                    # Проверяем наличие CSS файла
                    docker run --rm ${APP_IMAGE}:${BUILD_NUMBER} sh -c "test -f assets/style.css && echo '✅ style.css найден' || (echo '❌ style.css НЕ НАЙДЕН' && exit 1)"

                    # Проверяем наличие JS файла
                    docker run --rm ${APP_IMAGE}:${BUILD_NUMBER} sh -c "test -f assets/custom.js && echo '✅ custom.js найден' || (echo '❌ custom.js НЕ НАЙДЕН' && exit 1)"

                    # Проверяем, что файлы не пустые (опционально)
                    CSS_SIZE=\$(docker run --rm ${APP_IMAGE}:${BUILD_NUMBER} sh -c "wc -c < app/assets/style.css 2>/dev/null || echo 0")
                    JS_SIZE=\$(docker run --rm ${APP_IMAGE}:${BUILD_NUMBER} sh -c "wc -c < app/assets/custom.js 2>/dev/null || echo 0")

                    echo "📊 Размер style.css: \$CSS_SIZE байт"
                    echo "📊 Размер custom.js: \$JS_SIZE байт"

                    if [ \$CSS_SIZE -eq 0 ] || [ \$JS_SIZE -eq 0 ]; then
                        echo "❌ Один из файлов пуст"
                        exit 1
                    fi
                """
            }
        }

        stage('Test Run') {
            steps {
                echo '🧪 Тестовый запуск контейнера...'
                script {
                    try {
                        // Запускаем контейнер в фоне
                        sh """
                            docker run -d --name test-${BUILD_NUMBER} \
                                -p 8051:8050 \
                                ${APP_IMAGE}:${BUILD_NUMBER}
                        """

                        // Ждем 15 секунд для инициализации
                        sleep(15)

                        // Проверяем, что контейнер работает
                        sh 'docker ps | grep test-' + BUILD_NUMBER

                        echo "✅ Тестовый запуск успешен"
                    } catch (Exception e) {
                        echo "❌ Ошибка при тестовом запуске: ${e}"
                        // Сохраняем логи для диагностики
                        sh 'docker logs test-' + BUILD_NUMBER
                        error("Тестовый запуск не удался")
                    } finally {
                        // Останавливаем и удаляем тестовый контейнер
                        sh 'docker stop test-' + BUILD_NUMBER || true
                        sh 'docker rm test-' + BUILD_NUMBER || true
                    }
                }
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                echo '🚀 Деплой обновленной версии...'
                script {
                    // Останавливаем старый контейнер
                    sh 'docker stop roi-app || true'
                    sh 'docker rm roi-app || true'

                    // Запускаем новый контейнер
                    sh """
                        docker run -d --name roi-app \
                            -p 8050:8050 \
                            --restart unless-stopped \
                            ${APP_IMAGE}:${BUILD_NUMBER}
                    """

                    echo "✅ Приложение доступно на http://localhost:8050"
                }
            }
        }
    }

    post {
        success {
            echo '✅ Pipeline успешно выполнен!'
        }
        failure {
            echo '❌ Pipeline завершился с ошибкой!'
        }
        always {
            echo '🏁 Очистка временных ресурсов...'
            sh 'docker system prune -f || true'
        }
    }

}



