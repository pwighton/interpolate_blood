#!/usr/bin/env python3

import numpy
import scipy
import argparse
import json
import pandas
import matplotlib.pyplot as plt
from typing import Union



class OutOfRangeError(Exception):
    pass

FloatList = list[float]

def interpolate(manual_input, auto_input, frame_time_start:Union[float, FloatList], frame_duration:Union[float, FloatList],plot=False):

    if isinstance(frame_time_start, float) or isinstance(frame_time_start, int):
        frame_time_start = [frame_time_start]
    elif isinstance(frame_time_start, list):
        frame_time_start = [float(time) for time in frame_time_start]
    else:
        frame_time_start = [float(frame_time_start)]

    if isinstance(frame_duration, float) or isinstance(frame_duration, int):
        frame_duration = [frame_duration]
    elif isinstance(frame_duration, list):
        frame_duration = [float(time) for time in frame_duration]
    else:
        frame_duration = [float(frame_duration)]


    # PW: compatibility with `PS13_Subjects_10_kBq`
    rename_dict={
      'time[seconds]':'time',
      'Parent[Bq/mL]':'whole_blood_radioactivity'
    }
    
    # Read in the blood data
    if manual_input:
        manual_blood_data = pandas.read_csv(manual_input, delimiter='\t')
        manual_blood_data.rename(columns=rename_dict, inplace=True)
    else:
        manual_blood_data = pandas.DataFrame({'time': [], 'whole_blood_radioactivity': []})   
    if auto_input:
        auto_blood_data = pandas.read_csv(auto_input, delimiter='\t').rename(rename_dict)
        auto_blood_data.rename(columns=rename_dict, inplace=True)
    else:
        auto_blood_data = pandas.DataFrame({'time': [], 'whole_blood_radioactivity': []})

    # combine whole blood data from manual and auto files into one dataframe
    # pandas deprecates stuff like append so we're just going to use lists from here on out
    auto_blood_time = auto_blood_data.time.tolist()
    auto_whole_blood_radioactivity = auto_blood_data.whole_blood_radioactivity.tolist()

    # collect the time curve into a list
    time_curve = manual_blood_data.time.tolist()
    whole_blood_radioactivity = manual_blood_data.whole_blood_radioactivity.tolist()

    if len(auto_blood_time) == len(auto_whole_blood_radioactivity) and len(auto_blood_time) > 0:
        time_curve.extend(auto_blood_time)
        whole_blood_radioactivity.extend(auto_whole_blood_radioactivity)

    # create a pandas dataframe and sort by time
    blood_data = pandas.DataFrame({'time': time_curve, 'whole_blood_radioactivity': whole_blood_radioactivity}).dropna()
    blood_data.sort_values(by=['time'], inplace=True)

    time_curve = blood_data.time.tolist()
    whole_blood_radioactivity = blood_data.whole_blood_radioactivity.tolist()

    # interpolate the data
    # scipy.interpolate.Akima1DInterpolator(x, y, axis=0)
    #interpolate_fn = scipy.interpolate.Akima1DInterpolator(time_curve, whole_blood_radioactivity, axis=0)

    # PW 2024/09/12
    interpolate_fn = scipy.interpolate.interp1d(time_curve, whole_blood_radioactivity, axis=0)

    # return a point along the curve at the frame time
    interpolated_points = []
    for time in frame_time_start:
        try:
            if float(time) >= min(time_curve) and float(time) <= max(time_curve):
                interpolated_points.append(float(interpolate_fn(float(time))))
            else:
                raise OutOfRangeError(f"Frame time {time} is out of range: min: {min(time_curve)} max: {max(time_curve)} found in file(s) {auto_input} {manual_input} )")
        except OutOfRangeError as e:
            print(e)

    return interpolated_points

    if plot:
        # make a smooth curve from an expanded set of timepoints
        more_time = numpy.linspace(min(time_curve), max(time_curve), num=1000, endpoint=True, retstep=False, dtype=None)
        interpolated_curve = interpolate(more_time)

        # print the original data against the interpolated curve
        plt.plot(time_curve, whole_blood_radioactivity, 'o') 
        plt.plot(more_time, interpolated_curve, '-')
        plt.show()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Returns a point along a curve fitted to the inputs from a blood tsv, used to' 
                                    'match blood activity to frame timing of a pet scan.')

    parser.add_argument('-m', '--manual-input', help='Manually sampled input file name', required=True)
    parser.add_argument('-b', '--bids', help='BIDS sidecar file to PET data; expecting to find FrameTimesStart and FrameDuration', required=True)
    parser.add_argument('-a', '--auto-input', help='Auto sampled input file name', required=False)
    #parser.add_argument('-t', '--frame-time', nargs='+', help='Frame time in seconds', required=True, type=float)
    parser.add_argument('-p', '--plot', help='plot out a figure of a smoothly interpolated activity curve', required=False, action='store_true', default=False)


    args = parser.parse_args()
    
    with open(args.bids) as bids_sidecar_file:
      bids_sidecar_filedata = bids_sidecar_file.read()
    bids_sidecar = json.loads(bids_sidecar_filedata)
    
    frame_time_start = bids_sidecar["FrameTimesStart"]
    frame_duration = bids_sidecar["FrameDuration"]
    
    interpolated_points = interpolate(args.manual_input, args.auto_input, frame_time_start, frame_duration, args.plot)
    for point in interpolated_points:
        print(point)
