# importing everything needed
from hailo_sdk_client import ClientRunner, InferenceContext

import json
import os
import random

import matplotlib.patches as patches
import numpy as np
import tensorflow as tf
from IPython.display import SVG
from matplotlib import pyplot as plt
from PIL import Image


# First, we will prepare the calibration set. Resize the images to the correct size and crop them.
from tensorflow.python.eager.context import eager_mode


def preproc(image, output_height=640, output_width=640, resize_side=640):
    ''' imagenet-standard: aspect-preserving resize to 256px smaller-side, then central-crop to 224px'''
    with eager_mode():
        h, w = image.shape[0], image.shape[1]
        scale = tf.cond(tf.less(h, w), lambda: resize_side / h, lambda: resize_side / w)
        resized_image = tf.compat.v1.image.resize_bilinear(tf.expand_dims(image, 0), [int(h*scale), int(w*scale)])
        cropped_image = tf.compat.v1.image.resize_with_crop_or_pad(resized_image, output_height, output_width)

        return tf.squeeze(cropped_image)

#calibration dataset. WSL wont support all training dataset
images_path = '/home/bajram/Hailo8l/datasets/calibration'
images_list = [img_name for img_name in os.listdir(images_path) if
               os.path.splitext(img_name)[1] == '.jpg']

calib_dataset = np.zeros((len(images_list), 640, 640, 3))
for idx, img_name in enumerate(sorted(images_list)):
    img = np.array(Image.open(os.path.join(images_path, img_name)))
    img_preproc = preproc(img)
    calib_dataset[idx, :, :, :] = img_preproc.numpy()


np.save('calib_set.npy', calib_dataset)

print(calib_dataset.shape)

# Second, we will load our parsed HAR from the Parsing Tutorial

path_l = '/home/bajram/Hailo8l/model/runs/detect/retrain_yolov11n/weights/'
model_name = path_l+'best'
hailo_model_har_name = f'{model_name}.har'
assert os.path.isfile(hailo_model_har_name), 'Please provide valid path for HAR file'
runner = ClientRunner(har=hailo_model_har_name)
# By default it uses the hw_arch that is saved on the HAR. For overriding, use the hw_arch flag.

alls = '''
quantization_param([conv54, conv65, conv80], force_range_out=[0.0, 1.0])
normalization1 = normalization([0.0, 0.0, 0.0], [255.0, 255.0, 255.0])
change_output_activation(conv54, sigmoid)
change_output_activation(conv65, sigmoid)
change_output_activation(conv80, sigmoid)
nms_postprocess("/home/bajram/Hailo8l/config/postprocess_config/yolov11n_nms_config.json", meta_arch=yolov8, engine=cpu)

allocator_param(width_splitter_defuse=disabled)

'''
## yolov8 meta_arch is used for yolo based models, including v11 so its correct like this.

# Load the model script to ClientRunner so it will be considered on optimization
runner.load_model_script(alls)

try:
    # Call Optimize to perform the optimization process
    runner.optimize(calib_dataset)

    # Save the result state to a Quantized HAR file
    quantized_model_har_path = f'{model_name}_quantized_model.har'
    runner.save_har(quantized_model_har_path)
    print(f"Quantized model saved to {quantized_model_har_path}")
except Exception as e:
    print(f"Optimization failed: {e}")