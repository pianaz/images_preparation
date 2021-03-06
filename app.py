import sys
import os
import json
import cv2
import xml.etree.ElementTree as ET
import numpy as np

# REQUIRES lxml


START_BOUNDING_BOX_ID = 1
PRE_DEFINE_CATEGORIES = {}

def get(root, name):
    vars = root.findall(name)
    return vars


def get_and_check(root, name, length):
    vars = root.findall(name)
    if len(vars) == 0:
        raise NotImplementedError('Can not find %s in %s.'%(name, root.tag))
    if length> 0 and len(vars) != length:
        raise NotImplementedError('The size of %s is supposed to be %d, but is %d.'%(name, length, len(vars)))
    if length == 1:
        vars = vars[0]
    return vars


def get_filename_as_int(filename):
    try:
        filename = os.path.splitext(filename)[0]
        return int(filename)
    except:
        raise NotImplementedError('Filename %s is supposed to be an integer.'%(filename))

def resize(idx,img_dir,xmin,ymin,xmax,ymax):
    files=os.listdir(img_dir)
    imageToPredict = cv2.imread(os.path.join(img_dir,files[idx]), 3) 
    folder = "images/resized/"

    y_ = imageToPredict.shape[0]
    x_ = imageToPredict.shape[1]

    targetSize = [450,800]
    x_scale = targetSize[1] / x_
    y_scale = targetSize[0] / y_
    img = cv2.resize(imageToPredict, (targetSize[1], targetSize[0]));
    cv2.imwrite(os.path.join(folder,files[idx]),img)
    img = np.array(img)

    ymin = int(np.round(ymin * x_scale))
    xmin = int(np.round(xmin * y_scale))
    ymax = int(np.round(ymax * x_scale))
    xmax = int(np.round(xmax * y_scale))
    return xmin, ymin,xmax,ymax


def convert(img_dir, xml_dir, json_file):
    json_dict = {"images":[], "type": "instances", "annotations": [],
                 "categories": []}
    categories = PRE_DEFINE_CATEGORIES
    bnd_id = START_BOUNDING_BOX_ID
    idx=0
    for filename in os.listdir(xml_dir):
        with open(os.path.join(xml_dir, filename), 'r') as xml_f:
            tree = ET.parse(xml_f)
            root = tree.getroot()
            path = get(root,'path')
            if len(path) == 1:
                filename = os.path.basename(path[0].text)
            elif len(path) == 0:
                filename = get_and_check(root,'filename', 1).text
            else:
                raise NotImplementedError('%d paths found in %s'%(len(path), line))
            ## The filename must be a number
            image_id = get_filename_as_int(filename)
            size = get_and_check(root,'size', 1)
            width = int(get_and_check(size,'width', 1).text)
            height = int(get_and_check(size,'height', 1).text)
            image = {'file_name': filename,'height': height,'width': width,
                    'id':image_id}
            json_dict['images'].append(image)
            for obj in get(root,'object'):
                category = get_and_check(obj,'name', 1).text
                if category not in categories:
                    new_id = len(categories)
                    categories[category] = new_id
                category_id = categories[category]
                bndbox = get_and_check(obj,'bndbox', 1)
                xmin = int(get_and_check(bndbox,'xmin', 1).text)-1
                ymin = int(get_and_check(bndbox,'ymin', 1).text)-1
                xmax = int(get_and_check(bndbox,'xmax', 1).text)
                ymax = int(get_and_check(bndbox,'ymax', 1).text)
                xmin, ymin, xmax, ymax = resize(idx,img_dir,xmin,ymin,xmax,ymax)
                assert(xmax> xmin)
                assert(ymax> ymin)
                o_width = abs(xmax-xmin)
                o_height = abs(ymax-ymin)
                ann = {'image_id':
                    image_id,'bbox':[xmin, ymin, o_width, o_height],
                    'category_id': category_id,'id': bnd_id,}
                json_dict['annotations'].append(ann)
                bnd_id = bnd_id + 1
        idx+=1

    for cate, cid in categories.items():
        cat = {'supercategory':'none','id': cid,'name': cate}
        json_dict['categories'].append(cat)
    json_fp = open(json_file,'w')
    json_str = json.dumps(json_dict)
    json_fp.write(json_str)
    json_fp.close()


if __name__ =='__main__':
    if len(sys.argv) <= 3:
        print('3 auguments are need.')
        print('Usage: %s IMG_DIR XML_DIR OUTPU_JSON.json'%(sys.argv[0]))
        exit(1)

    convert(sys.argv[1], sys.argv[2], sys.argv[3])
