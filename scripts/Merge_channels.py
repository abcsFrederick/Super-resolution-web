# DIRECTIONS FOR USE: Run this script in the same directory as single-channel outputs from Cell DIVE scan. 
# Channel names will be automatically read from the file names. The output will be a single, pyramidal, multichannel
# OME-TIF file that combines all scans designated as "FINAL" in the name. To execute in command line, go to the
# directory where you've stored the single channel files (this script should be located there as well). Ensure 
# you've activated the environment omeropy-env3, then run: python3 Merge_channels.py

import numpy as np
import warnings
import os
import tifffile
from tifffile import imwrite
import cv2
import sys
import argparse as arg_main

parser_main = arg_main.ArgumentParser()

# assign directory
warnings.filterwarnings('ignore')

parser_main.add_argument('-p', '--data_path', help='Data folder path.', required=True)
parser_main.add_argument('-d', '--directory', help='tmp partition for saving the data.', required=True)


kwargs = vars(parser_main.parse_args())
folder = kwargs.pop('data_path')
# folder = './'

# obtain base filename
files = [f"{f}" for f in os.listdir(folder) if "_FINAL_" in f]
files.sort()
file = files[0].split("_1.0.4_")[0]
print(file)

# list relevant channel files, define output name
print(f"\n - Reading {len(files)} files")
output_dir = kwargs.pop('directory')
output = os.path.join(output_dir, file + "_merged.ome.tif")

print('Output saved in the path: ', output)
# read ome-tif files of each channel
chs = []
dtype = []
channels = []
for f in files:
    print(f"> Reading img {f}...")
    chs.append(tifffile.imread(os.path.join(folder, f)))
    dtype.append(chs[len(chs)-1].dtype)
    channels.append(f.split(file + "_")[-1].split("_FINAL")[0])
    print(f"Shape: {chs[len(chs)-1].shape}, dtype: {dtype[len(chs)-1]}, channel: {channels[len(chs)-1]}")

for i in range(1,len(dtype)):
    if dtype[i] != dtype[0]:
        print(f"Warning, image {i+1} dtype is different than dtype of 1st image.")

# combine all channels in one matrix
print(f"\n - Stacking channels")
stack = tuple(chs)
stack_working = np.stack(stack, axis=0)
print(f"Shape: {stack_working.shape}")

# create merged pyramidal ome.tif file
print(f"\n - Saving pyramidal file")
#imwrite(f"{folder}/{file}_merged.tif", stack_working)
num_subifds = 8 # 8 levels in the pyramidal
with tifffile.TiffWriter(output, bigtiff=True) as tif:
    # use tiles and JPEG compression
    options = {'tile': (256, 256), 'compression': 'lzw', 'metadata':{'Channel': {'Name': channels}}}
    # save the base image
    tif.write(stack_working, subifds=num_subifds, **options)
 
    stack_working = stack_working.astype(dtype=np.float32)
    # successively generate and save pyramid levels to the 8 SubIFDs
    for num_subifd in range(num_subifds):
        print('num_subifd: ', num_subifd)
        print('before operations shape: ', stack_working.shape)
        stack_working = np.transpose(stack_working, (1, 2, 0))  # (height, width, channel)
        print('after transpose shape: ', stack_working.shape)
        stack_working = cv2.resize(stack_working, (stack_working.shape[1] // 2, stack_working.shape[0] // 2), interpolation=cv2.INTER_LINEAR)  # (width, height)
        print('after resize shape: ', stack_working.shape)
        stack_working = np.transpose(stack_working, (2, 0, 1))  # (height, width, channel)
        print('after transpose shape: ', stack_working.shape)
        stack_working = stack_working.astype(dtype=np.uint16)
        tif.write(stack_working, **options)
        stack_working = stack_working.astype(dtype=np.float32)
        print('')