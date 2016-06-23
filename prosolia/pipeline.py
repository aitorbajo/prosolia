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
"""Implementation of the prosolia pipeline"""

import os
import shlex
import shutil
import subprocess
import tempfile

import numpy as np


def load_audio(filename, dtype=np.float64):
    """Return audio data from a file

    The wav file is assumed to be mono.

    Parameters:
    -----------

    filename (string or openfile handle): input audio file

    dtype: output scalar type (default is numpy.float64)

    Returns:
    --------

    sample_frequency (int): sample frequency of the audio content in Hz

    data (dtype numpy array): data read from file

    """
    import soundfile
    return soundfile.read(filename, dtype=dtype)


def apply_gammatone(data, sample_frequency, nb_channels=20, low_cf=20,
                    window_time=0.5, overlap_time=0.1, compression=None):
    """Return the response of a gammatone filterbank to data

    Calculate a spectrogram-like time frequency magnitude array based
    on gammatone subband filters. The waveform ``data`` (at sample
    rate ``sample_frequency``) is passed through an multi-channel
    gammatone auditory model filterbank, with lowest frequency
    ``min_cf`` and highest frequency ``sample_frequency`` / 2. The
    outputs of each band then have their energy integrated over
    windows of ``window_time`` seconds, advancing by ``overlap_time``
    secs for successive columns. The energy is then optionally
    compressed by log10 or cuboc root. These magnitudes are returned
    as a nonnegative real matrix with ``nb_channels`` rows.

    Parameters:
    -----------

    data (float numpy array): 1D input data to be processed

    sample_frequency (int): sample frequency of the data in Hz

    nb_channels (int): number of frequency channels in the filterbank

    low_cf (float): lowest center frequency of the filterbank in Hz

    window_time (float): integration time of the window in seconds

    overlap_time (float): overlap time of two successive windows in seconds

    compression (string): compression method to use on energy, choose
        None to disable compression, 'log' for 20*np.log10(X) or
        'cubic' for X**(1/3). Default is None

    Returns:
    --------

    output (float numpy array): 2D filterbank response to the input
        data, where output.shape[0] (time axis) depends on the window
        time and output.shape[1] == nb_channels

    center_frequencies (float numpy array): center frequencies of each
        channel in Hz.

    """
    from gammatone.gtgram import gtgram
    from gammatone.filters import erb_space

    # get the filterbank output (with increasing frequencies)
    output = np.flipud(gtgram(
        data, sample_frequency, window_time,
        overlap_time, nb_channels, low_cf))

    # get the center frequencies in increasing order
    center_frequencies = erb_space(low_cf, sample_frequency/2, nb_channels)[::-1]

    # compress the output
    compress = {'log': lambda X: 20 * np.log10(X),
                'cubic': lambda X: X ** (1./3)}
    try:
        return compress[compression](output), center_frequencies
    except KeyError:
        return output, center_frequencies


def apply_dct(data, norm=None, n=8):
    """Return the `n` first coefficients of the `data` DCT

    Apply type 2 discrete cosine transfrom on the first axis of `data`
    (frequencies) over the second axis (time). Wrapper on
    scipy.fftpack.dct.

    Parameters:
    -----------

    data (2D numpy array): input array, first axis is frequency,
        second axis is time

    norm: if 'ortho', normalize the dct such that makes the
        corresponding matrix of coefficients orthonormal, default is
        None

    n (int): keep the n first coefficients of the output

    Return:
    -------

    dct_output: numpy array of shape (n, data.shape[1])

    """
    from scipy.fftpack import dct

    if norm is not 'ortho':
        norm = None

    return dct(data, type=2, axis=0, norm=norm)[:n, :]


def apply_pitch(kaldi_root, wavfile, sample_frequency, verbose=True):
    """Apply Kaldi pitch extractor on a wav file

    Output is 2-dimensional features consisting of (NCCF, pitch in
    Hz), where NCCF is between -1 and 1, and higher for voiced frames.

    Raise:
    ------

    AssertionError if compute-kaldi-pitch-feats executable is not
    found in the Kaldi tree

    RuntimeError if compute-kaldi-pitch-feats failed

    """
    # locate the kaldi executable we want
    kaldi_pitch = os.path.join(
        kaldi_root, 'src', 'featbin', 'compute-kaldi-pitch-feats')
    assert os.path.isfile(kaldi_pitch), '{} not found'.format(kaldi_pitch)

    try:
        # directory where kaldi read and write
        tempdir = tempfile.mkdtemp()

        # register wav input to kaldi
        scp = os.path.join(tempdir, 'wav.scp')
        with open(scp, 'w') as fscp:
            fscp.write('{} {}\n'.format(
                os.path.splitext(os.path.basename(wavfile))[0],
                os.path.abspath(wavfile)))

        # the kaldi pitch/pov output
        pitch = os.path.join(tempdir, 'pitch.txt')

        # the kaldi command to execute
        command = (kaldi_pitch + ' --sample-frequency={0} scp:{1} ark,t:{2}'
                   .format(sample_frequency, scp, pitch))

        # execute it in a kaldi environment
        stderr = None if verbose else open(os.devnull)
        job = subprocess.Popen(shlex.split(command), cwd=tempdir, stderr=stderr)
        job.wait()
        if job.returncode != 0:
            raise RuntimeError('command "{}" returned with {}'
                               .format(command, job.returncode))

        # return the result as two numpy vectors
        a = np.loadtxt(pitch, skiprows=1, usecols=(0, 1))
        return a[:, 0].T, a[:, 1].T

    finally:
        shutil.rmtree(tempdir)
