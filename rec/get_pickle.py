import os
import cv2
import numpy as np
import pickle
import sys
import django
from mtcnn import MTCNN
from insightface.model_zoo.arcface_onnx import ArcFaceONNX
from insightface.app.common import Face

project_home = '/home/user/PycharmProjects/office_rec/officerec'
if project_home not in sys.path:
    sys.path.append(project_home)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Конфигурация путей
PERSONS_PATH = 'user'  # папка с пользователями
PICKLE_PATH = 'user_bd'  # папка для хранения pickle файла
MODEL_PATH = 'arcfaceresnet100-11-int8.onnx'

# Инициализация моделей
get_embd = ArcFaceONNX(model_file=MODEL_PATH)
detector = MTCNN()


def get_face_encoding(image):
    """Получение эмбеддинга лица из изображения"""
    result = detector.detect_faces(image)
    if not result:
        return None

    kps = result[0]['keypoints']
    arr = np.array(list(kps.values()))
    face = Face(d={'kps': arr})

    return get_embd.get(image, face)


def is_similar_face(face_enc1, face_enc2, threshold=0.9):
    """Проверка схожести двух лиц"""
    cosine_sim = np.dot(face_enc1, face_enc2) / (np.linalg.norm(face_enc1) * np.linalg.norm(face_enc2))
    return cosine_sim > threshold


def process_person_images(person_path):
    """Обработка изображений одного человека"""
    known_encodings = []
    images = os.listdir(person_path)

    for image_name in images:
        img_path = os.path.join(person_path, image_name)
        img = cv2.imread(img_path)
        face_enc = get_face_encoding(img)

        if face_enc is None:
            continue

        if not known_encodings:
            known_encodings.append(face_enc)
            continue

        # Проверяем схожесть с существующими энкодингами
        is_new = True
        for known_enc in known_encodings:
            if is_similar_face(face_enc, known_enc):
                is_new = False
                break

        if is_new:
            known_encodings.append(face_enc)

    return known_encodings


def train_model():
    """Обучение модели распознавания лиц"""
    # Получаем список пользователей, исключая системные файлы
    names_arr = [name for name in os.listdir(PERSONS_PATH)
                 if not name.endswith('.ipynb_checkpoints')]
    print(f"Найдены пользователи: {names_arr}")

    # Создаем словарь для хранения энкодингов
    data = {}

    # Обрабатываем каждого пользователя
    for name in names_arr:
        person_path = os.path.join(PERSONS_PATH, name)
        data[name] = process_person_images(person_path)
        print(f'Пользователь {name} добавлен')

    # Сохраняем результаты
    pickle_file = os.path.join(PICKLE_PATH, 'faces_encodings.pickle')
    with open(pickle_file, 'wb') as file:
        pickle.dump(data, file)

    return 'Модель обучена'
