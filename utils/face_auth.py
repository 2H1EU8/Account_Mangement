import cv2
import face_recognition
import numpy as np
import os
from config import Config

class FaceAuthenticator:
    def __init__(self):
        self.known_face_encodings = []
        self.load_known_faces()
        
    def load_known_faces(self):
        faces_dir = os.path.join(Config.BASE_DIR, 'faces')
        os.makedirs(faces_dir, exist_ok=True)
        
        for face_file in os.listdir(faces_dir):
            if face_file.endswith('.jpg'):
                image = face_recognition.load_image_file(
                    os.path.join(faces_dir, face_file)
                )
                encoding = face_recognition.face_encodings(image)[0]
                self.known_face_encodings.append(encoding)
    
    def register_face(self):
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            cv2.imshow('Register Face - Press SPACE when ready', frame)
            
            if cv2.waitKey(1) & 0xFF == 32:  # SPACE key
                face_locations = face_recognition.face_locations(frame)
                if face_locations:
                    encoding = face_recognition.face_encodings(frame)[0]
                    face_path = os.path.join(Config.BASE_DIR, 'faces', 
                                           f'user_face_{len(self.known_face_encodings)}.jpg')
                    cv2.imwrite(face_path, frame)
                    self.known_face_encodings.append(encoding)
                    break
                
        cap.release()
        cv2.destroyAllWindows()
        return True
    
    def verify_face(self):
        if not self.known_face_encodings:
            return False
            
        cap = cv2.VideoCapture(0)
        for _ in range(30):  # Try for 30 frames
            ret, frame = cap.read()
            cv2.imshow('Verify Face', frame)
            cv2.waitKey(1)
            
            face_locations = face_recognition.face_locations(frame)
            if face_locations:
                encoding = face_recognition.face_encodings(frame)[0]
                matches = face_recognition.compare_faces(
                    self.known_face_encodings, encoding
                )
                if any(matches):
                    cap.release()
                    cv2.destroyAllWindows()
                    return True
                    
        cap.release()
        cv2.destroyAllWindows()
        return False
