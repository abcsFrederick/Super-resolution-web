import numpy as np
import h5py
from options.test_options import TestOptions
from models import create_model
import os, glob, shutil
import torchvision.transforms as transforms
import argparse
from PIL import Image
import cv2
import skimage
Image.MAX_IMAGE_PIXELS = None

import gc
import tifffile
from tifffile import imwrite
from albumentations import (Resize, VerticalFlip, HorizontalFlip, Transpose, Rotate)
from tqdm import tqdm

import torch
from torch.utils.data import Dataset, DataLoader, sampler

class Whole_Slide_Bag_FP(Dataset):
    def __init__(self,
                 file_path,
                 ):
        """
		Args:
			file_path (string): Path to the .h5 file containing patched data.
		"""

        self.file_path = file_path

        with h5py.File(self.file_path, "r") as f:
            dset = f['coords']
            self.length = len(dset)
        self.summary()

    def __len__(self):
        return self.length

    def summary(self):
        hdf5_file = h5py.File(self.file_path, "r")
        dset = hdf5_file['coords']
        for name, value in dset.attrs.items():
            print(name, value)

        print('number of patches: ', self.length)

    def __getitem__(self, idx):
        with h5py.File(self.file_path, 'r') as hdf5_file:
            coord = hdf5_file['coords'][idx]
            img = hdf5_file['features'][idx]
        return img, coord

def save_hdf5(output_path, asset_dict, attr_dict= None, mode='a'):
    file = h5py.File(output_path, mode)
    for key, val in asset_dict.items():
        data_shape = val.shape
        # print('data_shape: ', data_shape)
        if key not in file:
            data_type = val.dtype
            chunk_shape = (1, ) + data_shape[1:]
            maxshape = (None, ) + data_shape[1:]
            dset = file.create_dataset(key, shape=data_shape, maxshape=maxshape, chunks=chunk_shape, dtype=data_type)
            dset[:] = val
            if attr_dict is not None:
                if key in attr_dict.keys():
                    for attr_key, attr_val in attr_dict[key].items():
                        dset.attrs[attr_key] = attr_val
        else:
            dset = file[key]
            dset.resize(len(dset) + data_shape[0], axis=0)
            dset[-data_shape[0]:] = val
    file.close()
    return output_path


def get_transform():
    transform_list = []
    transform_list += [transforms.ToTensor()]
    transform_list += [transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))]
    return transforms.Compose(transform_list)

def _infer_batch(model, test_patch, num_classes):
    with torch.no_grad():
        logits_all = model(test_patch[:, :, :, :])
        logits = logits_all[:, 0:num_classes, :, :]
    prob_classes_all = logits.cpu().numpy().transpose(0, 2, 3, 1)

    return (prob_classes_all + 1.0) / 2.0


