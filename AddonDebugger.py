#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The YSFlight Addon Diagnostic Utility will identify YSFlight Addons that may be causing errors
when you load YSFlight or at points while playing the game.
"""

# Import Standard Python Modules
import os


# Import 3rd Party Modules
# N/A


# Define support functions here
def import_file(filepath):
    """Import a text file assuming that the input filepath is real and a text file"""
    output = list()
    with open(filepath, mode='r') as txt_file:
        output = [i.strip() for i in txt_file.readlines()]
    return output

def write_csv(filepath, data):
    pass

def convert_speed(entry):
    units = ['MACH', 'KM/H', 'KT']
    factors = [340, 10/36, 1852/3600]
    
    entry = entry.upper()
    for unit, factor in zip(units, factors):
        if unit in entry:
            speed = entry.split(unit)[0]
            return float(speed) * factor
    return 0
            


# Define test Folderpath
ysflight_folderpath = os.path.join(os.getcwd(), 'Majorpack2_20110425')


ysf_version = 20150425

# Define filetypes that we have tests for.
filetypes_to_test = ['.lst', '.dat'] #, '.dnm', '.fld', '.acp']

# Walk through the folderpath provided and find all of the files that we
# have addon debugging tests for.
analysis_filepaths = list()
all_filepaths = list()
all_filenames = list()
for path, folders, files in os.walk(ysflight_folderpath):
    for filename in files:
        if os.path.splitext(filename)[-1] in filetypes_to_test:
            analysis_filepaths.append(os.path.join(path, filename))
        all_filenames.append(filename)
        all_filepaths = os.path.join(path, filename)

errors = list()   # List to store errors with [filename, error, relative_filepath, line, sugested line]

# Perform .lst file tests
max_lst_elements = {'air':5, 'gro':5, 'sce':4}
allowed_lst_filetypes = {'air':[['dat'], ['srf', 'dnm'], ['srf'], ['srf'], ['srf']],
                         'gro':[['dat'], ['srf', 'dnm'], ['srf'], ['srf'], ['srf']],
                         'sce':[['n/a'], ['fld'], ['stp'], ['yfs']]
                         }
if ysf_version > 20150000:
    allowed_lst_filetypes['gro'][-1].append('dnm')
    allowed_lst_filetypes['air'][-1].append('dnm')
    
lst_filepaths = [i for i in analysis_filepaths if i.lower().endswith(".lst")]
for filepath in lst_filepaths:
    # Import the lst file
    lst_file = import_file(filepath)
    
    # Get info from the lst filepath
    filename = os.path.basename(filepath)
    print(filename)
    lst_filetype = filename[:3].lower()
    relative_path = os.path.relpath(filepath, ysflight_folderpath)
    
    #
    # Perform intial checks on the lst file location and name
    #
    
    # Make sure the lst file starts with the correct characters for a valid file
    valid_filename_error = False
    if lst_filetype not in ['sce', 'air', 'gro']:
        valid_filename_error = True
        errors.append([filename, 'Invalid LST Filename', relative_path, 'LST filename started with: "{}"'.format(lst_filetype), 'Valid LST filenames start with "air", "gro", or "sce".'])
    
    # Make sure that the lst file is in the program-level correct aircraft, ground, or scenery folder
    lst_folder_error = not relative_path.lower().startswith(lst_filetype)
    if lst_folder_error:
        errors.append([filename, 'LST File Not In Correct Folder', relative_path, 'LST file found in a non-ysflight level folder.', 'All LST files should be in the YSFLIGHT/aircraft, YSFLIGHT/ground, or YSFLIGHT/scenery folders.'])
        
    #
    # Perform checks on the contents of the lst file
    #
    
    # initialize error checks
    lst_slash_error = False
    lst_filepath_separator_count = 0
    lst_invalid_filepath_error = False    
    valid_lst_line_length = 10
    lst_space_in_paths = False
    lst_invalid_filetype_by_position = False
    
    # Iterate over all the rows and check each line for issues.
    for idx, line in enumerate(lst_file):
        
        # Don't analyze lst file lines that are blank or have insufficient data to be a real LST definition line.
        if len(line) < valid_lst_line_length:
            continue
                
        # Check to see if the proper filepath separator was used.
        if "/" not in line and '\\' in line:  # Need \\ because a single \ is the escape character
            lst_slash_error = True
            lst_filepath_separator_count += 1
    
        # Check each path in the lst line to see if the file is located (case sensitive) at the location specified.
        paths = line.split()  # Defaults to whitespace delimiter
        for path_idx, path in enumerate(paths):
            path = path.replace('"', '')  # Remove the quotation marks around some paths in lst files
            
            if len(path) < 1:  
                # Skip entries that are placeholders for expected filetypes
                continue
            
            if path_idx == 0 and lst_filetype == 'sce':
                # Skip the Map name in Scenery LST Files
                continue
                
            if os.path.isfile(os.path.join(ysflight_folderpath, path)) is False:
                lst_invalid_filepath_error = True
                name = os.path.basename(path)
                possible_filepaths = [i for i in all_filepaths if os.path.basename(i) == name]
                
                msg = 'Ensure {} is a valid path.'.format(path)
                if len(possible_filepaths) > 0:
                    msg += ' Possible files at: '
                    for possible_path in possible_filepaths:
                        msg += ' {},'.format(os.path.relpath(possible_path, ysflight_folderpath))
                    msg = msg[:-1]
                else:
                    msg += " Unable to find any files with the same name."
                errors.append([filename, 'Invalid LST Filepath', relative_path, line,  msg])
            
        # Check to see if the filetype defined in each position is valid for the position of the type of lst file.
        if path[-3:].lower() not in allowed_lst_filetypes[lst_filetype][path_idx]:
            lst_invalid_filetype_by_position = True
            errors.append([filename, 'Invalid Filetype by LST Position', relative_path,  ])
            
        # Check to make sure that we don't have spaces in the filepaths or more than the max number of filepaths allowed
        if len(paths) > max_lst_elements[lst_filetype]:
            # We have a space in at least one filepath which is not allowed.
            lst_space_in_paths = True
            errors.append([filename, 'Space in Filepath or Too Many LST rRw Elements', relative_path, 'Found more than 5 elements in lst file row {}'.format(idx + 1), 'LST files contain no more than {} elements in {} lst files'.format(max_lst_elements[lst_filetype], lst_filetype.upper())])
                    
    # Write error logs based on whole-file results           
    if lst_slash_error:
        errors.append([filename, 'Invalid Filepath Separator', relative_path, 'Found {} of {} lines with \ instead of / for filepath separator'.format(lst_filepath_separator_count, len([i for i in lst_file if len(i) > valid_lst_line_length])), 'Should use / for compatibility across all operating systems'])
        
    # Print Analysis Results for the file
    error_status = [lst_slash_error, lst_invalid_filepath_error, lst_space_in_paths, valid_filename_error, lst_invalid_filetype_by_position]
    notes = ["- Found invalid filepath separator", "- Found invalid filepath(s)", "- Found a space in a filepath", "- Found LST file in folder that doesn't match lst filename", "- Found invalid filetype in an lst entry position."]
    for error, note in zip(error_status, notes):
        if error:
            print(note)
    

        

dat_filepaths = [i for i in analysis_filepaths if i.lower().endswith(".dat")]
identify_lines = list()
for filepath in dat_filepaths:
    # Import the lst file
    dat_file = import_file(filepath)
    
    # Get info from the lst filepath
    filename = os.path.basename(filepath)
    lst_filetype = filename[:3].lower()
    relative_path = os.path.relpath(filepath, ysflight_folderpath)
    
    # initialize values
    identify = ""
    number_of_turrets = 0
    found_turret_ids = list()
    invalid_instrument_panel_path = False
    max_speed = 0
    cruise_speed = 0
    raw_max_speed = ""
    raw_cruise_speed = ""
    # Read thru the dat file and pull out lines of interest
    for line in dat_file:
    
        if line.startswith("IDENTIFY"):
            # Extract the identify line for later determination of duplicate identify lines.
            if '"' in line:
                identify = line.split('"')[1]
            else:
                identify = line.split()[1]
            identify_lines.append(identify)
            
        elif line.startswith("INSTPANL"):
            # Verify that the filepath is valid.
            inst_path = line.split()[1]
            if os.path.isfile(os.path.join(ysflight_folderpath, path)) is False:
                invalid_instrument_panel_path = True
                errors.append([filename, 'Invalid Instrument Panel Filepath', relative_path, line, 'Could not find the file.'])
            
        elif line.startswith("NMTURRET"):
            # Need to check that all of the number of the turrets is accurate.
            number_of_turrets = int(line.split()[1])
            
        elif line.startswith("TURRETPO"):
            found_turret_ids.append(int(line.split()[1]))
        
        elif line.startswith("WPNSHAPE"):
            wpn_shape_path = line.split()[3]
            if os.path.isfile(os.path.join(ysflight_folderpath, wpn_shape_path)) is False:
                errors.append([filename, 'Invalid Weapon Shape Filepath', relative_path, line, 'Could not find the file.'])
                
        elif line.startswith("MAXSPEED"):
            raw_max_speed = line
            max_speed = convert_speed(line.split()[1])
            
        elif line.startswith("REFVCRUS"):
            raw_cruise_speed = line
            cruise_speed = convert_speed(line.split()[1])
            
    # Check to see if we have all of the turrets
    if number_of_turrets != len(found_turret_ids):
        # We have a mismatch between the number of turrets expected and the number defined.
        errors.append([filename, 'Incorrect Number of Turrets', relative_path, 'Expected {} Turrets, Found {}'.format(number_of_turrets, len(found_turret_ids)), 'The NMTURRET value should be {}.'.format(len(found_turret_ids))])
    elif number_of_turrets > 0:
        # Don't want to raise errors when no turrets are defined.

        # Check to see if we valid turret IDs.
        found_turret_ids = sorted(found_turret_ids) # Sort assending
        for turret_id in range(0, number_of_turrets):
            if turret_id not in found_turret_ids:
                errors.append([filename, 'Invalid Turret ID', relative_path, 'No Turret ID #{} found.'.format(turret_id), 'The Turrets should have ID numbers between 0 and {}.'.format(number_of_turrets - 1)])
    
    # Check to see if the max speed is greater than the cruising speed
    if max_speed < cruise_speed:
        errors.append([filename, 'Cruise Speed Greater Than Max Speed', relative_path, '{}  {}'.format(raw_max_speed, raw_cruise_speed), 'Increase Max Speed or decrease Cruise Speed'])
            
    
# Test to see if we have duplicate identify names. Also need to check that there are not duplicates within the first 32 characters
first_32_identify = [i[:31] for i in identify_lines if len(i) > 32 else i]
for identify in identify_lines:
    if identify_lines.count(identify) > 1:
        # We have actual duplicates





# Write report to file


