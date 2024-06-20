import os
import omero
import time
from omero.gateway import BlitzGateway
from omero.cli import cli_login
from multiprocessing import Pool, cpu_count
from functools import partial
from image_from_omero import cycle_gan_test

def connect_to_omero(user, password, host, port=4064, suid=None):
    if suid != None:
        conn = BlitzGateway( host=host, port=port)
        conn.connect(sUuid=suid)
    else:
        conn = BlitzGateway(user, password, host=host, port=port)
        conn.connect()
    user = conn.getUser()
    # print("Current user:")
    # print("   ID:", user.getId())
    # print("   Username:", user.getName())
    # print("   Full Name:", user.getFullName())
    # print("Member of:")
    for g in conn.getGroupsMemberOf():
        print("   ID:", g.getName(), " Name:", g.getId())
    group = conn.getGroupFromContext()
    # print("Current group: ", group.getName())
    return conn


def download_omero_image(imageId, username, token, host, dataset_dir):
    # if image.getFileset() is None:
    #     print("No files to download for Image", image.id)
    # # image_dir = os.path.join(dataset_dir, image.name)
    # # If each image is a single file, or are guaranteed not to clash
    # # then we don't need image_dir. Can use dataset_dir instead
    
    # fileset = image.getFileset()
    # if fileset is None:
    #     print('Image has no Fileset')
    # dc.download_fileset(conn, fileset, dataset_dir)
    # with cli_login("tianyi_test@nife-images-dev.cancer.gov", "-w", "mivsyv-dYfrit-wezmy6") as cli:
    with cli_login("-u", username, "-w", token, host) as cli:
        cli.invoke(["download", f'Image:{imageId}', dataset_dir])


def data_fetch(data_id, data_type, username, token, omero_host, shared_partition_tmp_directory):
    print('fetching omero data')
    conn = connect_to_omero(username, token, omero_host)
    # conn = connect_to_omero("tianyi_test","mivsyv-dYfrit-wezmy6","nife-images-dev.cancer.gov")
    data = conn.getObject(data_type, data_id)
    # dc = DownloadControl()


    dataset_dir = os.path.join(shared_partition_tmp_directory, data.name)
    os.makedirs(dataset_dir, exist_ok=True)

    if data_type == 'Dataset':
        print("There are {} CPUs on this machine ".format(cpu_count()))
        pool = Pool(cpu_count() - 1)
        download_func = partial(download_omero_image, username = username, token = token, host = omero_host, dataset_dir = dataset_dir)
        imageIds = []
        for image in data.listChildren():
            imageIds.append(image.id)
        results = pool.map(download_func, imageIds)
        pool.close()
        pool.join()
    else:
        image = data
        download_omero_image(image.id, username, token, omero_host, dataset_dir)

    return dataset_dir

import argparse as arg_main

parser_main = arg_main.ArgumentParser()
parser_main.add_argument('-i', '--data_id', help='omero data id.', required=True)
parser_main.add_argument('-t', '--data_type', help='omero data type.', required=True)
parser_main.add_argument('-u', '--user', help='current login username', required=True)
parser_main.add_argument('-k', '--token', help='current login user token', required=True)
parser_main.add_argument('-d', '--directory', help='tmp partition for saving the data.', required=True)
parser_main.add_argument('-host', '--omero_host', help='omero host.', required=True)


kwargs = vars(parser_main.parse_args())

try:
    data_id = kwargs.pop('data_id')
    data_type = kwargs.pop('data_type')
    username = kwargs.pop('user')
    token = kwargs.pop('token')
    omero_host = kwargs.pop('omero_host')
    directory = kwargs.pop('directory')
except Exception:
    print('need data_id, data_type, username, token')
    sys.exit()

conn = connect_to_omero(username, token, omero_host)

fetch_start = time.time()
file_dir = data_fetch(data_id, data_type, username, token, omero_host, directory)
fetch_end = time.time()
print('Finished fetching data.')
print('--- Finish fetching in %s seconds ---' % (fetch_end - fetch_start))
print('Run following analysis....')

def createAnImage():
    import numpy
    from PIL import Image

    # path = './Slide1413_cellseg/SLIDE-1413_2.0.4_R000_Cy3_CST-CD3E-O_FINAL_AFR_F_cp_masks.tif'
    path = './ivg_temp_RGB.tif'
    a = numpy.random.rand(30,30,3) * 255
    im_out = Image.fromarray(a.astype('uint8')).convert('RGB')
    im_out.save(path)

    return path

def image2Omero(conn, path):
    import ezomero
    ezomero.print_groups(conn)

    image_ids = ezomero.ezimport(conn, path, dataset=919 )

    # image = conn.getObject("Image", image_ids[0])
    # image.setName(path)
    # image.save()

    return image_ids

# print('Creating a temp image named as ivg_temp_RGB.tif.')
# imagePath = createAnImage()
print('Running cycle gan inference for images in the directory: ', file_dir)

for file in os.listdir(file_dir):
    print('--- Running image: ', file)
    file_path = os.path.join(file_dir, file)
    prediction_start = time.time()
    output_file_path = cycle_gan_test(file_path, directory)
    prediction_end = time.time()
    print('Finish cycle gan prediction.')
    print('--- Finish prediction in %s seconds ---' % (prediction_end - prediction_start))

    print('Uploading prediction image back to omero server. ')
    conn = connect_to_omero(username, token, omero_host)

    image2Omero_start = time.time()
    imageID = image2Omero(conn, output_file_path)
    image2Omero_end = time.time()
    print("Upload image to image Id: ", imageID)
    print('--- Finish uploading in %s seconds ---' % (image2Omero_end - image2Omero_start))

print("Complete.")