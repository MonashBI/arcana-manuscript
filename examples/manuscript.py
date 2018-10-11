from arcana import (Study, StudyMetaClass, AcquiredFilesetSpec, FilesetSpec,
                    AcquiredFieldSpec, FieldSpec, ParameterSpec, SwitchSpec,
                    FilesetCollection, XnatRepository, Fileset)
from arcana.data.file_format.standard import text_format
from nianalysis.file_format import (
    nifti_gz_format, dicom_format, nifti_format, analyze_format)

STD_IMAGE_FORMATS = (dicom_format, nifti_format, nifti_gz_format,
                     analyze_format)

template_repo = XnatRepository('http://central.xnat.org', 'SAMPLE_TEMPLATES')
template1_default = FilesetCollection(Fileset)


class ExampleStudy(Study, metaclass=StudyMetaClass):

    add_data_specs = [
        # Acquired file sets
        AcquiredFilesetSpec('acquired_file1', text_format),
        AcquiredFilesetSpec('acquired_file2', IMAGE_FORMATS),
        # Acquired fields
        AcquiredFieldSpec('acquired_field1', int, frequency='per_subject'),
        AcquiredFieldSpec('acquired_field2', str,),
        # "Acquired" file set with default value. Useful for standard templates
        AcquiredFilesetSpec('template1', IMAGE_FORMATS, frequency='per_study',
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

    add_parameter_specs = [
        # Standard parameters
        ParameterSpec('parameter1', 10),
        ParameterSpec('parameter2', 25.8),
        # Parameters that specify a qualitative change in the analysis
        SwitchSpec('pipeline_tool', 'toolA', ('toolA', 'toolB'))]
