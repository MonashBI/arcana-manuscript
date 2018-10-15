#!/usr/bin/env python3
import os.path as op
from arcana import (
    FilesetSelector, FieldSelector, XnatRepository,
    SlurmProcessor, ModulesEnvironment)
from .example_study import ExampleStudy
from nianalysis.file_format import dicom_format

# Create study object that accesses an XNAT repository
# and submits jobs to a SLURM scheduler
study = ExampleStudy(
    # Give a name to this analysis to
    # differentiate it from other analyses
    # performed on the same data
    name='example',
    # Set up connection to XNAT repository
    repository=XnatRepository(
        project_id='SAMPLE_PROJECT',
        server='https://central.xnat.org',
        cache_dir=op.expanduser('~/xnat-cache')),
    # Specify the use the SLURM scheduler to submit
    # nodes as jobs using Nipype's SlurmGraphPlugin
    processor=SlurmProcessor(
        work_dir=op.expanduser('~/work')),
    # Specify the use of environment modules to
    # satisfy software requirements. Non-standard
    # package names explicitly mapped to approp. reqs.
    environment=ModulesEnvironment(
        packages_map={
            'Package1_Parallel': package1_req}),
    # Link files and fields in the repository
    # to entries in the data specification
    inputs={
        'acquired1_file': FilesetSelector(
            '.*mprage.*', dicom_format, is_regex=True),
        'acquired_file2': FilesetSelector(
            'SWI_Images', dicom_format),
        'acquired_field1': FieldSelector(
            'YOB', int, frequency='per_subject'),
        'acquired_field2': FieldSelector(
            'weight', float)},
    # Specify parameters specific to this
    # analysis
    parameters={'parameter1': 55.0,
                'pipeline_tool': 'toolB'})

# Generate whole brain tracks and return path to
# a cached dataset
derived5 = study.data('whole_brain_tracks')
print("The \"derived5\" fileset for the second visit "
      "of subject 'PILOT1' were produced at:\n{}"
      .format(derived5.path(subject_id='PILOT1',
                            visit_id=1)))