def _inference(args, model, IMAGE_SIZE, BATCH_SIZE, file_name, PREDICTION_PATH, num_classes, kernel):
    device = torch.device('cuda:{}'.format(args.gpu_ids[0])) if args.gpu_ids else torch.device('cpu')
    print('device: ', device)
    model.eval()
    transforms_img = get_transform()
    print('Name of the file to be inferenced: ', len(file_name))

    mode = 'w'

    basename_string, ext = os.path.basename(file_name).split('.', 1)
    dir_string = file_name.split('/')[-2]
    print('Basename String: ', dir_string + '_' + basename_string)
    print(f'extention: {ext}, extention.upper: {ext.upper()}')
    # output_path = os.path.join(PREDICTION_PATH, dir_string + '_' + basename_string + '.h5')
    output_path = os.path.join(PREDICTION_PATH, dir_string + '/' + basename_string + '.h5')
    print('output path: ', output_path)

    if ext.upper() == 'TIFF' or ext.upper() == 'TIF' or ext.upper() == 'OME.TIF':
        print('extension is TIFF related')
        from tifffile import imread
        image_org = imread(file_name)
        image_amax = np.amax(image_org)
        image_amin = np.amin(image_org)
        image_org = (image_org - image_amin)/(image_amax - image_amin)
        image_org = image_org * 255.0
        image_org = image_org.astype(dtype=np.uint8)
    else:
        print('extension is not related to TIF')
        from skimage.io import imread
        image_org = imread(file_name)

    print('image org shape: ', image_org.shape)
    print('')

    ## Up-sample 8 times
    height = image_org.shape[0]
    width = image_org.shape[1]

    aug = Resize(p=1.0, height=height * 8, width=width * 8)
    augmented = aug(image=image_org)
    image_working = augmented['image']
    # cv2.imwrite(PREDICTION_PATH + dir_string + '_' + basename_string + '_lr.png', image_large)
    print('image working shape: ', image_working.shape)

    image_working = image_working[..., np.newaxis]

    print('image working shape: ', image_working.shape)
    print('')

    del image_org

    height = image_working.shape[0]
    width = image_working.shape[1]

    PATCH_OFFSET = IMAGE_SIZE * 2
    SLIDE_OFFSET = IMAGE_SIZE // 2

    heights = (height + PATCH_OFFSET * 2 - IMAGE_SIZE) // SLIDE_OFFSET + 1
    widths = (width + PATCH_OFFSET * 2 - IMAGE_SIZE) // SLIDE_OFFSET + 1

    height_ext = SLIDE_OFFSET * heights + PATCH_OFFSET * 2
    width_ext = SLIDE_OFFSET * widths + PATCH_OFFSET * 2

    org_slide_ext = np.zeros((height_ext, width_ext, num_classes), np.uint8)
    prob_map = np.zeros((height_ext, width_ext, num_classes), dtype=np.float32)
    weight_sum = np.zeros((height_ext, width_ext, num_classes), dtype=np.float32)

    org_slide_ext[PATCH_OFFSET: PATCH_OFFSET + height, PATCH_OFFSET:PATCH_OFFSET + width, :] = image_working[:, :, :]

    test_patch_3c = np.zeros((IMAGE_SIZE, IMAGE_SIZE, 3), np.uint8)
    test_patch_tensor = torch.zeros([BATCH_SIZE, 3, IMAGE_SIZE, IMAGE_SIZE], dtype=torch.float).cuda(
        non_blocking=True)

    position = 0
    coords = np.zeros((BATCH_SIZE, 2), np.int32)

    for i in tqdm(range(heights)):
        for j in range(widths):
            test_patch_1c = org_slide_ext[i * SLIDE_OFFSET: i * SLIDE_OFFSET + IMAGE_SIZE,
                         j * SLIDE_OFFSET: j * SLIDE_OFFSET + IMAGE_SIZE, :]

            test_avg = np.average(test_patch_1c)
            if test_avg > 11: ## If the value is too low, some of the tissue will not be inferenced
                for l in range(3):
                    test_patch_3c[:, :, l] = test_patch_1c[:, :, 0]
                coords[position, 0] = i * SLIDE_OFFSET
                coords[position, 1] = j * SLIDE_OFFSET
                test_patch_tensor[position, :, :, :] = transforms_img(test_patch_3c).to(device)
                position += 1

            if position == BATCH_SIZE:
                batch_predictions = _infer_batch(model, test_patch_tensor, num_classes)
                asset_dict = {'features': batch_predictions, 'coords': coords}
                save_hdf5(output_path, asset_dict, attr_dict=None, mode=mode)
                mode = 'a'

                position = 0

    # Very last part of the region
    if position != 0:
        batch_predictions = _infer_batch(model, test_patch_tensor, num_classes)
        asset_dict = {'features': batch_predictions[:position, ...], 'coords': coords[:position, ...]}
        save_hdf5(output_path, asset_dict, attr_dict=None, mode=mode)


    ## Free memory as much as possible
    del org_slide_ext

    dataset = Whole_Slide_Bag_FP(file_path=output_path)
    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    kwargs = {'num_workers': 4, 'pin_memory': True} if device.type == "cuda" else {}
    loader = DataLoader(dataset=dataset, batch_size=BATCH_SIZE, **kwargs, collate_fn=None)

    for count, (batch, coords) in enumerate(loader):
        with torch.no_grad():

            for i in range(len(batch)):
                # Working but not refined code
                coord_y = coords[i][0]
                coord_x = coords[i][1]
                image = np.asarray(batch[i])

                # Previous code
                prob_map[coord_y: coord_y + IMAGE_SIZE, coord_x: coord_x + IMAGE_SIZE, :] \
                    += np.multiply(image, kernel)

                weight_sum[coord_y: coord_y + IMAGE_SIZE, coord_x: coord_x + IMAGE_SIZE, :] \
                    += kernel


    prob_map = np.true_divide(prob_map, weight_sum)
    prob_map_valid = prob_map[PATCH_OFFSET:PATCH_OFFSET + height, PATCH_OFFSET:PATCH_OFFSET + width, :]

    prob_map_valid = prob_map_valid * 255.0
    prob_map_valid = np.squeeze(prob_map_valid.astype('uint8'))

    # imwrite(output_file_path, prob_map_valid)

    ## Delete hd5 file
    os.remove(output_path)

    gc.collect()

    ## Rewriting to ome.tif
    print(f'image size: {prob_map_valid.shape}')

    image_height = prob_map_valid.shape[0]
    image_width = prob_map_valid.shape[1]

    image_amax = np.amax(prob_map_valid)
    image_amin = np.amin(prob_map_valid)
    print(f'image min value: {image_amin}, image max value: {image_amax}')

    num_channels = 1
    print(f'num_channels: ', num_channels)

    stack_working = np.zeros((num_channels, image_height, image_width), np.uint32)
    print('stack_working.shape: ', stack_working.shape)
    stack_working[0, :, :] = prob_map_valid
    del prob_map_valid

    num_subifds = 8
    output_file_path = os.path.join(PREDICTION_PATH, dir_string + '/' + basename_string + '_pr.ome.tif')
    # output_file_path = os.path.join(PREDICTION_PATH, dir_string + '_' + basename_string + '_pr.ome.tif')
    with tifffile.TiffWriter(output_file_path, bigtiff=True) as tif:
        # use tiles and JPEG compression
        options = {'tile': (256, 256), 'compression': 'lzw'}
        # save the base image
        tif.write(stack_working, subifds=num_subifds, **options)

        stack_working = stack_working.astype(dtype=np.float32)
        # successively generate and save pyramid levels to the 8 SubIFDs
        for num_subifd in range(num_subifds):
            print('num_subifd: ', num_subifd)
            stack_working = np.transpose(stack_working, (1, 2, 0))  # (height, width, channel)
            stack_working = cv2.resize(stack_working, (stack_working.shape[1] // 2, stack_working.shape[0] // 2),
                                       interpolation=cv2.INTER_LINEAR)  # (width, height)
            print('after resize shape: ', stack_working.shape)  # should be (height, width, channel)
            stack_working = np.expand_dims(stack_working, axis=2)
            print('after newaxis shape: ', stack_working.shape)  # should be (height, width, channel)
            stack_working = np.transpose(stack_working, (2, 0, 1))  # (height, width, channel)
            print('after transpose shape: ', stack_working.shape)
            stack_working = stack_working.astype(dtype=np.uint32)
            tif.write(stack_working, **options)
            stack_working = stack_working.astype(dtype=np.float32)
            print('')

    del stack_working
    gc.collect()

    return output_file_path

def _gaussian_2d(num_classes, image_size, sigma, mu):
    x, y = np.meshgrid(np.linspace(-1, 1, image_size), np.linspace(-1, 1, image_size))
    d = np.sqrt(x * x + y * y)
    # sigma, mu = 1.0, 0.0
    k = np.exp(-((d - mu) ** 2 / (2.0 * sigma ** 2)))

    k_min = np.amin(k)
    k_max = np.amax(k)

    k_normalized = (k - k_min) / (k_max - k_min)
    k_normalized[k_normalized <= 1e-6] = 1e-6

    kernels = [(k_normalized) for i in range(num_classes)]
    kernel = np.stack(kernels, axis=-1)

    print('Kernel shape: ', kernel.shape)
    print('Kernel Min value: ', np.amin(kernel))
    print('Kernel Max value: ', np.amax(kernel))

    return kernel


def inference_WSIs(args, model, image_size, batch_size, file_name, output_path, num_classes):
    kernel = _gaussian_2d(num_classes, image_size, 0.5, 0.0)
    output_file_path = _inference(args, model, image_size, batch_size, file_name, output_path, num_classes, kernel)

    return output_file_path

def parse():
    parser = argparse.ArgumentParser(description='PyTorch Super-resolution Training')
    parser.add_argument('--checkpoints_dir', type=str, default='../weights/checkpoints', help='models are saved here')
    parser.add_argument('--name', type=str, default='experiment_name',
                        help='name of the experiment. It decides where to store samples and models')
    parser.add_argument('--model', type=str, default='cycle_gan', help='chooses which model to use. [cycle_gan | pix2pix | test | colorization]')
    parser.add_argument('--tnum', default=1, type=int, metavar='N',
                        help='set the Try number (default: 1)')
    parser.add_argument('--knum', default=1, type=int, metavar='N',
                        help='set the K-Fold interation number (default: 1)')
    parser.add_argument('--num_threads', default=4, type=int, help='# threads for loading data')
    parser.add_argument('--batch_size', type=int, default=1, help='input batch size')
    parser.add_argument('--load_size', type=int, default=256, help='scale images to this size')
    parser.add_argument('--crop_size', type=int, default=256, help='then crop to this size')
    parser.add_argument('--load_iter', type=int, default='0',
                        help='which iteration to load? if load_iter > 0, the code will load models by iter_[load_iter]; otherwise, the code will load models by [epoch]')
    args = parser.parse_args()
    print('Did it parsed?')
    return args

def cycle_gan_test(file_name, results_dir):
    opt = TestOptions().parse()  # get test options
    # hard-code some parameters for test
    opt.dataroot = './datasets/low2high'
    opt.checkpoints_dir = '/mnt/hpc/webdata/server/fsivgl-cellt01d/weights/checkpoints'
    opt.results_dir = results_dir
    opt.name = 'esr105_cyclegan3_interpol_batch8'
    opt.model = 'cycle_gan'
    opt.crop_size = 256
    opt.load_size = 256
    opt.load_iter = 0
    opt.gpu_ids = [0]
    opt.no_dropout = True

    opt.num_threads = 0  # test code only supports num_threads = 0
    opt.batch_size = 1  # test code only supports batch_size = 1
    opt.serial_batches = True  # disable data shuffling; comment this line if results on randomly chosen images are needed.
    opt.no_flip = True  # no flip; comment this line if results on flipped images are needed.
    opt.display_id = -1  # no visdom display; the test code saves the results to a HTML file.
    opt.file_name = file_name
    model = create_model(opt)  # create a model given opt.model and other options
    print('model created')
    print('option isTrain: ', opt.isTrain)
    opt.isTrain = False
    model.setup(opt)  # regular setup: load and print networks; create schedulers

    # file name which would be inferenced for synthetic super-resolution image generation
    # file_name = opt.file_name

    model = create_model(opt)  # create a model given opt.model and other options
    model.setup(opt)               # regular setup: load and print networks; create schedulers

    output_file_path = inference_WSIs(opt, model.netG_A, opt.crop_size, 16, file_name, opt.results_dir, 1)

    print('Result path: ', output_file_path)
    return output_file_path

if __name__ == '__main__':
    file_name = '/mnt/hpc/webdata/server/fsivgl-cellt01d/tmp/3034_G12C_pflox_veh_frame_6_channel_AF555.png'
    results_dir = '/mnt/hpc/webdata/server/fsivgl-cellt01d/tmp/'
    cycle_gan_test(file_name, results_dir)

# python image_from_omero.py --dataroot ./datasets/low2high --name esr105_cyclegan3_interpol_batch8 --model cycle_gan 
# --gpu_ids 2 --load_size 256 --crop_size 256 --load_iter 0 --file_name './Data/CZ_ESR105/3034_G12C_pflox_veh_frame_6_channel_AF555.png'