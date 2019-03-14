from arcana import (Study, StudyMetaClass, FilesetInputSpec, FilesetSpec,
                    FieldInputSpec, FieldSpec, ParamSpec, SwitchSpec,
                    FilesetCollection, XnatRepo, Fileset)
from arcana.data.file_format.standard import text_format
from banana.file_format import (
    nifti_gz_format, dicom_format, nifti_format, analyze_format)

STD_IMAGE_FORMATS = (dicom_format, nifti_format, nifti_gz_format,
                     analyze_format)

template_repo = XnatRepo('http://central.xnat.org', 'SAMPLE_TEMPLATES')
template1_default = FilesetCollection(Fileset('sample_atlas', ))


class ExampleStudy(Study, metaclass=StudyMetaClass):

    add_data_specs = [
        # Acquired file sets
        FilesetInputSpec('acquired_file1', text_format),
        FilesetInputSpec('acquired_file2', IMAGE_FORMATS),
        # Acquired fields
        FieldInputSpec('acquired_field1', int, frequency='per_subject'),
        FieldInputSpec('acquired_field2', str,),
        # "Acquired" file set with default value. Useful for standard templates
        FilesetInputSpec('template1', IMAGE_FORMATS, frequency='per_study',
                            default=template1_default),
        # Derived file sets
        FilesetSpec('derived_file1', text_format, 'pipeline1'),
        FilesetSpec('derived_file2', nifti_gz_format, 'pipeline1'),
        FilesetSpec('derived_file3', text_format, 'pipeline2'),
        FilesetSpec('derived_file4', dicom_format, 'pipeline3'),
        FilesetSpec('derived_file5', nifti_gz_format, 'pipeline3',
                    frequency='per_subject'),
        FilesetSpec('derived_file6', text_format, 'pipeline4',
                    frequency='per_visit'),
        # Derived fields
        FieldSpec('derived_field4', float, 'pipeline2'),
        FieldSpec('derived_field7', int, 'pipeline4',
                  frequency='per_study')]

    add_param_specs = [
        # Standard parameters
        ParamSpec('parameter1', 10),
        ParamSpec('parameter2', 25.8),
        # Parameters that specify a qualitative change in the analysis
        SwitchSpec('pipeline_tool', 'toolA', ('toolA', 'toolB'))]
