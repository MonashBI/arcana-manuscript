import os
from arcana import (
    Study, StudyMetaClass, AcquiredFilesetSpec, FilesetSpec,
    AcquiredFieldSpec, FieldSpec, ParameterSpec, SwitchSpec,
    FilesetSelector, XnatRepository)
from nianalysis.file_format import (
    nifti_gz_format, dicom_format, nifti_format, analyze_format,
    gif_format, text_format, text_mat_format)

STD_IMAGE_FORMATS = (dicom_format, nifti_format, nifti_gz_format,
                     analyze_format)

atlas_repo = XnatRepository(
    'http://central.xnat.org', 'SAMPLE_TEMPLATES',
    os.path.expanduser(os.path.join('~', 'xnat-cache')))

atlas = FilesetSelector(
    'an_atlas', nifti_gz_format,
    'an_atlas', frequency='per_study').match(atlas_repo.tree())


class ExampleStudy(Study, metaclass=StudyMetaClass):

    add_data_specs = [
        # Acquired file sets
        AcquiredFilesetSpec('acquired_file1', text_format),
        AcquiredFilesetSpec('acquired_file2', STD_IMAGE_FORMATS),
        # Acquired fields
        AcquiredFieldSpec('acquired_field1', int,
                          frequency='per_subject'),
        AcquiredFieldSpec('acquired_field2', float),
        # "Acquired" file set with default value. Useful for
        # standard templates
        AcquiredFilesetSpec('atlas1', STD_IMAGE_FORMATS,
                            frequency='per_study', default=atlas),
        # Derived file sets
        FilesetSpec('derived_file1', text_format, 'pipeline1'),
        FilesetSpec('derived_file2', nifti_gz_format, 'pipeline1'),
        FilesetSpec('derived_file3', text_mat_format, 'pipeline2'),
        FilesetSpec('derived_file4', dicom_format, 'pipeline3'),
        FilesetSpec('derived_file5', nifti_gz_format, 'pipeline3',
                    frequency='per_subject'),
        FilesetSpec('derived_file6', text_format, 'pipeline4',
                    frequency='per_visit'),
        # Derived fields
        FieldSpec('derived_field1', float, 'pipeline2'),
        FieldSpec('derived_field2', int, 'pipeline4',
                  frequency='per_study')]

    add_parameter_specs = [
        # Standard parameters
        ParameterSpec('parameter1', 10),
        ParameterSpec('parameter2', 25.8),
        # "Switch" parameters that specify a qualitative change
        # in the analysis
        SwitchSpec('pipeline_tool', 'toolA', ('toolA', 'toolB'))]

    def pipeline2(self, **mods):

        pipeline = self.pipeline(
            name='pipeline2',
            modifications=mods,
            desc="Description of the pipeline",
            references=[methods_paper_cite])

        node1 = pipeline.add(
            'node1',
            Interface1(
                param1=3.5,
                param3=self.parameter('parameter1')),
            inputs={
                'in_file1': ('acquired_file1', text_format),
                'in_file2': ('acquired_file2', analyze_format),
                'in_field': ('acquired_field1', int)},
            outputs={
                'out_field': ('derived_field1', int)},
            wall_time=25, requirements=[software_req1])

        if self.branch('pipeline_tool', 'toolA'):
            pipeline.add(
                'node2',
                Interface2(
                    param1=self.parameter('parameter2')),
                inputs={
                    'template': ('atlas1', nifti_gz_format)},
                connect={
                    'in_file': (node1, 'out_file')},
                outputs={
                    'out_file': ('derived_file3',
                                 text_mat_format)},
                wall_time=10, requirements=[software_req2])
        elif self.branch('pipeline_tool', 'toolB'):
            pipeline.add(
                'node2',
                Interface3(),
                inputs={
                    'template': ('atlas1', nifti_gz_format)},
                connect={
                    'in_file': (node1, 'out_file')},
                outputs={
                    'out_file': ('derived_file3',
                                 text_mat_format)},
                wall_time=30, requirements=[matlab_req,
                                            toolbox1_req])
        else:
            self.unhandled_branch('pipeline_tool')

        return pipeline
