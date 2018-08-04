from arcana import (
    MultiStudy, MultiStudyMetaClass, SubStudySpec, ParameterSpec)
from nianalysis.study.mri.structural.diffusion import DiffusionStudy
from nianalysis.study.mri.structural.t2star import T2StarStudy
import numpy as np
from itertools import chain
from collections import defaultdict
import os.path as op
import matplotlib.image
import tempfile
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import subprocess as sp


class ArcanaPaper(MultiStudy, metaclass=MultiStudyMetaClass):
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
        SubStudySpec('dmri', DiffusionStudy),
        # SubStudySpec('t2star', T2starwT1wStudy)
        ]

    add_parameter_specs = [
        # Override default parameter in DiffusionStudy
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
        self._plot_slice_panel(('swi', 'qsm', 'vein_atlas', 'ven_mask'),
                               save_path=save_path, **kwargs)
        print('Plotted Figure 10')

    def figure11(self, save_path=None, **kwargs):
        """
        Generates an image panel containing the derived FA and ADC
        images

        Parameters
        ----------
        save_path : str | None
            The path to save the image to. If None the image will be
            displayed instead of saved
        """
        self._plot_slice_panel(('dmri_fa', 'dmri_adc'),
                               save_path=save_path,
                               plot_args={'fa': {'vmax': 1.0}},
                               **kwargs)
        print('Plotted Figure 11')

    def figure12(self, save_path=None, img_size=3, padding=1,
                 view_area=(100, 100)):
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
        for subj_id in self.subject_ids:
            for visit_id in self.visit_ids:
                tck_path = self.data('dmri_global_tracks').path(
                    subject_id=subj_id, visit_id=visit_id)
                fa_path = self.data('dmri_fa').path(
                    subject_id=subj_id, visit_id=visit_id)
                sp_kwargs = {}
                cmd = ''
                if self._mrtrix_path is not None:
                    cmd = self._mrtrix_path + '/'
                else:
                    sp_kwargs['shell'] = True
                cmd += 'mrview'
                options = ['-tractography.load', tck_path]
                tmpdir = tempfile.mkdtemp()
                options.extend(
                    ['-noannotations', '-lock', 'yes',
                     '-size', '{},{}'.format(*view_area),
                     '-capture.grab', '-exit'])
                # Create figure in which to aggregate the plots
                gs = GridSpec(1, 3)
                gs.update(wspace=0.0, hspace=0.0)
                fig = plt.figure(figsize=(3 * img_size, img_size))
                # Call mrview to display the tracks, capture them to
                # file and then reload the image into a matplotlib
                # grid
                imgs = []
                for i in range(3):
                    sp.call(
                        '{} {} -plane {} {}'.format(
                            cmd, fa_path, 2 - i, ' '.join(options)),
                        cwd=tmpdir, **sp_kwargs)
                    img = matplotlib.image.imread(
                        op.join(tmpdir, 'screenshot0000.png'))
                    imgs.append(self._crop(img, border=padding))
                padded_size = max(chain(*(a.shape for a in imgs)))
                for i, img in enumerate(imgs):
                    img = self._pad_to_size(img, (padded_size,
                                                  padded_size))
                    axis = fig.add_subplot(gs[i])
                    axis.get_xaxis().set_visible(False)
                    axis.get_yaxis().set_visible(False)
                    plt.imshow(img)
#                 plt.tight_layout()
                if save_path is None:
                    plt.show()
                else:
                    base, ext = op.splitext(save_path)
                    if len(list(self.subject_ids)) > 1:
                        base += '-sub{}'.format(subj_id)
                    if len(list(self.visit_ids)) > 1:
                        base += '-vis{}'.format(visit_id)
                    sess_save_path = base + ext
                    plt.savefig(sess_save_path)
                print('Plotted Figure 12')

    def _plot_slice_panel(self, data_names, save_path=None,
                          img_size=5, plot_args=None):
        """
        Plots in a Nx3 panel axial, coronal and sagittal slices for each
        of the image names specified

        Parameters
        ----------
        data_names : List[str]
            List of image names to plot as rows of a panel
        size : Tuple(2)[int]
            Size of the figure to plot
        plot_args : Dict[str,Dict[str,str]]
            A dictionary of dictionaries containing any image specific
            kwargs to be passed to the plot
        """
        n_rows = len(data_names)
        # Make sure plot_args is a default dict of dicts
        if plot_args is not None:
            plot_args = defaultdict(dict, plot_args)
        else:
            plot_args = defaultdict(dict)
        for subj_id in self.subject_ids:
            for visit_id in self.visit_ids:
                # Set up figure
                gs = GridSpec(n_rows, 3)
                gs.update(wspace=0.0, hspace=0.0)
                fig = plt.figure(figsize=(3 * img_size,
                                          n_rows * img_size))

                # Loop through derivatives and generate image
                for i, data_name in enumerate(data_names):
                    fileset = self.data(data_name, subject_id=subj_id,
                                        visit_id=visit_id)
                    array = fileset.get_array()
                    header = fileset.get_header()
                    vox = header['pixdim'][1:4]
                    self._plot_mid_slices(
                        array, vox, fig, gs, i, **plot_args[data_name])
                # Remove space around figure
                plt.tight_layout(0.0)
                # Either show image or save it to file
                if save_path is None:
                    plt.show()
                else:
                    base, ext = op.splitext(save_path)
                    if len(list(self.subject_ids)) > 1:
                        base += '-sub{}'.format(subj_id)
                    if len(list(self.visit_ids)) > 1:
                        base += '-vis{}'.format(visit_id)
                    sess_save_path = base + ext
                    plt.savefig(sess_save_path)

    def _plot_mid_slices(self, array, vox_sizes, fig, grid_spec,
                         row_index, padding=1, vmax=None,
                         vmax_percentile=98):
        # Guard agains NaN
        array[np.isnan(array)] = 0.0
        # Crop black-space around array
        array = self._crop(array, padding)
        # Pad out image array into cube
        padded_size = np.max(array.shape)
        mid = np.array(array.shape, dtype=int) // 2

        # Get dynamic range of array
        if vmax is None:
            assert vmax_percentile is not None
            vmax = np.percentile(array, vmax_percentile)

        # Function to plot a slice
        def plot_slice(slce, index, aspect):
            axis = fig.add_subplot(grid_spec[index])
            axis.get_xaxis().set_visible(False)
            axis.get_yaxis().set_visible(False)
            padded_slce = self._pad_to_size(slce, (padded_size,
                                                   padded_size))
            plt.imshow(padded_slce,
                       interpolation='bilinear',
                       cmap='gray', aspect=aspect,
                       vmin=0, vmax=vmax)
        # Plot slices
        plot_slice(np.squeeze(array[-1:0:-1, -1:0:-1, mid[2]]).T,
                   row_index * 3, vox_sizes[0] / vox_sizes[1])
        plot_slice(np.squeeze(array[-1:0:-1, mid[1], -1:0:-1]).T,
                   row_index * 3 + 1, vox_sizes[0] / vox_sizes[2])
        plot_slice(np.squeeze(array[mid[0], -1:0:-1, -1:0:-1]).T,
                   row_index * 3 + 2, vox_sizes[1] / vox_sizes[2])

    @classmethod
    def _crop(cls, array, border=0):
        nz = np.argwhere(array)
        return array[tuple(
            slice(max(a - border, 0),
                  min(b + border, array.shape[i]))
            for i, (a, b) in enumerate(zip(nz.min(axis=0),
                                           nz.max(axis=0))))]

    @classmethod
    def _pad_to_size(cls, array, size):
        pad_before = [
            (size[i] - array.shape[i]) // 2
            for i in range(2)]
        pad_after = [
            size[i] - array.shape[i] - pad_before[i]
            for i in range(2)]
        padding = list(zip(pad_before, pad_after))
        padding.extend((0, 0) for _ in range(array.ndim - 2))
        return np.pad(array, padding, 'constant')


if __name__ == '__main__':
    from arcana import (
        LocalRepository, LinearProcessor, FilesetMatch)
    from nianalysis.file_format import dicom_format
    import os

    study_dir = op.join(op.dirname(__file__), '..', 'data')

    paper = ArcanaPaper(
        'arcana_paper',
        LocalRepository(op.join(study_dir, 'study')),
        LinearProcessor(op.join(study_dir, 'work')),
        inputs=[FilesetMatch('dmri_primary', dicom_format, '16.*',
                             is_regex=True),
                FilesetMatch('dmri_reverse_phase', dicom_format, '15.*',
                             is_regex=True)])

    fig_dir = op.join(study_dir, 'figures')
    os.makedirs(fig_dir, exist_ok=True)
#     paper.figure10(op.join(fig_dir, 'figure10.png'))
    paper.figure11(op.join(fig_dir, 'figure11.png'))
    paper.figure12(op.join(fig_dir, 'figure12.png'))
