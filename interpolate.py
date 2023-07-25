import numpy
import scipy
import argparse
import pandas
import matplotlib.pyplot as plt
from typing import Union



class OutOfRangeError(Exception):
    pass

FloatList = list[float]

def interpolate(manual_input, auto_input, frame_time:Union[float, FloatList], plot=False):

    if isinstance(frame_time, float) or isinstance(frame_time, int):
        frame_time = [frame_time]
    elif isinstance(frame_time, list):
        frame_time = [float(time) for time in frame_time]
    else:
        frame_time = [float(frame_time)]

    # Read in the blood data
    if manual_input:
        manual_blood_data = pandas.read_csv(manual_input, delimiter='\t')
    else:
        manual_blood_data = pandas.DataFrame({'time': [], 'whole_blood_radioactivity': []})   
    if auto_input:
        auto_blood_data = pandas.read_csv(auto_input, delimiter='\t')
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
    interpolate = scipy.interpolate.Akima1DInterpolator(time_curve, whole_blood_radioactivity, axis=0)

    # return a point along the curve at the frame time
    interpolated_points = []
    for time in frame_time:
        try:
            if float(time) >= min(time_curve) and float(time) <= max(time_curve):
                interpolated_points.append(float(interpolate(float(time))))
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
    parser.add_argument('-a', '--auto-input', help='Auto sampled input file name', required=False)
    parser.add_argument('-t', '--frame-time', nargs='+', help='Frame time in seconds', required=True, type=float)
    parser.add_argument('-p', '--plot', help='plot out a figure of a smoothly interpolated activity curve', required=False, action='store_true', default=False)


    args = parser.parse_args()
    
    interpolated_points = interpolate(args.manual_input, args.auto_input, args.frame_time, args.plot)
    for point in interpolated_points:
        print(point)
