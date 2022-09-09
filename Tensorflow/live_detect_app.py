import tensorflow as tf
from object_detection.utils import config_util
import os
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as viz_utils
from object_detection.builders import model_builder
import numpy as np 
#from PIL import Image
#import pathlib
import cv2 
#import matplotlib.pyplot as plt 
import numpy as np



WORKSPACE_PATH = 'Tensorflow/workspace'
APIMODEL_PATH = 'Tensorflow/models'
ANNOTATION_PATH = WORKSPACE_PATH+'/annotations'
MODEL_PATH = WORKSPACE_PATH+'/models'
CONFIG_PATH = MODEL_PATH+'/my_ssd_mobnet/pipeline.config'
CHECKPOINT_PATH = MODEL_PATH+'/my_ssd_mobnet/'
IMAGE_PATH = WORKSPACE_PATH+'/images'
CUSTOM_MODEL_NAME = 'my_ssd_mobnet' 

########################################################
#####           LOAD TRAINED MODEL            ##########
########################################################

CUSTOM_MODEL_NAME = 'my_ssd_mobnet' 
CHECKPOINT_PATH = MODEL_PATH+'/{}/'.format(CUSTOM_MODEL_NAME)
CHECKPOINT_PATH

# Load pipeline config and build a detection model
configs = config_util.get_configs_from_pipeline_file(CONFIG_PATH)
detection_model = model_builder.build(model_config=configs['model'], is_training=False)

# Restore checkpoint
ckpt = tf.compat.v2.train.Checkpoint(model=detection_model)
ckpt.restore(os.path.join(CHECKPOINT_PATH, 'ckpt-13')).expect_partial()

@tf.function
def detect_fn(image):
    image, shapes = detection_model.preprocess(image)
    prediction_dict = detection_model.predict(image, shapes)
    detections = detection_model.postprocess(prediction_dict, shapes)
    return detections

category_index = label_map_util.create_category_index_from_labelmap(ANNOTATION_PATH+'/label_map.pbtxt')

############################################################
#############     GET MODEL METRICS            #############
############################################################

# Run this output in a bash terminal in the root directory to get the performance metrics 
print("""python {}/research/object_detection/model_main_tf2.py --model_dir={}/{} --pipeline_config_path={}/{}/pipeline.config --checkpoint_dir={}/{}""".format(APIMODEL_PATH, MODEL_PATH, CUSTOM_MODEL_NAME, MODEL_PATH, CUSTOM_MODEL_NAME, MODEL_PATH, CUSTOM_MODEL_NAME))

############################################################
##############       CONNECT TO WEBCAM             #########
############################################################
 
cap = cv2.VideoCapture(0)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

############################################################
##############      RUN DETECTION                 ##########
############################################################

while True: 
    ret, frame = cap.read()
    image_np = np.array(frame)
    
    input_tensor = tf.convert_to_tensor(np.expand_dims(image_np, 0), dtype=tf.float32)
    detections = detect_fn(input_tensor)
    
    num_detections = int(detections.pop('num_detections'))
    detections = {key: value[0, :num_detections].numpy()
                  for key, value in detections.items()}
    detections['num_detections'] = num_detections

    # detection_classes should be ints.
    detections['detection_classes'] = detections['detection_classes'].astype(np.int64)

    label_id_offset = 1
    image_np_with_detections = image_np.copy()

    frame2 = viz_utils.visualize_boxes_and_labels_on_image_array(
                image_np_with_detections,
                detections['detection_boxes'],
                detections['detection_classes']+label_id_offset,
                detections['detection_scores'],
                category_index,
                use_normalized_coordinates=True,
                max_boxes_to_draw=3,
                min_score_thresh=.6,
                agnostic_mode=False)

    cv2.imshow('object detection',  cv2.resize(image_np_with_detections, (1280, 720))) #(800, 600)))
    
    #################################################################
    ################## save image with bounding box #################
    #################################################################
    cv2.imwrite("Tensorflow/workspace/images/results/detection.png", frame2)
        
    key = cv2.waitKey(500)#half of 1 second
    
    if np.greater_equal(detections['detection_scores'][0], .6):
        obj = detections['detection_scores'][0]
        break

    if cv2.waitKey(1) & key ==27:
        cap.release()
        break

# stops detection 
cap.release()
cv2.destroyAllWindows()