import cv2
import mediapipe as mp
import numpy as np
import math as m
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

import json
import pymongo
from datetime import datetime

client = pymongo.MongoClient("mongodb+srv://ergobot:ergobot@cluster0.ebhix5u.mongodb.net/?retryWrites=true&w=majority")

position = client["position"]
users = position["users"]

email = {"email": "rajprabhakar@gmail.com"}

user = {
    "email": "rajprabhakar@gmail.com",
    "days": []
}

users.update_one({"email": "rajprabhakar@gmail.com"}, {"$setOnInsert": user}, upsert=True)

today = {
    "date": str(datetime.now().date()),
    "good_pos": [],
    "bad_pos": [],
    "good_duration": 0,
    "bad_duration": 0
}

users.update_one({"email": "rajprabhakar@gmail.com"}, {"$addToSet": {"days": today}})

# Initialize frame counters.
good_frames = 0
bad_frames  = 0
 
# Font type.
font = cv2.FONT_HERSHEY_SIMPLEX
 
# Colors.
blue = (255, 127, 0)
red = (50, 50, 255)
green = (127, 255, 0)
dark_blue = (127, 20, 0)
light_green = (127, 233, 100)
yellow = (0, 255, 255)
pink = (255, 0, 255)

#helpers
def findDistance(x1, y1, x2, y2):
    dist = m.sqrt((x2-x1)**2+(y2-y1)**2)
    return dist

def findAngle(x1, y1, x2, y2):
    theta = m.acos( (y2 -y1)*(-y1) / (m.sqrt(
        (x2 - x1)**2 + (y2 - y1)**2 ) * y1) )
    degree = int(180/m.pi)*theta
    return degree

pos = "start"
start = datetime.now()

good_pos = []
bad_pos = []

good_duration = 0
bad_duration = 0

# video process
cap=cv2.VideoCapture(0)

