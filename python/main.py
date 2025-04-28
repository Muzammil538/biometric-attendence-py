import cv2
import numpy as np
import os
import serial
import time
import sqlite3
from datetime import datetime
from time import sleep

# Database setup
conn = sqlite3.connect('attendance.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS attendance
             (id INTEGER PRIMARY KEY, name TEXT, date TEXT, time TEXT, 
              face_recognized INTEGER, fingerprint_matched INTEGER)''')
conn.commit()

# Initialize face recognizer
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
recognizer = cv2.face.LBPHFaceRecognizer_create()


# Load trained faces
def load_trained_faces():
    if os.path.exists('trainer.yml'):
        recognizer.read('trainer.yml')


load_trained_faces()

# Serial communication with Arduino
# arduino = serial.Serial('COM3', 9600, timeout=1)
arduino = serial.Serial('/dev/cu.usbmodem140111', 9600, timeout=1)


time.sleep(2)  # Allow time for Arduino to initialize

# Known faces (should match your training data)
known_faces = {
    0: "Sai",
    # Add more as needed
}


def train_new_face(name):
    try:
        # Ensure connection is alive
        if not arduino.is_open:
            arduino.open()

        # Add small delay after opening
        time.sleep(2)
        # Capture face images and train the model
        face_samples = []
        ids = []

        # Get the next available ID
        new_id = max(known_faces.keys()) + 1 if known_faces else 0

        cam = cv2.VideoCapture(1)
        print(f"Capturing training images for {name}. Please look at the camera...")

        count = 0
        while count < 30:  # Capture 30 samples
            ret, img = cam.read()
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                count += 1
                face_samples.append(gray[y:y + h, x:x + w])
                ids.append(new_id)

            cv2.imshow('Training', img)
            if cv2.waitKey(100) & 0xff == 27:  # ESC to exit
                break

        cam.release()
        cv2.destroyAllWindows()

        # Train the model
        recognizer.update(face_samples, np.array(ids))
        recognizer.write('trainer.yml')
        known_faces[new_id] = name

        # Enroll fingerprint
        print("Please place your finger on the sensor to enroll...")
        arduino.write(b'E')  # Send enroll command
        arduino.write(str(new_id).encode())  # Send ID

        response = ""
        while "Enrolled" not in response:
            if arduino.in_waiting > 0:
                response = arduino.readline().decode().strip()
                print(response)

        print(f"Successfully enrolled {name} with ID {new_id}")
    except serial.SerialException as e:
        print(f"Serial error: {e}")
        print("Reconnecting...")
        reconnect_arduino()
        train_new_face(name)  # Retry

def reconnect_arduino():
    global arduino
    print("Reconnecting to Arduino...")
    try:
        if arduino.is_open:
            arduino.close()
        time.sleep(1.5)
        arduino = serial.Serial('/dev/cu.usbmodem140111', 9600, timeout=1)
        time.sleep(2)  # Important wait period
        print("Arduino reconnected successfully")
    except Exception as e:
        print(f"Failed to reconnect: {e}")

def recognize_face():
    cam = cv2.VideoCapture(1)
    recognized = False
    face_id = None

    while not recognized:
        ret, img = cam.read()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            id, confidence = recognizer.predict(gray[y:y + h, x:x + w])

            if confidence < 100:
                recognized = True
                face_id = id
                name = known_faces.get(id, "Unknown")
                cv2.putText(img, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
            else:
                cv2.putText(img, "Unknown", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

        cv2.imshow('Face Recognition', img)
        if cv2.waitKey(10) & 0xff == 27:  # ESC to exit
            break

    cam.release()
    cv2.destroyAllWindows()
    return face_id


def verify_fingerprint():
    print("Please place your finger on the sensor...")

    # Clear input buffer before sending command
    arduino.reset_input_buffer()

    arduino.write(b'S')  # Send scan command
    print("Scan command sent")

    # Give Arduino time to process
    start_time = time.time()
    response = ""
    timeout = 15  # seconds

    while (time.time() - start_time) < timeout:
        if arduino.in_waiting > 0:
            response = arduino.readline().decode().strip()
            print(f"Arduino response: {response}")
            if response.startswith("ID:"):
                fingerprint_id = int(response.split(":")[1])
                return fingerprint_id if fingerprint_id != -1 else None
        time.sleep(0.1)  # Short delay to prevent CPU hogging

    print("Fingerprint verification timed out")
    return None
def mark_attendance():
    max_attempts = 3
    attempt = 0

    print("Starting face recognition...")
    face_id = recognize_face()

    if face_id is not None and face_id in known_faces:
        print(f"Face recognized as {known_faces[face_id]}")

        while attempt < max_attempts:
            attempt += 1
            print(f"Verifying fingerprint (attempt {attempt}/{max_attempts})...")

            try:
                # Clear any pending data in serial buffer
                arduino.reset_input_buffer()

                # Send scan command
                arduino.write(b'S')
                print("Scan command sent to Arduino")

                # Wait for fingerprint to be placed
                print("Please place your finger on the sensor...")

                # Read with timeout
                start_time = time.time()
                response = ""

                while not response.startswith("ID:") and (time.time() - start_time) < 10:
                    if arduino.in_waiting > 0:
                        response = arduino.readline().decode().strip()
                        print(f"Arduino response: {response}")

                if not response.startswith("ID:"):
                    print("Timeout waiting for fingerprint data")
                    continue

                fingerprint_id = int(response.split(":")[1])
                print(f"Fingerprint ID detected: {fingerprint_id}")

                if fingerprint_id == face_id:
                    print("Fingerprint matched!")
                    now = datetime.now()
                    date = now.strftime("%Y-%m-%d")
                    time_str = now.strftime("%H:%M:%S")

                    c.execute(
                        "INSERT INTO attendance (id, name, date, time, face_recognized, fingerprint_matched) VALUES (?, ?, ?, ?, ?, ?)",
                        (face_id, known_faces[face_id], date, time_str, 1, 1))
                    conn.commit()
                    print("Attendance marked successfully!")
                    return
                else:
                    print(f"Fingerprint verification failed! Expected ID {face_id}, got ID {fingerprint_id}")

            except Exception as e:
                print(f"Error during fingerprint verification: {e}")
                # Try to reconnect if there's a communication issue
                reconnect_arduino()

        print("Failed to verify fingerprint after multiple attempts")
    else:
        print("Face not recognized!")

def main_menu():
    while True:
        print("\nBiometric Attendance System")
        print("1. Mark Attendance")
        print("2. Register New User")
        print("3. View Attendance Records")
        print("4. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            mark_attendance()
        elif choice == '2':
            name = input("Enter the name of the new user: ")
            train_new_face(name)
        elif choice == '3':
            print("\nAttendance Records:")
            for row in c.execute("SELECT * FROM attendance ORDER BY date DESC, time DESC"):
                print(row)
        elif choice == '4':
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    try:
        main_menu()
    finally:
        arduino.close()
        conn.close()