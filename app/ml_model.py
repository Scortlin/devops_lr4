import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib
import os
import time


class ROIPredictor:
    """Класс для загрузки и использования ML-модели прогнозирования ROI"""

    def __init__(self, model_path='roi_model.pkl'):
        self.model_path = model_path
        self.model = None
        self.is_loaded = False

    def train_dummy_model(self):
        """Создание демо-модели для примера"""
        print("[ML] Создание демо-модели...")
        np.random.seed(42)
        X = np.random.rand(1000, 5)  # spend, impressions, clicks, channel_encoded, region_encoded
        y = X[:, 0] * 2.5 + np.random.randn(1000) * 0.1  # ROI ~ spend * 2.5

        model = RandomForestRegressor(n_estimators=10, max_depth=5)
        model.fit(X, y)

        # Сохраняем модель
        joblib.dump(model, self.model_path)
        print(f"[ML] Демо-модель сохранена в {self.model_path}")

        # ВАЖНО: Небольшая пауза, чтобы файл точно записался
        time.sleep(1)

        return model

    def load_model(self):
        """Загрузка модели с диска (имитация длительной загрузки)"""
        print("[ML] Начало загрузки модели в память...")
        time.sleep(25)  # Имитация загрузки большой модели

        # Проверяем, существует ли файл модели
        if not os.path.exists(self.model_path):
            print(f"[ML] Модель {self.model_path} не найдена, создаем новую")
            self.model = self.train_dummy_model()
        else:
            try:
                # Проверяем, что файл не пустой
                if os.path.getsize(self.model_path) == 0:
                    print("[ML] Файл модели пустой, создаем новую модель")
                    self.model = self.train_dummy_model()
                else:
                    # Пытаемся загрузить модель
                    self.model = joblib.load(self.model_path)
                    print("[ML] Модель успешно загружена из файла!")
            except EOFError:
                print("[ML] Файл модели поврежден, создаем новую модель")
                self.model = self.train_dummy_model()
            except Exception as e:
                print(f"[ML] Ошибка при загрузке модели: {e}, создаем новую")
                self.model = self.train_dummy_model()

        self.is_loaded = True
        print("[ML] Модель готова к использованию!")

    def predict_roi(self, features):
        """Прогнозирование ROI на основе входных признаков"""
        if not self.is_loaded:
            raise RuntimeError("Модель не загружена!")
        return self.model.predict(features)

    def is_model_ready(self):
        """Проверка готовности модели"""
        return self.is_loaded

roi_predictor = ROIPredictor()