#setup pose
with mp_pose.Pose(min_detection_confidence=0.5,min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        ret,frame = cap.read()


        #recolor img to rgb
        image = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        image.flags.writeable = False

        #make detection 
        results = pose.process(image)

        #recolor back to  BGR
        image.flags.writeable = True
        image = cv2.cvtColor(image,cv2.COLOR_RGB2BGR)

        #extract landmark
        try:
            h, w = image.shape[:2]
            fps = cap.get(cv2.CAP_PROP_FPS)
            landmarks = results.pose_landmarks.landmark
            lm = results.pose_landmarks
            lmPose  = mp_pose.PoseLandmark
            # Left shoulder.
            l_shldr_x = int(lm.landmark[lmPose.LEFT_SHOULDER].x * w)
            l_shldr_y = int(lm.landmark[lmPose.LEFT_SHOULDER].y * h)
            # Right shoulder.
            r_shldr_x = int(lm.landmark[lmPose.RIGHT_SHOULDER].x * w)
            r_shldr_y = int(lm.landmark[lmPose.RIGHT_SHOULDER].y * h)

            # Left ear.
            l_ear_x = int(lm.landmark[lmPose.LEFT_EAR].x * w)
            l_ear_y = int(lm.landmark[lmPose.LEFT_EAR].y * h)

            # Left hip.
            l_hip_x = int(lm.landmark[lmPose.LEFT_HIP].x * w)
            l_hip_y = int(lm.landmark[lmPose.LEFT_HIP].y * h)

            #calculation
            # Calculate angles.
            neck_inclination = findAngle(l_shldr_x, l_shldr_y, l_ear_x, l_ear_y)
            torso_inclination = findAngle(l_hip_x, l_hip_y, l_shldr_x, l_shldr_y)

            # Draw landmarks.
            cv2.circle(image, (l_shldr_x, l_shldr_y), 7, yellow, -1)
            cv2.circle(image, (l_ear_x, l_ear_y), 7, yellow, -1)

            # Let's take y - coordinate of P3 100px above x1,  for display elegance.
            # Although we are taking y = 0 while calculating angle between P1,P2,P3.
            cv2.circle(image, (l_shldr_x, l_shldr_y - 100), 7, yellow, -1)
            cv2.circle(image, (r_shldr_x, r_shldr_y), 7, pink, -1)
            cv2.circle(image, (l_hip_x, l_hip_y), 7, yellow, -1)

            # Similarly, here we are taking y - coordinate 100px above x1. Note that
            # you can take any value for y, not necessarily 100 or 200 pixels.
            cv2.circle(image, (l_hip_x, l_hip_y - 100), 7, yellow, -1)

            # Put text, Posture and angle inclination.
            # Text string for display.
            angle_text_string = 'Neck : ' + str(int(neck_inclination)) + '  Torso : ' + str(int(torso_inclination))
            cv2.putText(image,angle_text_string,(10, 30), font, 0.9, light_green, 2)

            #==========>
                        # Calculate distance between left shoulder and right shoulder points.
            offset = findDistance(l_shldr_x, l_shldr_y, r_shldr_x, r_shldr_y)
            
            # Assist to align the camera to point at the side view of the person.
            # Offset threshold 30 is based on results obtained from analysis over 100 samples.
            if offset < 100:
                cv2.putText(image, str(int(offset)) + ' Aligned', (w - 150, 30), font, 0.9, green, 2)
            else:
                cv2.putText(image, str(int(offset)) + ' Not Aligned', (w - 150, 30), font, 0.9, red, 2)


            #==========>
                        # Determine whether good posture or bad posture.
            # The threshold angles have been set based on intuition.
            if neck_inclination < 40 and torso_inclination < 10:
                bad_frames = 0
                good_frames += 1

                cv2.putText(image, angle_text_string, (10, 30), font, 0.9, light_green, 2)
                cv2.putText(image, str(int(neck_inclination)), (l_shldr_x + 10, l_shldr_y), font, 0.9, light_green, 2)
                cv2.putText(image, str(int(torso_inclination)), (l_hip_x + 10, l_hip_y), font, 0.9, light_green, 2)

                # Join landmarks.
                cv2.line(image, (l_shldr_x, l_shldr_y), (l_ear_x, l_ear_y), green, 4)
                cv2.line(image, (l_shldr_x, l_shldr_y), (l_shldr_x, l_shldr_y - 100), green, 4)
                cv2.line(image, (l_hip_x, l_hip_y), (l_shldr_x, l_shldr_y), green, 4)
                cv2.line(image, (l_hip_x, l_hip_y), (l_hip_x, l_hip_y - 100), green, 4)

            else:
                good_frames = 0
                bad_frames += 1

                cv2.putText(image, angle_text_string, (10, 30), font, 0.9, red, 2)
                cv2.putText(image, str(int(neck_inclination)), (l_shldr_x + 10, l_shldr_y), font, 0.9, red, 2)
                cv2.putText(image, str(int(torso_inclination)), (l_hip_x + 10, l_hip_y), font, 0.9, red, 2)

                # Join landmarks.
                cv2.line(image, (l_shldr_x, l_shldr_y), (l_ear_x, l_ear_y), red, 4)
                cv2.line(image, (l_shldr_x, l_shldr_y), (l_shldr_x, l_shldr_y - 100), red, 4)
                cv2.line(image, (l_hip_x, l_hip_y), (l_shldr_x, l_shldr_y), red, 4)
                cv2.line(image, (l_hip_x, l_hip_y), (l_hip_x, l_hip_y - 100), red, 4)

            # Calculate the time of remaining in a particular posture.
            good_time = (1 / fps) * good_frames
            bad_time =  (1 / fps) * bad_frames

            # Pose time.
            if good_time > 0:
                if pos != "good":
                    now = datetime.now()
                    duration = (now - start).total_seconds()
                    #users.update_one({"email": "rajprabhakar@gmail.com"}, {"$push": {"bad_pos": {"$push": {now.date(): {"$push": {"start": start.time(), "end": now.time()}}}}}})
                    if duration>2:
                        bad_pos.append({"start": str(start.time()), "end": str(now.time()), "duration": duration})
                        bad_duration = bad_duration + duration
                    users.update_one({"email": "rajprabhakar@gmail.com"}, {"$set": {"now": {"pose": "good"}}})
                    pos = "good"
                    start = now
                time_string_good = 'Good Posture Time : ' + str(round(good_time, 1)) + 's'
                cv2.putText(image, time_string_good, (10, h - 20), font, 0.9, green, 2)
            else:
                if pos != "bad":
                    now = datetime.now()
                    duration = (now - start).total_seconds()
                    #users.update_one({"email": "rajprabhakar@gmail.com"}, {"$push": {"good_pos": {"$push": {now.date(): {"$push": {"start": start.time(), "end": now.time()}}}}}})
                    if duration>2:
                        good_pos.append({"start": str(start.time()), "end": str(now.time()), "duration": duration})
                        good_duration = good_duration + duration
                    users.update_one({"email": "rajprabhakar@gmail.com"}, {"$set": {"now": {"pose": "bad", "remedy": "wait"}}})
                    pos = "bad"
                    start = now
                time_string_bad = 'Bad Posture Time : ' + str(round(bad_time, 1)) + 's'
                if bad_time>1:
                    if neck_inclination>40 and torso_inclination>10:
                        users.update_one({"email": "rajprabhakar@gmail.com"}, {"$set": {"now": {"pose": "bad", "remedy": "straight"}}})
                    elif neck_inclination>40:
                        users.update_one({"email": "rajprabhakar@gmail.com"}, {"$set": {"now": {"pose": "bad", "remedy": "neck"}}})
                    elif torso_inclination>10:
                        users.update_one({"email": "rajprabhakar@gmail.com"}, {"$set": {"now": {"pose": "bad", "remedy": "back"}}})
                cv2.putText(image, time_string_bad, (10, h - 20), font, 0.9, red, 2)
        except:
            pass
        
        #render
        #mp_drawing.draw_landmarks(image,results.pose_landmarks,mp_pose.POSE_CONNECTIONS)

        cv2.imshow('Mediapipe Feed',image)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            users.update_one({"email": "rajprabhakar@gmail.com", "days.date": str(datetime.now().date())},
                             {"$push": {"days.$.good_pos": {"$each": good_pos}, "days.$.bad_pos": {"$each": bad_pos}},
                              "$inc": {"days.$.good_duration": good_duration, "days.$.bad_duration": bad_duration}})
            break

cap.release()
cv2.destroyAllWindows()