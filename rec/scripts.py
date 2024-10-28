import datetime
import os
import sys
import django
from insightface.app.common import Face
from insightface.model_zoo import model_zoo
from .class_load_rtsp import LoadStreams
import cv2
import time
import pickle
import logging
import numpy as np

from django.apps import apps

project_home = '/home/user/PycharmProjects/office_rec/officerec'
if project_home not in sys.path:
    sys.path.append(project_home)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

Facerec_model = apps.get_model('rec', 'Facerec')
def draw_bounding_box(image, bbox):
    x, y, w, h = bbox.astype(int)
    cv2.rectangle(image, (x, y), (w, h), (0, 255, 0), 2)
def face_lets_go():
    #Facerec_model = apps.get_model('rec', 'Facerec')

    logging.basicConfig(level=logging.INFO, filename='face.log', filemode='w', \
                        format='%(asctime)s %(levelname)s %(message)s')
    models = {}
    sources = {
        'camera1': 'url_cam1',
        'camera2': 'url_cam2'
    }
    onnx_file = './det_10g.onnx'
    onnx_file1 = './w600k_r50.onnx'
    time_in = None
    database = pickle.loads(open('./face_embeddings.pickle', 'rb').read())
    last_recognition_time = {key: None for key in database}
    # onnx_file = 'buffalo_l/det_10g.onnx'
    # onnx_file1 = 'buffalo_l/w600k_r50.onnx'
    model = model_zoo.get_model(onnx_file)
    model1 = model_zoo.get_model(onnx_file1)
    #start_time = time.time()
    model1.prepare(ctx_id=0)
    #det_size = (640, 640)
    models[model.taskname] = model
    det_model = models['detection']
    det_model.prepare(ctx_id=0, input_size=(640, 640), det_thresh=0.5)
    streams_loader = LoadStreams(sources, imgsz=640, vid_stride=1, buffer=False)
    last_recognition = {}
    last_clear_time = datetime.datetime.now()
    threshold = 0.5
    try:
        while True:
            current_time_check = datetime.datetime.now()
            if current_time_check.day != last_clear_time.day:
                last_recognition.clear()
                last_clear_time = current_time_check
            for cam_name, sources, images, _, _ in streams_loader:
                for i, image in enumerate(images):
                    if cam_name[i] == 'camera1':
                        cropped_frame = image[480:960, 525:1165]
                    elif cam_name[i] == 'camera2':
                        cropped_frame = image[200:680, 630:1270]
                    bboxes, kpss = det_model.detect(cropped_frame, max_num=0, metric='default')
                    for j in range(bboxes.shape[0]):
                        bbox = bboxes[j, 0:4]
                        det_score = bboxes[j, 4]
                        draw_bounding_box(cropped_frame, bbox)
                        kps = None
                        if kpss is not None:
                            kps = kpss[j]
                            for kp in kps:
                                x, y = kp.astype(int)
                                cv2.circle(cropped_frame, (x, y), 3, (0, 0, 255), -1)
                        face = Face(bbox=bbox, kps=kps, det_score=det_score)
                        arc = model1.get(cropped_frame, face)
                        recognized = False
                        for key, values in database.items():
                            for item in range(0, len(values)):
                                cosine_similarity = np.dot(arc, values[item]) / (
                                        np.linalg.norm(arc) * np.linalg.norm(values[item]))
                                # Условие проверки совпадения лиц и действия на распознание
                                if cosine_similarity > threshold:
                                    recognized = True  # Это статус распознавания из вашей логики
                                    current_time = datetime.datetime.now()
                                    status = 'in' if cam_name[i] == 'camera1' else 'out'
                                    #person_camera_key = (key, cam_name[i])

                                    # last_info = last_recognition.get(person_camera_key, (None, None))
                                    # last_time, last_event = last_info
                                    last_info = last_recognition.get(key, (None, None))
                                    last_time, last_event = last_info
                                    # Проверим, прошло ли более 60 секунд с последней записи для данной камеры
                                    if not last_time or last_event != status or (current_time - last_time).total_seconds() > 60:
                                        if last_event and last_event != status and (current_time - last_time).total_seconds() <= 10:
                                            last_recognition[key] = (current_time, status)
                                            Facerec_model.objects.create(
                                                id_person=key,
                                                event=status,
                                                time=current_time.strftime('%Y-%m-%d %H:%M:%S')
                                            )
                                            print(f'{key} come {status} в {current_time} но обошел cj,snbt b d bnjut ghb')
                                        elif last_event and last_event == status:
                                            last_recognition[key] = (current_time, status)
                                            print(f'Возможно {key} прощаемся с катей, либо придерживает дверь заднему')
                                        else:
                                            last_recognition[key] = (current_time, status)
                                            Facerec_model.objects.create(
                                                id_person=key,
                                                event=status,
                                                time=current_time.strftime('%Y-%m-%d %H:%M:%S')
                                            )
                                            print(f'{key} come {status} в {current_time}')
                            if recognized:
                                break
                        # if not recognized:
                        #     print(f'Человек {in_or_out}, но не распознан')
                        #embeddings[cam_name[i]].append(arc)

                        # Отобразите кадр
                    # cv2.namedWindow(cam_name[i], cv2.WINDOW_NORMAL)
                    # cv2.imshow(cam_name[i], cropped_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        streams_loader.close()
        cv2.destroyAllWindows()
    except Exception as error:
        logging.exception(error)
