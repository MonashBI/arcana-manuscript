#!/usr/bin/env python3
import os.path as op
from arcana import (
    FilesetInput, FieldInput, XnatRepo, SlurmProc, ModulesEnv)
from .example_study import ExampleStudy
from banana.file_format import dicom_format
from myproj.requirements import package1_req

# Create study object that accesses an XNAT repository
# and submits jobs to a SLURM scheduler
study = ExampleStudy(
    # Give a name to this analysis to
    # differentiate it from other analyses
    # performed on the same data
    name='example',
    # Set up connection to XNAT repository
    repository=XnatRepo(
        project_id='SAMPLE_PROJECT',
        server='https://central.xnat.org',
        cache_dir=op.expanduser('~/xnat-cache')),
    # Specify the use the SLURM scheduler to submit
    # nodes as jobs using Nipype's SlurmGraphPlugin
    processor=SlurmProc(
        work_dir=op.expanduser('~/work')),
    # Specify the use of environment modules to
    # satisfy software requirements. Non-standard
    # package names explicitly mapped to approp. reqs.
    environment=ModulesEnv(
        packages_map={
            package1_req: 'Package1_Parallel'}),
    # Link files and fields in the repository
    # to entries in the data specification
    inputs={
        'acquired1_file': FilesetInput(pattern='.*mprage.*',
                                       dicom_format),
        'acquired_file2': FilesetInput('SWI_Images',
                                       dicom_format),
        'acquired_field1': FieldInput('YOB', int,
                                      frequency='per_subject'),
        'acquired_field2': FieldInput('weight', float)},
    # Specify parameters specific to this
    # analysis
    parameters={'parameter1': 55.0,
                'pipeline_tool': 'toolB'})

# Generate whole brain tracks and return path to
# a cached dataset
derived5 = study.data('whole_brain_tracks')
print("The \"derived5\" fileset for the 'SECOND' visit "
      "of subject 'PILOT1' was produced at:\n{}"
      .format(derived5.path(subject_id='PILOT1',
                            visit_id='SECOND')))
