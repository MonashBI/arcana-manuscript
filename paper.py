from arcana import (
    MultiStudy, MultiStudyMetaClass, SubStudySpec, ParameterSpec)
from nianalysis.study.mri.structural.diffusion import DiffusionStudy
from nianalysis.study.mri.structural.t2star import T2starwT1wStudy
from nianalysis.plot import ImageDisplayMixin
import os.path as op


class ArcanaPaper(MultiStudy, ImageDisplayMixin,
                  metaclass=MultiStudyMetaClass):
    """
    An Arcana study that analyses a MRI project data contain T1-weighted,
    T2*-weighted and diffusion MRI contrasts

    Parameters
    ----------
    mrtrix_path : str | None
        Path to the installation of MRtrix (required to render the
        streamlines in Figure 11) if not installed on the system
        path
    """

    def __init__(self, *args, mrtrix_path=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._mrtrix_path = mrtrix_path

    add_sub_study_specs = [
        SubStudySpec('t2star', T2starwT1wStudy),
        SubStudySpec('dmri', DiffusionStudy)]

    add_parameter_specs = [
        # Override default parameters in DiffusionStudy
        ParameterSpec('dmri_num_global_tracks', int(1e5)),
        ParameterSpec('dmri_global_tracks_cutoff', 0.2)]

    def figure10(self, save_path=None, **kwargs):
        """
        Generates an image panel containing the SWI, QSM, vein atlas,
        and vein mask

        Parameters
        ----------
        save_path : str | None
            The path to save the image to. If None the image will be
            displayed instead of saved
        """
        # Derive (when necessary) and access data SWI, QSM, vein atlas,
        # and vein mask data in the repository.
        swis = self.data('swi')
        qsms = self.data('qsm')
        vein_atlases = self.data('vein_atlas')
        vein_masks = self.data('vein_mask')
        # Loop through all sessions
        for swi, qsm, vein_atlas, vein_mask in zip(swis, qsms,
                                                   vein_atlases,
                                                   vein_masks):
            # Display slices from the filesets in a panel using
            # method from the ImageDisplayMixin base class.
            self._display_slice_panel(
                (swi, qsm, vein_atlas, vein_mask), **kwargs)
            # Display or save to file the generated image.
            self._save_or_show(save_path, swi.subject_id, swi.visit_id)

    def figure11(self, save_path=None, **kwargs):
        """
        Generates an image panel containing the derived FA and ADC
        images for each session in the study (typically only one)

        Parameters
        ----------
        save_path : str | None
            The path to save the image to. If None the image will be
            displayed instead of saved
        """
        # Derive FA and ADC if necessary and return a handle to the
        # data collections in the repository
        fas, adcs = self.data(('dmri_fa', 'dmri_adc'))
        # Loop through all sessions
        for fa, adc in zip(fas, adcs):
            # Display slices from the filesets in a panel using
            # method from the ImageDisplayMixin base class.
            self._display_slice_panel((fa, adc),
                                      row_kwargs=({'vmax': 1.0},
                                                  {}), **kwargs)
            # Display or save to file the generated image.
            self._save_or_show(save_path, fa.subject_id, fa.visit_id)

    def figure12(self, save_path=None, **kwargs):
        """
        Generates dMRI tractography streamlines seeded from without the
        white matter.

        Is a bit more complex as it uses MRtrix's mrview to display and
        screenshot to file the high volume of streamlines created. Then
        reload, crop and combine the different slice orientations into
        a single panel.

        Parameters
        ----------
        save_path : str | None
            The path of the file to save the image at. If None the
            images are displayed instead
        size : Tuple(2)[int]
            The size of the combined figure to plot
        """
        # Generate and loop through tcks and FA maps for each
        # session in repository
        for tck, fa in zip(*self.data(('dmri_global_tracks',
                                       'dmri_fa'))):
            # Display generated streamlines with mrview from the
            # MRtrix package
            self._display_tcks_with_mrview(
                tcks=(tck,), backgrounds=(fa,), **kwargs)
            # Display or save to file the generated image.
            self._save_or_show(save_path, tck.subject_id, tck.visit_id)
        print('Figure12')


if __name__ == '__main__':
    from arcana import (
        LocalRepository, LinearProcessor, FilesetMatch)
    from nianalysis.file_format import dicom_format
    import os

    # Path to data, work and output directories
    this_dir = op.dirname(__file__)
    data_dir = op.join(this_dir, 'data')
    work_dir = op.join(this_dir, 'work')
    fig_dir = op.join(this_dir, 'figures')
    os.makedirs(fig_dir, exist_ok=True)

    # Instantiate the ArcanaPaper class in order to apply it to a
    # specific dataset
    paper = ArcanaPaper(
        # Name for this analysis instance
        'arcana_paper',
        # Repository is a simple directory on the local file system
        LocalRepository(data_dir),
        # Use a single process on the local system to derive
        LinearProcessor(work_dir),
        # Match names in the data specification to filenames used
        # in the repository
        inputs=[FilesetMatch('dmri_primary', dicom_format, '16.*',
                             is_regex=True),
                FilesetMatch('dmri_reverse_phase', dicom_format, '15.*',
                             is_regex=True)])

    # Derive the data required for each figure and display them a single
    # steps
    paper.figure10(op.join(fig_dir, 'figure10.png'))
    paper.figure11(op.join(fig_dir, 'figure11.png'))
    paper.figure12(op.join(fig_dir, 'figure12.png'))
