from arcana import (
    MultiStudy, MultiStudyMetaClass, SubStudySpec, ParameterSpec)
from nianalysis.study.mri.structural.diffusion import DiffusionStudy
# from nianalysis.study.mri.structural.t2star import T2starwT1wStudy
from nianalysis.plot import ImageDisplayMixin
import os.path as op


class ArcanaPaper(MultiStudy, ImageDisplayMixin,
                  metaclass=MultiStudyMetaClass):
    """
    An Study class to perform the analyses performed in the paper
    introducing Arcana. Requires a repository containing
    T1-weighted, T2*-weighted and diffusion MRI data.
    """

    add_sub_study_specs = [
        # Include two Study classes in the overall study
#         SubStudySpec('t2star', T2starwT1wStudy),
        SubStudySpec('dmri', DiffusionStudy)]

    add_parameter_specs = [
        ParameterSpec(
            'fig12_13_slice_offset', (4, 0, 0),
            desc=("Offset the sagittal slices of Figure 11 & 12 so they "
                  "intersect a cerebral hemisphere instead of the "
                  "midline between the hemispheres"))]

    def figure11(self, save_path=None, **kwargs):
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
        swis = self.data('t2star_swi')
        qsms = self.data('t2star_qsm')
        vein_atlases = self.data('t2star_vein_atlas')
        vein_masks = self.data('t2star_vein_mask')
        # Loop through all sessions
        for swi, qsm, vein_atlas, vein_mask in zip(swis, qsms,
                                                   vein_atlases,
                                                   vein_masks):
            # Display slices from the filesets in a panel using
            # method from the ImageDisplayMixin base class.
            self.display_slice_panel(
                (swi, qsm, vein_atlas, vein_mask), **kwargs)
            # Display or save to file the generated image.
            self.save_or_show(save_path, swi.subject_id, swi.visit_id)

    def figure12(self, save_path=None, **kwargs):
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
            self.display_slice_panel(
                (fa, adc),
                row_kwargs=({'vmax': 1.0}, {}),
                offset=self.parameter('fig12_13_slice_offset'),
                **kwargs)
            # Display or save to file the generated image.
            self.save_or_show(save_path, fa.subject_id, fa.visit_id)

    def figure13(self, save_path=None, **kwargs):
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
            self.display_tcks_with_mrview(
                tcks=(tck,), backgrounds=(fa,),
                offset=self.parameter('fig11_12_slice_offset'),
                **kwargs)
            # Display or save to file the generated image.
            self.save_or_show(save_path, tck.subject_id, tck.visit_id)


if __name__ == '__main__':
    from arcana import (
        DirectoryRepository, LinearProcessor, FilesetMatch)
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
        DirectoryRepository(data_dir),
        # Use a single process on the local system to derive
        LinearProcessor(work_dir),
        # Match names in the data specification to filenames used
        # in the repository
        inputs=[FilesetMatch('dmri_primary', dicom_format, '16.*',
                             is_regex=True),
                FilesetMatch('dmri_reverse_phase', dicom_format, '15.*',
                             is_regex=True)],
        parameters={
            'dmri_num_global_tracks': int(1e5),
            'dmri_global_tracks_cutoff': 0.175})

    # Derive required data and display them in a single step for each
    # figure.
#     paper.figure10(op.join(fig_dir, 'figure11.png'))
    paper.figure11(op.join(fig_dir, 'figure12.png'))
    paper.figure12(op.join(fig_dir, 'figure13.png'))
