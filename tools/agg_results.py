#! /usr/bin/env python

import sys
import os
import argparse
import time
from collections import defaultdict

if __name__ == '__main__':
    '''Recursively search for pisc output files and aggregate into one.'''

    parser = argparse.ArgumentParser(description='Recursively search for pisc output files and aggregate into one.')
    parser.add_argument('input_directory', help='Where to recursively search for files.')
    args = parser.parse_args()
    
    # Convert command line arguments
    input_directory = args.input_directory
    
    if not os.path.exists(input_directory):
        print "Directory does not exist: {0}".format(input_directory)
        sys.exit(1)
        
    # Get list of image file paths to rename.
    pisc_filepaths_by_type = defaultdict(list)
    for (dirpath, dirnames, filenames) in os.walk(input_directory):
        if 'combined' in dirpath:
            continue # don't combine already combined results
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if filename == 'pisc.log':
                pisc_filepaths_by_type['log'].append(filepath)
                continue
            just_filename = os.path.splitext(filename)[0]
            filename_parts = just_filename.split('_')
            if len(filename_parts) < 3:
                print 'Skipping {} due to wrong file name format'.format(filepath)
                continue
            timstamp = filename_parts[-1]
            sensor_id = filename_parts[-2]
            sensor_name = '_'.join(filename_parts[:-2])
            pisc_filepaths_by_type["{}_{}".format(sensor_name, sensor_id)].append(filepath)
    
    print "Found {} unique sensor types".format(len(pisc_filepaths_by_type))
    
    output_directory = os.path.join(input_directory, 'combined_{}/'.format(time.strftime("%Y%m%d-%H%M%S")))
    
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
 
    print "Output combined results to {}".format(output_directory)
 
    for file_type, filepaths in pisc_filepaths_by_type.iteritems():
        print "{} files with type {}".format(len(filepaths), file_type)
        
        extension = os.path.splitext(filepaths[0])[1]
        
        output_filename = "{}_combined{}".format(file_type, extension)
        output_filepath = os.path.join(output_directory, output_filename)
        
        with open(output_filepath, 'w') as out_file:
            for filepath in filepaths:
                with open(filepath, 'r') as pisc_file:
                    for line in pisc_file:
                        out_file.write(line)
                        
        #print "Combined files to {}".format(output_filename)
    