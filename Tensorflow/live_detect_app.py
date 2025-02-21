import tensorflow as tf
from object_detection.utils import config_util
import os
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as viz_utils
from object_detection.builders import model_builder
import numpy as np 
import cv2  
import numpy as np



class Detection:

    WORKSPACE_PATH = 'Tensorflow/workspace'
    APIMODEL_PATH = 'Tensorflow/models'
    ANNOTATION_PATH = WORKSPACE_PATH+'/annotations'
    MODEL_PATH = WORKSPACE_PATH+'/models'
    CONFIG_PATH = MODEL_PATH+'/my_ssd_mobnet/pipeline.config'
    CHECKPOINT_PATH = MODEL_PATH+'/my_ssd_mobnet/'
    IMAGE_PATH = WORKSPACE_PATH+'/images'
    CUSTOM_MODEL_NAME = 'my_ssd_mobnet' 

    CUSTOM_MODEL_NAME = 'my_ssd_mobnet' 
    CHECKPOINT_PATH = MODEL_PATH+'/{}/'.format(CUSTOM_MODEL_NAME)
    CHECKPOINT_PATH
    conf_lev = 0.0


    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    configs = config_util.get_configs_from_pipeline_file(CONFIG_PATH)
    detection_model = model_builder.build(model_config=configs['model'], is_training=False)

    ckpt = tf.compat.v2.train.Checkpoint(model=detection_model)
    ckpt.restore(os.path.join(CHECKPOINT_PATH, 'ckpt-43')).expect_partial()

    @classmethod
    def detect_fn(cls, image):
        image, shapes = cls.detection_model.preprocess(image)
        prediction_dict = cls.detection_model.predict(image, shapes)
        detections = cls.detection_model.postprocess(prediction_dict, shapes)
        return detections

    category_index = label_map_util.create_category_index_from_labelmap(ANNOTATION_PATH+'/label_map.pbtxt')

    @classmethod
    def live_detect(cls):
        while True: 
            ret, frame = cls.cap.read()
            image_np = np.array(frame)
            
            input_tensor = tf.convert_to_tensor(np.expand_dims(image_np, 0), dtype=tf.float32)
            detections = cls.detect_fn(input_tensor)
            
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
                cls.category_index,
                use_normalized_coordinates=True,
                max_boxes_to_draw=3,
                min_score_thresh=.6,
                agnostic_mode=False)
            frame2

            cv2.imshow('object detection',  cv2.resize(image_np_with_detections, (cls.width, cls.height))) 
            cv2.imwrite("Tensorflow/workspace/images/detection.png", frame2)
            
            cv2.waitKey(1000)
            if np.less_equal(detections['detection_scores'][0],.75):
                pass
            elif np.greater_equal(detections['detection_scores'][0], .75):
                setattr(Detection,'conf_lev', detections['detection_scores'][0])
                break
