# coding:utf-8
'''
    人脸比较类
'''

import dlib
import numpy as np
import os, time


class FaceCompare:

    def __init__(self, predictor_path, face_rec_model_path):
        self.predictor_path = predictor_path
        self.face_rec_model_path = face_rec_model_path
        self.detector = dlib.get_frontal_face_detector()
        self.shape_predictor = dlib.shape_predictor(self.predictor_path)
        self.face_rec_model = dlib.face_recognition_model_v1(self.face_rec_model_path)

    def face_detection(self, url_img):
        img = dlib.load_rgb_image(url_img)
        # 检测人脸
        faces = self.detector(img, 1)
        # # 提取68个特征点
        shape = self.shape_predictor(img, faces[0])
        # 计算人脸的128维的向量
        face_message = self.face_rec_model.compute_face_descriptor(img, shape)
        return face_message

    # 欧式距离
    def compare(self, dist_1, dist_2):
        dis = np.sqrt(sum((np.array(dist_1)-np.array(dist_2))**2))
        return dis

    def score(self, url_img):
        data2 = self.face_detection(url_img)
        for parent, dirnames, filenames in os.walk(os.path.join("faces")):
            for img_path in filenames:
                try:
                    data1 = self.face_detection(os.path.join("faces", img_path))
                    goal = self.compare(data1, data2)
                    if goal < 0.4:
                        # 判断结果，如果goal小于0.4的话是同一个人，否则不是。我所用的是欧式距离判别
                        return goal, img_path
                except Exception as e:
                    print(e)
                    pass
            return 1


predictor_path = os.path.join("utils", "model", "shape_predictor_68_face_landmarks.dat")
face_rec_model_path = os.path.join("utils", "model", "dlib_face_recognition_resnet_model_v1.dat")

Face = FaceCompare(predictor_path, face_rec_model_path)