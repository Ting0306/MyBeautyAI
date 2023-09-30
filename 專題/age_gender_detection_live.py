import cv2
import time
from collections import Counter

def getFaceBox(net, frame,conf_threshold = 0.75):
    frameOpencvDnn = frame.copy()
    frameHeight = frameOpencvDnn.shape[0]
    frameWidth = frameOpencvDnn.shape[1]
    blob = cv2.dnn.blobFromImage(frameOpencvDnn,1.0,(300,300),[104, 117, 123], True, False)

    net.setInput(blob)
    detections = net.forward()
    bboxes = []

    for i in range(detections.shape[2]):
        confidence = detections[0,0,i,2]
        if confidence > conf_threshold:
            x1 = int(detections[0,0,i,3]* frameWidth)
            y1 = int(detections[0,0,i,4]* frameHeight)
            x2 = int(detections[0,0,i,5]* frameWidth)
            y2 = int(detections[0,0,i,6]* frameHeight)
            bboxes.append([x1,y1,x2,y2])
            cv2.rectangle(frameOpencvDnn,(x1,y1),(x2,y2),(0,255,0),int(round(frameHeight/150)),8)

    return frameOpencvDnn , bboxes

def run(faceProto, faceModel, ageProto, ageModel, genderProto, genderModel):
    
    MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
    ageList = ['(15-20)', '(15-20)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
    genderList = ['Male', 'Female']

    #load the network
    ageNet = cv2.dnn.readNet(ageModel,ageProto)
    genderNet = cv2.dnn.readNet(genderModel, genderProto)
    faceNet = cv2.dnn.readNet(faceModel, faceProto)

    cap = cv2.VideoCapture(0)
    padding = 20
    
    results = []  # 用於儲存每次偵測的結果
    detection_count = 0  # 偵測次數計數器

    while cv2.waitKey(1) < 0:
        #read frame
        t = time.time()
        hasFrame , frame = cap.read()

        if not hasFrame:
            cv2.waitKey()
            break
        #creating a smaller frame for better optimization
        small_frame = cv2.resize(frame,(0,0),fx = 0.5,fy = 0.5)

        frameFace ,bboxes = getFaceBox(faceNet,small_frame)
        if not bboxes:
            print("No face Detected, Checking next frame")
            continue
        for bbox in bboxes:
            face = small_frame[max(0,bbox[1]-padding):min(bbox[3]+padding,frame.shape[0]-1),
                    max(0,bbox[0]-padding):min(bbox[2]+padding, frame.shape[1]-1)]
            blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
            genderNet.setInput(blob)
            genderPreds = genderNet.forward()
            gender = genderList[genderPreds[0].argmax()]
            # print("Gender : {}, conf = {:.3f}".format(gender, genderPreds[0].max()))

            ageNet.setInput(blob)
            agePreds = ageNet.forward()
            age = ageList[agePreds[0].argmax()]
            # print("Age Output : {}".format(agePreds))
            # print("Age : {}, conf = {:.3f}".format(age, agePreds[0].max()))

            results.append((gender, age))
            
            detection_count += 1
            
            if detection_count == 20:
                break
            
            label = "{},{}".format(gender, age)
            cv2.putText(frameFace, label, (bbox[0], bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
            cv2.imshow("Age Gender Demo", frameFace)
        
        if detection_count == 20:
            break
        
    result_counter = Counter(results)  # 使用 Counter 統計結果出現次數
    most_common_result = result_counter.most_common(1)[0][0]  # 取得出現最多的結果
    print(most_common_result)

    return most_common_result