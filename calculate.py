from interpolate import interpolate
import argparse
from bids import BIDSLayout
import pandas
from pathlib import Path
import re

parser = argparse.ArgumentParser(description='Interpolate blood activity curves to match frame timing of PET images')
parser.add_argument('bidsdataset', help='Path to bids dataset')


# given a bids dataset containing pet images, we want to create a set of tsv files containing the interpolated blood
# activity curves matching the frame timing of the pet images. This is done by using the interpolate function from
# interpolate.py

def calculate_tacs_at_frametimes(bids_dataset_path: Path):
    # obtain the path to the bids dataset and load with pybids
    layout = BIDSLayout(bids_dataset_path)

    # collect all time activity curves from the dataset
    original_tacs = layout.get(suffix='blood', extension=['.tsv', '.json'])

    # collect subject id's where tacs exist
    subjects = []
    for tac in original_tacs:
        subjects.append(tac.entities['subject'])
    subjects = list(set(subjects))
    subjects.sort()
    print(f"Found the following subjects with blood time activity curves: {subjects}")

    # collect frame timing info from every subject that has a tac
    frame_times = {}
    for subject in subjects:
        pet_scans = layout.get(subject=subject, suffix='pet', extension=['.nii.gz', 'nii.gz'])
        for pet_scan in pet_scans:
            pet_scan_path = pet_scan.path
            metadata = pet_scan.get_metadata()
            session = pet_scan.get_entities().get('session')
            frame_times[subject] = frame_times.get(subject, {})

            if session:
                frame_times[subject]['Sessions'] = frame_times[subject].get('Sessions', {})
                frame_times[subject]['Sessions'][session] = {
                                            'Nifti': pet_scan_path,
                                            'SessionID': session,
                                            'FrameTimesStart': metadata['FrameTimesStart'], 
                                            'manual': {'.json': "", '.tsv': ""}, 
                                            'autosampler': {'.json': "", '.tsv': ""}
                                            }
            else:
                frame_times[subject] = {
                                        'Nifti': pet_scan_path,
                                        'FrameTimesStart': metadata['FrameTimesStart'], 
                                        'manual': {'.json': "", '.tsv': ""}, 
                                        'autosampler': {'.json': "", '.tsv': ""}
                                        }

    for tac in original_tacs:
        subject = tac.entities['subject']
        session = tac.entities['session']
        recording = tac.entities['recording']
        extension = tac.entities['extension']
        try:
            if session: 
                frame_times[subject]['Sessions'][session][recording][extension] = tac.path
            else:
                frame_times[subject][recording][extension] = tac.path
        except KeyError as err:
            print(err)

    # now that we've collected all the requisite files we can interpolate the blood activity curves at each frame position
    for subject, data in frame_times.items():
        if 'Sessions' in data.keys():
            for session, session_data in data['Sessions'].items():
                manual_tsv = session_data.get('manual', {}).get('.tsv', "")
                autosampler_tsv = session_data.get('autosampler', {}).get('.tsv', "")
                frame_start_times = session_data.get('FrameTimesStart', [])
                interpolated = interpolate(manual_input=manual_tsv, auto_input=autosampler_tsv, frame_time=frame_start_times)
                frame_times[subject]['Sessions'][session]['interpolated_tac'] = interpolated
        else:
            for recording, recording_data in data.items():
                for extension, path in recording_data.items():
                    if extension == '.tsv':
                        frame_times[subject][recording]['interpolated'] = interpolate(path, frame_times[subject]['FrameTimesStart'])

    # now that we've interpolated the blood activity curves we can write them to a tsv file
    for subject, data in frame_times.items():
        # start to construct an output path in the derivatives folder within the dataset
        output_path = bids_dataset_path / 'derivatives' / 'interpolated_tacs' / subject
        output_path.mkdir(parents=True, exist_ok=True)

        # iterate over sessions
        if data.get("Sessions"):
            for session, session_data in data['Sessions'].items():
                # create session folders
                session_output_path = output_path / session / 'pet'
                session_output_path.mkdir(parents=True, exist_ok=True)
                #for interpolated_tac in session_data.get('interpolated_tac', []):
                    # create a new tsv file for each interpolated tac
                tac_path = session_output_path / f"sub-{subject}_ses-{session}_desc-interpolatedtac_blood.tsv"
                with open(tac_path, 'w') as tac_file:
                    tac_file.write(f"FrameTimesStart\twhole_blood_radioactivity\n")
                    for time, radioactivity in zip(session_data['FrameTimesStart'], session_data['interpolated_tac']):
                        tac_file.write(f"{time}\t{radioactivity}\n")
        else:
            print("You need to add logic for sessionless data here")
        # check to see if both manual and autosampler are present



if __name__ == '__main__':
    args = parser.parse_args()
    calculate_tacs_at_frametimes(Path(args.bidsdataset))