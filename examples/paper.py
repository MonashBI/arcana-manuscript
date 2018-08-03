from arcana import MultiStudy, MultiStudyMetaClass, SubStudySpec
from nianalysis.study.mri.structural.diffusion import DiffusionStudy
from nianalysis.study.mri.structural.t2star import T2StarStudy
from nianalysis.file_format import dicom_format
import os.path as op
import matplotlib.pyplot as plt


class ArcanaPaperStudy(MultiStudy, metaclass=MultiStudyMetaClass):

    add_sub_study_specs = [
        SubStudySpec('dmri', DiffusionStudy),
        SubStudySpec('t2star', T2StarStudy)]

    def figure10(self, save_path=None):
        for derivative in ('fa', 'adc'):
            for fileset in enumerate(self.data(derivative)):
                array = fileset.array
                mid = array.size // 2
                if save_path is None:
                    plt.imshow(array[mid[0], :, :])
                    plt.imshow(array[:, mid[1], :])
                    plt.imshow(array[:, :, mid[2]])
        if save_path is None:
            plt.show()


if __name__ == '__main__':
    from arcana import LocalRepository, LinearProcessor, FilesetMatch
    test_dir = op.join(op.dirname(__file__), '..', 'data')

    study = ArcanaPaperStudy(
        'paper',
        LocalRepository(op.join(test_dir, 'study')),
        LinearProcessor(op.join(test_dir, 'work')),
        inputs=[FilesetMatch('dmri_primary', dicom_format, '16.*',
                             is_regex=True),
                FilesetMatch('dmri_reverse_phase', dicom_format, '15.*',
                             is_regex=True)])
    study.figure10()
