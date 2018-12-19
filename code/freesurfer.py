#!/usr/bin/env python3
from arcana import (
    MultiStudy, MultiStudyMetaClass, SubStudySpec)
from banana.study import (
    T1Study, T2Study)
import os
import os.path as op
import logging
from argparse import ArgumentParser
from arcana import (
    DirectoryRepository, LinearProcessor, StaticEnvironment,
    FilesetSelector, DEFAULT_PROV_IGNORE)
from arcana.utils import parse_value
from banana.file_format import nifti_gz_format

logger = logging.getLogger('arcana')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class FreesurferStudy(MultiStudy, metaclass=MultiStudyMetaClass):
    """
    An Study class to perform the analyses performed in the paper
    introducing Arcana. Requires a repository containing
    T1-weighted, T2*-weighted and diffusion MRI data.
    """

    add_sub_study_specs = [
        # Sub-study to process the T1-weighted data
        SubStudySpec(
            't1',
            T1Study,
            name_map={
                't2_coreg': 't2_coreg'}),
        SubStudySpec(
            't2',
            T2Study,
            name_map={
                'coreg_ref': 't1_magnitude'})]


# Set up parser to parse arguments passed to the script
parser = ArgumentParser(
    "A script to produce figures for the Arcana manuscript")
parser.add_argument('data_dir',
                    help="The directory containing repository")
parser.add_argument('--work_dir', help="The work directory",
                    default=op.join(op.expanduser('~'),
                                    'arcana-paper-work'))
args = parser.parse_args()


# Instantiate the ArcanaPaper class in order to apply it to a
# specific dataset
paper = FreesurferStudy(
    # Name for this analysis instance
    'fs',
    # Repository is a simple directory on the local file system
    repository=DirectoryRepository(args.data_dir),
    # Use a single process on the local system to derive
    processor=LinearProcessor(args.work_dir,
                              prov_ignore=DEFAULT_PROV_IGNORE + [
                                  '/workflow/.*'],
                              clean_work_dir_between_runs=False),
    # Use the static environment (i.e. no Modules)
    environment=StaticEnvironment(),
    # Match names in the data specification to filenames used
    # in the repository
    inputs=[
        FilesetSelector('t1_preproc', 't1_preproc', nifti_gz_format,
                        is_regex=True),
        FilesetSelector('t2_preproc', 't2_preproc', nifti_gz_format,
                        is_regex=True)],
        enforce_inputs=False)

print('Running freesurfer')
paper.data('t1_fs_recon_all')
print('Ran freesurfer')

    # Derive required data and display them in a single step for each
    # figure.
#     paper.vein_fig(op.join(args.fig_dir, 'veins.png'))
#     paper.fa_adc_fig(op.join(args.fig_dir, 'fa_adc.png'))
#     paper.tractography_fig(op.join(args.fig_dir, 'tractography.png'))
