import os
from arcana import (
    Study, StudyMetaClass, FilesetInputSpec, FilesetSpec,
    FieldInputSpec, FieldSpec, ParamSpec, SwitchSpec,
    FilesetInput, XnatRepo)
from banana.file_format import (
    nifti_gz_format, dicom_format, nifti_format, analyze_format,
    text_format, text_matrix_format)

STD_IMAGE_FORMATS = (dicom_format, nifti_format, nifti_gz_format,
                     analyze_format)

# Select a Fileset collection to use as a default for template1
template_repo = XnatRepo(
    server='http://central.xnat.org', project_id='TEMPLATES',
    cache=os.path.expanduser(os.path.join('~', 'xnat-cache')))
template_selector = FilesetInput('MNI152_T1', nifti_gz_format,
                                 frequency='per_study')
template_collectn = template_selector.match(template_repo.tree())


class ExampleStudy(Study, metaclass=StudyMetaClass):

    add_data_specs = [
        # Acquired file sets
        FilesetInputSpec('acquired_file1', text_format),
        FilesetInputSpec('acquired_file2', STD_IMAGE_FORMATS),
        # Acquired fields
        FieldInputSpec('acquired_field1', int, array=True,
                       frequency='per_subject'),
        FieldInputSpec('acquired_field2', float, optional=True),
        # "Acquired" file set with default value. Useful for
        # standard templates
        FilesetInputSpec('template1', STD_IMAGE_FORMATS,
                         frequency='per_study',
                         default=template_collectn),
        # Derived file sets
        FilesetSpec('derived_file1', text_format, 'pipeline1'),
        FilesetSpec('derived_file2', nifti_gz_format, 'pipeline1'),
        FilesetSpec('derived_file3', text_matrix_format,
                    'pipeline2'),
        FilesetSpec('derived_file4', dicom_format, 'pipeline3'),
        FilesetSpec('derived_file5', nifti_gz_format, 'pipeline3',
                    frequency='per_subject'),
        FilesetSpec('derived_file6', analyze_format, 'pipeline2',
                    frequency='per_visit'),
        # Derived fields
        FieldSpec('derived_field1', float, 'pipeline2'),
        FieldSpec('derived_field2', int, 'pipeline4',
                  frequency='per_study')]

    add_param_specs = [
        # Standard parameters
        ParamSpec('parameter1', 10),
        ParamSpec('parameter2', 25.8),
        # "Switch" parameters that specify a qualitative change
        # in the analysis
        SwitchSpec('node1_option', False),  # Boolean switch
        SwitchSpec('pipeline2_tool', 'toolA', ('toolA', 'toolB'))]

    def pipeline2(self, **name_maps):

        pipeline = self.new_pipeline(
            name='pipeline2',
            name_maps=name_maps,
            desc="Description of the pipeline",
            citations=[methods_paper_cite])

        node1 = pipeline.add(
            'node1',
            Interface1(
                param1=3.5,
                param2=self.parameter('parameter1')),
            inputs={
                'in_file1': ('acquired_file1', text_format),
                'in_file2': ('acquired_file2', analyze_format),
                'in_field': ('acquired_field1', int)},
            outputs={
                'derived_field1': ('out_field', int)},
            wall_time=25, requirements=[software_req1])
        if self.branch('node1_option'):
            node1.inputs.an_option = 'set-extra-option'

        if self.branch('pipeline2_tool', 'toolA'):
            pipeline.add(
                'node2',
                Interface2(
                    param1=self.parameter('parameter2')),
                inputs={
                    'template': ('template1', nifti_gz_format),
                    'in_file': (node1, 'out_file')},
                outputs={
                    'derived_file3': ('out_file',
                                      text_matrix_format)},
                wall_time=10, requirements=[software_req2])

            self.connect_output('derived_file6', node1, 'out',
                                nifti_format)
        elif self.branch('pipeline2_tool', 'toolB'):
            pipeline.add(
                'node2',
                Interface3(),
                inputs={
                    'template': ('template1', nifti_gz_format),
                    'in_file': (node1, 'out_file')},
                outputs={
                    'derived_file3': ('out_file',
                                      text_matrix_format)},
                wall_time=30, requirements=[matlab_req,
                                            toolbox1_req])
        else:
            self.unhandled_branch('pipeline2_tool')

        return pipeline
