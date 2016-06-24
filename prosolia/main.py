#!/usr/bin/env python
#
# Copyright 2016 Mathieu Bernard
#
# You can redistribute this file and/or modify it under the terms of
# the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import argparse
import configparser
import logging
import os
import sys
import scipy.io as sio

import prosolia.pipeline as pipeline
import prosolia.plot as plot


class CatchExceptions(object):
    """A decorator wrapping 'function' in a try/except block

    When an exception occurs, display a user friendly message before
    exiting.

    """
    def __init__(self, function):
        self.function = function

    def _exit(self, msg):
        sys.stderr.write(msg + '\n')
        sys.exit(1)

    def __call__(self):
        try:
            self.function()

        except (IOError, OSError, RuntimeError, AssertionError) as err:
            self._exit('fatal error: {}'.format(err))

        except KeyboardInterrupt:
            self._exit('keyboard interruption, exiting')


def parse_args(argv=sys.argv[1:]):
    """Return parsed arguments from command-line"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Extract pitch, probability of voicing and '
        'frequency-band energy modulation from a wav file')

    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help='display log messages to stdout')

    parser.add_argument(
        '-c', '--config', type=str, metavar='<file.cfg>', required=True,
        help='configuration file to load')

    parser.add_argument(
        '-p', '--plot', action='store_true',
        help='display the pipeline result in a figure')

    parser.add_argument(
        '-o', '--output', metavar='<file.mat>', default=None,
        help='optional .mat output file')

    parser.add_argument(
        'wav', nargs=1,
        help='input wav file')

    args = parser.parse_args(argv)
    args.wav = args.wav[0]
    args.output = (os.path.splitext(args.wav)[0] + '.mat'
                   if args.output is None else args.output[0])
    return args


@CatchExceptions
def main(argv=sys.argv[1:]):
    """Entry point of the program when used from command-line"""
    # parse the input arguments and load configuration
    args = parse_args(argv)
    config = configparser.ConfigParser()
    config._interpolation = configparser.ExtendedInterpolation()
    config.read(args.config)

    # setup the log
    log = logging.getLogger('prosolia')
    log.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    log.addHandler(logging.StreamHandler(sys.stdout))

    # load the input audio file
    audio, sample_frequency = pipeline.load_audio(args.wav)

    # compute filterbank energy
    energy, center_frequencies = pipeline.apply_gammatone(
        audio, sample_frequency,
        nb_channels=config.getint('filterbank', 'nb_channels'),
        low_cf=config.getfloat('filterbank', 'low_frequency'),
        window_time=config.getfloat('energy', 'window_time'),
        overlap_time=eval(config.get('energy', 'overlap_time')),
        compression=config.get('energy', 'compression'))

    # compute delta and delta-delta from energy
    # TODO delta, delta_delta = pipeline.apply_delta(energy)

    # compute DCT on energy
    dct = pipeline.apply_dct(
        energy,
        norm=config.get('dct', 'normalize'),
        size=config.getint('dct', 'size'))

    # compute pitch and probability of voicing
    pov, pitch = pipeline.apply_pitch(
        config['pitch']['kaldi_root'], args.wav, sample_frequency)

    # save results
    if args.verbose:
        print('saving to {}'.format(args.output))
    sio.savemat(args.output, {
        'wav': args.wav,
        'config': config,
        'sample_frequency': sample_frequency,
        'center_frequencies': center_frequencies,
        'energy': energy,
        'dct': dct,
        'pitch': pitch,
        'pov': pov})

    if args.plot:
        if args.verbose:
            print('plotting...')
        plot.plot_pipeline(
            sample_frequency,
            config.getfloat('filterbank', 'low_frequency'),
            audio, energy, dct, pov, pitch)

if __name__ == '__main__':
    main()
