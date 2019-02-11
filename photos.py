#!/usr/bin/env python

"""
Organize the family photos and videos. Initially used to aggregate the 60,000+
photos and videos we had stored in hundreds of directories across multiple drives
on multiple devices. The goal was to get all photos in one directory organized by
year and month and to filter out unwanted files. That makes it easy to 
synchronize with our AWS S3 bucket which we use for backup. 

Anytime someone exports media from a device or downloads it from another source,
we run this script to organize it in the central location. 
"""

import argparse
import json
import os
import shutil
import time
from PIL import Image

__author__ = 'Adam "Bread" Slesinger'
__version__ = '1.0'

log_file = None

def process_args():
    """
    Parses command line arguments.
    """    
    description = 'Photo Organizer, version {0}'.format(__version__)
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--source', dest='source_dir', default='.', help='source directory')                
    parser.add_argument(
        '--dest', dest='dest_dir', default='E:\\Media', help='destination directory')                        
    return parser.parse_args()


def get_best_date(full_path):
    """
    Get the date that most accurately represents when a photo was taken. If the
    proper Exif tag for generated date/time exits, we trust it. If it doesn't
    exist, pick the crated or modified file date, whichever is earlier. 
    """      
    info = None
    exif = False    
    try:
        im = Image.open(full_path)
        info = im._getexif()
    except:
        # Give up on any error.
        pass
    if info and 36867 in info:
        best_date = info[36867]
        exif = True        
    else:
        created_date = os.path.getctime(full_path)
        modified_date = os.path.getmtime(full_path)
        ctime = modified_date if modified_date < created_date else created_date
        best_date = time.strftime('%Y:%m:%d %I:%M:%S', time.localtime(ctime))
    return best_date, exif


def create_dir(args, date_string, media_dir):
    """
    Creates a directory based on a datetime string and provided subdirectory.
    For example a datetime string "2017:06:19 12:26:16" and subdirectory
    "Pictures" will create "E:\\Media\\Pictures\\2017\\2017-06"
    """
    base_dir = args.dest_dir
    parts = date_string.split(":")
    new_dir = os.path.join(base_dir, media_dir, parts[0], parts[0] + "-" + parts[1])
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    return new_dir


def copy_file(source_dir, source_file_name, dest_dir):
    """
    Copies a file from the source to the destination directory, 
    taking care to not overwrite files.
    """
    source_full_path = os.path.join(source_dir, source_file_name)
    dest_full_path = os.path.join(dest_dir, source_file_name)
    append = 0
    while os.path.exists(dest_full_path):
        append += 1
        name_parts = source_file_name.split('.')
        name_parts[0] += "-" + str(append)
        new_name = '.'.join(name_parts)
        dest_full_path = os.path.join(dest_dir, new_name)
    # copy2 will attempt to preserve meta data which is important
    # since we don't want to overwrite created or modified date
    shutil.copy2(source_full_path, dest_full_path)
    return new_name if append > 0 else None


def log(message):
    """
    Log a message to the screen and to a log file.
    """
    print(message)
    global log_file
    log_file.write(message + "\n")
    

def main():
    """
    Process command line arguments and kick off the process.
    """
    global log_file
    start_time = time.time() 
    args = process_args()
    
    total_files = 0
    ignored_files = 0
    total_exif = 0
    total_photos = 0
    total_videos = 0
    file_exts = {}
    photo_exts = ['.jpg', '.png', '.jpeg', '.tiff', '.tif', '.bmp', '.gif', '.crw']
    video_exts = ['.mov', '.mp4', '.m4v', '.mpg', '.mpeg', '.ogv', '.flv', '.avi', '.wmv', '.webm']
    ignore_files = ['Thumbs.db', '.DS_Store', 'desktop.ini']
    
    log_file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), "log.txt")
    if os.path.exists(log_file_name):
        os.remove(log_file_name)
    log_file = open(log_file_name, "a")

    for root, dirs, files in os.walk(args.source_dir):
        for name in files:
            total_files += 1
            full_path = os.path.join(root, name)        
            file_name, file_ext = os.path.splitext(full_path)
            file_ext = file_ext.lower() 
            if file_ext in file_exts:
                file_exts[file_ext] += 1
            else:
                file_exts[file_ext] = 1    
            best_date, had_exif = get_best_date(full_path)
            if had_exif:
                total_exif += 1
            log(('(Exif) ' if had_exif else '') + best_date + " " + full_path)
            if file_ext in photo_exts:
                media_dir = 'Pictures'
                total_photos += 1   
            elif file_ext in video_exts:
                media_dir = 'Videos'
                total_videos += 1
            else:
                media_dir = 'Other'
            if name not in ignore_files:
                created_dir = create_dir(args, best_date, media_dir)            
                new_name = copy_file(root, name, created_dir)
                if new_name:
                    log("Renamed {0} to {1}".format(name, new_name))
            else:
                ignored_files += 1

    log('')
    log('Total files: {0:,}'.format(total_files))
    log('Total ignored files: {0:,}'.format(ignored_files))
    log('Total photo files: {0:,}'.format(total_photos))
    log('Total video files: {0:,}'.format(total_videos))
    log('Total files with exif data: {0:,}'.format(total_exif))
    log(json.dumps(file_exts))
    log('Total running time: %.2f seconds' % (time.time() - start_time))

    log_file.close()


if __name__ == '__main__':
    main()

