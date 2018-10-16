from arcana import (
    MultiStudy, MultiStudyMetaClass, SubStudySpec, ParameterSpec)
from nianalysis.study.mri.structural.diffusion import DiffusionStudy
from nianalysis.study.mri.structural.t1 import T1Study
from nianalysis.study.mri.structural.t2star import T2StarStudy
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
        SubStudySpec(
            't1', T1Study),
        SubStudySpec(
            't2star', T2StarStudy,
            name_map={'t1_brain': 'coreg_ref_brain',
                      't1_coreg_to_atlas_mat': 'coreg_to_atlas_mat',
                      't1_coreg_to_atlas_warp': 'coreg_to_atlas_warp'}),
        SubStudySpec('dmri', DiffusionStudy)]

    add_param_specs = [
        ParameterSpec(
            'dmri_fig_slice_offset', (4, 0, 0),
            desc=("Offset the sagittal slices of dMRI figures so they "
                  "intersect a cerebral hemisphere instead of the "
                  "midline between the hemispheres"))]

    def vein_fig(self, save_path=None, **kwargs):
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
        cv_image = self.data('t2star_composite_vein_image')
        vein_masks = self.data('t2star_vein_mask')
        # Loop through all sessions
        for swi, qsm, vein_atlas, vein_mask in zip(swis, qsms, cv_image,
                                                   vein_masks):
            # Display slices from the filesets in a panel using
            # method from the ImageDisplayMixin base class.
            self.display_slice_panel(
                (swi, qsm, vein_atlas, vein_mask), **kwargs)
            # Display or save to file the generated image.
            self.save_or_show(save_path, swi.subject_id, swi.visit_id)

    def fa_adc_fig(self, save_path=None, **kwargs):
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
                offset=self.parameter('dmri_fig_slice_offset'),
                **kwargs)
            # Display or save to file the generated image.
            self.save_or_show(save_path, fa.subject_id, fa.visit_id)

    def tractography_fig(self, save_path=None, **kwargs):
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
                offset=self.parameter('tractography_fig_slice_offset'),
                **kwargs)
            # Display or save to file the generated image.
            self.save_or_show(save_path, tck.subject_id, tck.visit_id)


if __name__ == '__main__':
    from arcana import (
        DirectoryRepository, LinearProcessor, FilesetSelector)
    from nianalysis.file_format import dicom_format, zip_format
    import os

    # Path to data, work and output directories
    this_dir = op.dirname(__file__)
    data_dir = op.join(this_dir, 'data', 'lifespan')
    work_dir = op.join(this_dir, 'work')
    fig_dir = op.join(this_dir, 'manuscript', 'figures')
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
        inputs=[
            FilesetSelector('t1_magnitude', dicom_format, '.*t1_mprage.*',
                            is_regex=True),
            FilesetSelector('t2star_channels', zip_format,
                            'swi_coils_icerecon'),
            FilesetSelector('t2star_header_image', dicom_format,
                            '12-SWI_Images'),
            FilesetSelector('t2star_swi', dicom_format, 'SWI_Images'),
            FilesetSelector('dmri_magnitude', dicom_format, '.*ep2d_.*',
                            is_regex=True),
            FilesetSelector('dmri_reverse_phase', dicom_format, '.*PRE_DWI.*',
                            is_regex=True)],
        parameters={
            'dmri_num_global_tracks': int(1e5),
            'dmri_global_tracks_cutoff': 0.175})

    # Derive required data and display them in a single step for each
    # figure.
    paper.vein_fig(op.join(fig_dir, 'veins.png'))
    paper.fa_adc_fig(op.join(fig_dir, 'fa_adc.png'))
    paper.tractography_fig(op.join(fig_dir, 'tractography.png'))
