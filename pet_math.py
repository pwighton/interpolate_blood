import numpy
import scipy
import argparse
import pandas
import matplotlib.pyplot as plt


parser = argparse.ArgumentParser(description='Returns a point along a curve fitted to the inputs from a blood tsv, used to' 
                                 'match blood activity to frame timing of a pet scan.')

parser.add_argument('-m', '--manual-input', help='Manually sampled input file name', required=True)
parser.add_argument('-a', '--auto-input', help='Auto sampled input file name', required=False)
parser.add_argument('-t', '--frame-time', help='Frame time in seconds', required=True)

args = parser.parse_args()

# Read in the blood data
manual_blood_data = pandas.read_csv(args.manual_input, delimiter='\t')
auto_blood_data = pandas.read_csv(args.auto_input, delimiter='\t')

# combine whole blood data from manual and auto files into one dataframe
# pandas deprecates stuff like append so we're just going to use lists from here on out

auto_blood_time = auto_blood_data.time.tolist()
auto_whole_blood_radioactivity = auto_blood_data.whole_blood_radioactivity.tolist()


# collect the time curve into a list
time_curve = manual_blood_data.time.tolist()
whole_blood_radioactivity = manual_blood_data.whole_blood_radioactivity.tolist()
plasma_radioactivity = manual_blood_data.plasma_radioactivity.tolist()

if len(auto_blood_time) == len(auto_whole_blood_radioactivity) and len(auto_blood_time) > 0:
    time_curve.extend(auto_blood_time)
    whole_blood_radioactivity.extend(auto_whole_blood_radioactivity)

# create a pandas dataframe and sort by time
blood_data = pandas.DataFrame({'time': time_curve, 'whole_blood_radioactivity': whole_blood_radioactivity})
blood_data.sort_values(by=['time'], inplace=True)

time_curve = blood_data.time.tolist()
whole_blood_radioactivity = blood_data.whole_blood_radioactivity.tolist()

# interpolate the data
# scipy.interpolate.Akima1DInterpolator(x, y, axis=0)
interpolate = scipy.interpolate.Akima1DInterpolator(time_curve, whole_blood_radioactivity, axis=0)

# make a smooth curve from an expanded set of timepoints
more_time = numpy.linspace(min(time_curve), max(time_curve), num=1000, endpoint=True, retstep=False, dtype=None)
interpolated_curve = interpolate(more_time)

# print the original data against the interpolated curve
#plt.plot(time_curve, whole_blood_radioactivity, 'o') 
plt.plot(more_time, interpolated_curve, '-')
plt.show()