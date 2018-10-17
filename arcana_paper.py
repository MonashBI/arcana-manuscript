#!/usr/bin/env python3
from arcana import (
    MultiStudy, MultiStudyMetaClass, SubStudySpec, ParameterSpec)
from nianalysis.study.mri import (DiffusionStudy, T1Study, T2StarStudy)
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
            't1',
            T1Study),
        SubStudySpec(
            't2star',
            T2StarStudy,
            name_map={'t1_brain': 'coreg_ref_brain',
                      't1_coreg_to_atlas_mat': 'coreg_to_atlas_mat',
                      't1_coreg_to_atlas_warp': 'coreg_to_atlas_warp'}),
        SubStudySpec(
            'dmri',
            DiffusionStudy)]

    add_param_specs = [
        ParameterSpec(
            'dmri_fig_slice_offset', (6, 0, 0),
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
            # Set the saturation limits for the QSM image
            row_kwargs = [{} for _ in range(4)]
            row_kwargs[1]['vmax_percentile'] = 95
            row_kwargs[1]['vmin_percentile'] = 5
            # Display slices from the filesets in a panel using
            # method from the ImageDisplayMixin base class.
            self.display_slice_panel(
                (swi, qsm, vein_atlas, vein_mask),
                row_kwargs=row_kwargs, **kwargs)
            # Display or save to file the generated image.
            self.show(save_path, swi.subject_id, swi.visit_id)

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
            self.show(save_path, fa.subject_id, fa.visit_id)

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
                offset=self.parameter('dmri_fig_slice_offset'),
                **kwargs)
            # Display or save to file the generated image.
            self.show(save_path, tck.subject_id, tck.visit_id)


if __name__ == '__main__':
    import os
    from argparse import ArgumentParser
    from arcana import (
        DirectoryRepository, LinearProcessor, StaticEnvironment,
        FilesetSelector)
    from nianalysis.file_format import (
        dicom_format, zip_format, nifti_gz_format)

    parser = ArgumentParser(
        "A script to produce figures for the Arcana manuscript")
    parser.add_argument('data_dir',
                        help="The directory containing repository")
    parser.add_argument('--work_dir', help="The work directory",
                        default=op.join(op.expanduser('~'),
                                        'arcana-paper-work'))
    parser.add_argument(
        '--fig_dir', help="The directory to store the figures",
        default=op.join(op.expanduser('~'),
                        'arcana-paper-fig'))
    args = parser.parse_args()

    # Make figure directory
    os.makedirs(args.fig_dir, exist_ok=True)

    # Instantiate the ArcanaPaper class in order to apply it to a
    # specific dataset
    paper = ArcanaPaper(
        # Name for this analysis instance
        'arcana_paper',
        # Repository is a simple directory on the local file system
        repository=DirectoryRepository(args.data_dir),
        # Use a single process on the local system to derive
        processor=LinearProcessor(args.work_dir,
                                  clean_work_dir_between_runs=False),
        # Use the static environment (i.e. no Modules)
        environment=StaticEnvironment(),
        # Match names in the data specification to filenames used
        # in the repository
        inputs=[
            FilesetSelector('t1_magnitude', dicom_format, '.*t1_mprage.*',
                            is_regex=True),
            FilesetSelector('t2star_channels', zip_format,
                            'swi_coils_icerecon'),
            FilesetSelector('t2star_header_image', dicom_format,
                            'SWI_Images.old'),
            FilesetSelector('t2star_swi', nifti_gz_format, 'SWI_Images'),
            FilesetSelector('dmri_magnitude', dicom_format, '.*ep2d_.*',
                            is_regex=True),
            FilesetSelector('dmri_reverse_phase', dicom_format, '.*PRE_DWI.*',
                            is_regex=True)],
        parameters={
            'dmri_num_global_tracks': int(1e5),
            'dmri_global_tracks_cutoff': 0.175,
            # This is needed as the channels aren't reconstructed with the
            # correct headers
            't2star_force_channel_flip': ['-x', '-y', 'z']})

    # Derive required data and display them in a single step for each
    # figure.
    paper.vein_fig(op.join(args.fig_dir, 'veins.png'))
    paper.fa_adc_fig(op.join(args.fig_dir, 'fa_adc.png'))
    paper.tractography_fig(op.join(args.fig_dir, 'tractography.png'))