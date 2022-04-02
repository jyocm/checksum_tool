#!/usr/bin/env python3

import os
import argparse
import hashlib
import sys

#TODO add flag to either create checksums or to only list folders missing checksums at the end

parser = argparse.ArgumentParser()

parser.add_argument('--input', '-i', action='store', dest='input_path', type=str, help='full path to input folder')
parser.add_argument('--output', '-o', action='store', dest='output_path', type=str, help='full path to output text file')
parser.add_argument('--filter_list', action='store', dest='filter_list', type=str, help='Pull list of folders to process from a text file')
parser.add_argument('--skip_verify', '-s', action='store_true', dest='skip', help='Only generate checksums. Do not verify.')
parser.add_argument('--generate', '-g', action='store_true', dest='generate', help='Generate checksums in folders that do not have md5 files')


args = parser.parse_args()

def input_check():
    '''Checks if input was provided and if it is a directory that exists'''
    if args.input_path:
        indir = args.input_path
    else:
        print ("No input provided")
        quit()
    return indir

def get_immediate_subdirectories(folder):
    '''
    get list of immediate subdirectories of input
    '''
    return [name for name in os.listdir(folder)
        if os.path.isdir(os.path.join(folder, name))]

def filter_subdirectories(title_list):
    with open(args.filter_list) as f:
        filter_list = set(line.rstrip() for line in f)
    title_list = [item for item in title_list if item in filter_list]
    return title_list

def generate_checksums(filename, checksum_type):
    '''Uses hashlib to return an MD5 checksum of an input filename'''
    read_size = 0
    last_percent_done = 0
    method_to_call = getattr(hashlib, checksum_type)
    chksm = method_to_call()
    total_size = os.path.getsize(filename)
    with open(filename, 'rb') as f:
        while True:
            #2**20 is for reading the file in 1 MiB chunks
            buf = f.read(2**20)
            if not buf:
                break
            read_size += len(buf)
            chksm.update(buf)
            percent_done = 100 * read_size / total_size
            if percent_done > last_percent_done:
                sys.stdout.write('[%d%%]\r' % percent_done)
                sys.stdout.flush()
                last_percent_done = percent_done
        #print()
    checksum_output = chksm.hexdigest()
    return checksum_output
'''
def load_checksum_value(checksum_file):
    with open(checksum_file) as f:
        content = f.readlines()
    content = [line.rstrip('\n') for line in content]
    for value in content:
        if '*' in value:
            checksum_filename = value.split('*')[1]
        else:
            checksum_filename = value.split('  ')[1]
        checksum_value = value.split(' ')[0]
        checksum_value = checksum_value.lower()
    return checksum_filename, checksum_value
'''
def calculate_checksum_value(file_abspath, checksum_value):
    rel_file = os.path.basename(os.path.normpath(file_abspath))
    if os.path.isfile(file_abspath):
        calculated_checksum = generate_checksums(file_abspath, 'md5')
        if calculated_checksum == checksum_value:
            checksum_result = 'PASS'
        else:
            checksum_result = 'FAIL'
        print(rel_file + ':', checksum_result)
    else:
        checksum_result = 'FILE NOT FOUND'
        print (rel_file + ':', checksum_result)
    if args.output_path:
        with open(args.output_path, "a", newline='\n') as outfile:
            #print(i, file=outfile)
            print('\t', rel_file + ':', checksum_result, file=outfile)

def output_check():
    '''Checks that output is valid'''
    output = args.output_path
    if not output.endswith('.txt'):
        print("\n--- ERROR: Output must be a .txt file ---\n")
        quit()
    #print("Checking output path")
    try:
        with open(output, 'w', newline='\n') as outfile:
            outfile.close
    except OSError:
        print("\n--- ERROR: Unable to create output file", output + ' ---\n')
        quit()

indir = input_check()
base_folder_list = get_immediate_subdirectories(indir)
if args.filter_list:
    base_folder_list = filter_subdirectories(base_folder_list)
missing_checksums = []
for i in base_folder_list:
    if args.output_path:
        with open(args.output_path, "a", newline='\n') as outfile:
            print(i, file=outfile)
    for subdir, dirs, files in os.walk(indir):
        if files:
            checksum_file_list = [file for file in files if file.endswith(".md5")]
            if not checksum_file_list:
                print(subdir + " does not contain checksum files")
                missing_checksums.append(subdir)
                if args.generate:
                    for file in files:
                        fpath = os.path.join(indir, subdir, file)
                        md5path = os.path.join(indir, subdir, 'checksum.md5')
                        filehash = generate_checksums(fpath, 'md5')
                        with open (md5path, 'a',  newline='\n') as f:
                            print(filehash, '*' + file, file=f)
            else:
                if not args.skip:
                    #TODO count checksum_file_list and warn if multiple checksum files are found
                    for i in checksum_file_list:
                        checksum_abspath = os.path.join(indir, subdir, i)
                        with open(checksum_abspath) as f:
                            content = f.readlines()
                        #skip empty lines
                        content = [line for line in content if line.strip()]
                        #skip lines starting with #
                        content = [line for line in content if not line.startswith('#')]
                        #remove eol characters
                        content = [line.rstrip('\n') for line in content]
                        for value in content:
                            if '*' in value:
                                checksum_filename = value.split('*')[1]
                            else:
                                checksum_filename = value.split('  ')[1]
                            checksum_value = value.split(' ')[0]
                            checksum_value = checksum_value.lower()
                            file_abspath = os.path.join(indir, subdir, checksum_filename)
                            calculate_checksum_value(file_abspath, checksum_value)
        elif dirs:
            print(subdir + " only contains folders")
        else:
            print(subdir + " is empty")
if args.output_path and missing_checksums:
    with open(args.output_path, "a", newline='\n') as outfile:
        print("Folders missing checksum files", file=outfile)
    for i in missing_checksums:
        with open(args.output_path, "a", newline='\n') as outfile:
            #print(i, file=outfile)
            print('\t', i, file=outfile)
#print("Folders missing checksum files: " + str(missing_checksums))
