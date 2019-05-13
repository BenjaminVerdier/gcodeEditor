#Code from https://github.com/zhangyaqi1989/Gcode-Reader


from enum import Enum
import os.path
import pprint
import sys
import numpy as np
import pandas as pd


class LayerError(Exception):
    """ layer number error """
    pass

class GcodeType(Enum):
    """ enum of GcodeType """

    FDM_REGULAR = 1
    FDM_STRATASYS = 2
    LPBF = 3

    @classmethod
    def has_value(cls, value):
        return any(value == item.value for item in cls)

class GcodeReader:
    """ Gcode reader class """

    def __init__(self, filename, filetype=GcodeType.FDM_REGULAR):
        if not os.path.exists(filename):
            print("{} does not exist!".format(filename))
            sys.exit(1)
        self.filename = filename
        self.filetype = filetype
        # print(self.filetype)
        self.n_segs = 0  # number of line segments
        self.segs = None  # list of line segments [(x0, y0, x1, y1, z)]
        self.n_layers = 0  # number of layers
        # seg_index_bars and subpath_index_bars have the same format
        # e.g. ith layer has segment indexes [seg_index_bars[i-1],
        # seg_index_bars[i])
        self.seg_index_bars = []
        self.subpath_index_bars = []
        self.summary = None
        self.lengths = None
        self.subpaths = None
        self.xyzlimits = None
        self.elements = None
        self.elements_index_bars = []
        # read file to populate variables
        self._read()

    def mesh(self, max_length):
        """ mesh segments according to max_length """
        self.elements = []
        self.elements_index_bars = []
        bar = 0
        n_eles = 0
        for i, (x0, y0, x1, y1, z) in enumerate(self.segs):
            if i == self.seg_index_bars[bar]:
                bar += 1
                self.elements_index_bars.append(n_eles)
            length = np.hypot(x0 - x1, y0 - y1)
            n_slices = int(np.ceil(length / max_length))
            n_eles += n_slices
            dx = (x1 - x0) / n_slices
            dy = (y1 - y0) / n_slices
            for _ in range(n_slices - 1):
                self.elements.append((x0, y0, x0 + dx, y0 + dy, z))
                x0, y0 = x0 + dx, y0 + dy
            self.elements.append((x0, y0, x1, y1, z))
        self.elements_index_bars.append(n_eles)
        # print(self.elements_index_bars)
        print("Meshing finished, {:d} elements generated".
              format(len(self.elements)))
    """
    def plot_mesh_layer(self, layernum, ax=None):
        # plot mesh in one layer
        if not self.elements:
            self.mesh(max_length=1)
        if not ax:
            fig, ax = create_axis(projection='2d')
        left, right = self.elements_index_bars[layernum - 1:layernum + 1]
        for x0, y0, x1, y1, _ in self.elements[left:right]:
            ax.plot([x0, x1], [y0, y1], 'b-')
            # ax.scatter(0.5 * (x0 + x1), 0.5 * (y0 + y1), s=4, color='r')
            ax.plot([0.5 * (x0 + x1)], [0.5 * (y0 + y1)], 'ro', markersize=4)
        return fig, ax

    def plot_mesh(self, ax=None):
        # plot mesh
        if not self.elements:
            self.mesh()
        if not ax:
            fig, ax = create_axis(projection='3d')
        for x0, y0, x1, y1, z in self.elements:
            ax.plot([x0, x1], [y0, y1], [z, z], 'b-')
            ax.scatter(0.5 * (x0 + x1), 0.5 * (y0 + y1), z, 'r', s=4,
                       color='r')
        return fig, ax
    """
    def _read(self):
        """
        read the file and populate self.segs, self.n_segs and
        self.seg_index_bars
        """
        if self.filetype == GcodeType.FDM_REGULAR:
            self._read_fdm_regular()
        elif self.filetype == GcodeType.FDM_STRATASYS:
            self._read_fdm_stratasys()
        elif self.filetype == GcodeType.LPBF:
            self._read_lpbf()
        else:
            print("file type is not supported")
            sys.exit(1)
        self.xyzlimits = self._compute_xyzlimits(self.segs)

    def _compute_xyzlimits(self, seg_list):
        """ compute axis limits of a segments list """
        xmin, xmax = float('inf'), -float('inf')
        ymin, ymax = float('inf'), -float('inf')
        zmin, zmax = float('inf'), -float('inf')
        for x0, y0, x1, y1, z in seg_list:
            xmin = min(x0, x1) if min(x0, x1) < xmin else xmin
            ymin = min(y0, y1) if min(y0, y1) < ymin else ymin
            zmin = z if z < zmin else zmin
            xmax = max(x0, x1) if max(x0, x1) > xmax else xmax
            ymax = max(y0, y1) if max(y0, y1) > ymax else ymax
            zmax = z if z > zmax else zmax
        return (xmin, xmax, ymin, ymax, zmin, zmax)

    def _read_lpbf(self):
        """ read LPBF gcode """
        with open(self.filename) as infile:
            # read nonempty lines
            lines = (line.strip() for line in infile.readlines()
                     if line.strip())
            # only keep line that starts with 'N'
            lines = (line for line in lines if line.startswith('N'))
        # pp.pprint(lines) # for debug
        self.segs = []
        self.powers = []
        temp = -float('inf')
        ngxyzfl = [temp, temp, temp, temp, temp, temp, temp]
        d = dict(zip(['N', 'G', 'X', 'Y', 'Z', 'F', 'L'], range(7)))
        seg_count = 0
        for line in lines:
            old_ngxyzfl = ngxyzfl[:]
            tokens = line.split()
            for token in tokens:
                ngxyzfl[d[token[0]]] = float(token[1:])
            if ngxyzfl[d['Z']] > old_ngxyzfl[d['Z']]:
                self.n_layers += 1
                self.seg_index_bars.append(seg_count)
            if (ngxyzfl[1] == 1 and ngxyzfl[2:4] != old_ngxyzfl[2:4]
                    and ngxyzfl[4] == old_ngxyzfl[4]
                    and ngxyzfl[5] > 0):
                x0, y0, z = old_ngxyzfl[2:5]
                x1, y1 = ngxyzfl[2:4]
                self.segs.append((x0, y0, x1, y1, z))
                self.powers.append(ngxyzfl[-1])
                seg_count += 1
        self.n_segs = len(self.segs)
        self.segs = np.array(self.segs)
        self.seg_index_bars.append(self.n_segs)
        # print(self.n_layers)
        assert(len(self.seg_index_bars) - self.n_layers == 1)

    def _read_fdm_regular(self):
        """ read fDM regular gcode type """
        with open(self.filename) as infile:
            # read nonempty lines
            lines = (line.strip() for line in infile.readlines()
                     if line.strip())
            # only keep line that starts with 'G1'
            lines = (line for line in lines if line.startswith('G1'))
        # pp.pprint(lines) # for debug
        self.segs = []
        temp = -float('inf')
        gxyzef = [temp, temp, temp, temp, temp, temp]
        d = dict(zip(['G', 'X', 'Y', 'Z', 'E', 'F'], range(6)))
        seg_count = 0
        for line in lines:
            old_gxyzef = gxyzef[:]
            for token in line.split():
                if token[1:] == "":
                    continue
                try:
                    gxyzef[d[token[0]]] = float(token[1:])
                except:
                    print("invalid token: " + token[1:] + ";")
                    sys.exit(1)
            if gxyzef[3] > old_gxyzef[3]:  # z value
                self.n_layers += 1
                self.seg_index_bars.append(seg_count)
            if (gxyzef[0] == 1 and gxyzef[1:3] != old_gxyzef[1:3]
                    and gxyzef[3] == old_gxyzef[3]
                    and gxyzef[4] > old_gxyzef[4]):
                x0, y0, z = old_gxyzef[1:4]
                x1, y1 = gxyzef[1:3]
                self.segs.append((x0, y0, x1, y1, z))
                seg_count += 1
        self.n_segs = len(self.segs)
        self.segs = np.array(self.segs)
        self.seg_index_bars.append(self.n_segs)
        assert(len(self.seg_index_bars) - self.n_layers == 1)

    def _read_fdm_stratasys(self):
        """ read stratasys fdm G-code file """
        self.areas = []
        self.is_supports = []
        self.styles = []
        self.deltTs = []
        self.segs = []
        temp = -float('inf')
        # x, y, z, area, deltaT, is_support, style
        xyzATPS = [temp, temp, temp, temp, temp, False, '']
        seg_count = 0
        with open(self.filename, 'r') as in_file:
            lines = in_file.readlines()
            # means position denoted by the line is the start of subpath
            is_start = True
            for line in lines:
                if line.startswith('#'):
                    continue
                if not line.strip():  # skip empty line
                    start = True
                    continue
                old_xyzATPS = xyzATPS[:]
                tokens = line.split()
                # print(tokens)
                xyzATPS[:5] = [float(token) for token in tokens[:5]]
                xyzATPS[5] = bool(tokens[5])
                xyzATPS[6] = tokens[6]
                if xyzATPS[2] != old_xyzATPS[2]:  # z value
                    self.seg_index_bars.append(seg_count)
                    self.n_layers += 1
                elif not start:
                    # make sure is_support and style do not change
                    assert(xyzATPS[5:] == old_xyzATPS[5:])
                    x0, y0 = old_xyzATPS[:2]
                    x1, y1, z = xyzATPS[:3]
                    self.segs.append((x0, y0, x1, y1, z))
                    seg_count += 1
                    self.areas.append(xyzATPS[3])
                    self.deltTs.append(xyzATPS[4])
                    self.is_supports.append(xyzATPS[5])
                    self.styles.append(xyzATPS[6])
                start = False
            self.n_segs = len(self.segs)
            self.segs = np.array(self.segs)
            self.seg_index_bars.append(self.n_segs)
            # print(self.seg_index_bars)

    def _compute_subpaths(self):
        """ compute subpaths
            a subpath is represented by (xs, ys, zs)
        """
        if not self.subpaths:
            self.subpaths = []
            self.subpath_index_bars = [0]
            x0, y0, x1, y1, z = self.segs[0, :]
            xs, ys, zs = [x0, x1], [y0, y1], [z, z]
            for x0, y0, x1, y1, z in self.segs[1:, :]:
                if x0 != xs[-1] or y0 != ys[-1] or z != zs[-1]:
                    self.subpaths.append((xs, ys, zs))
                    if z != zs[-1]:
                        self.subpath_index_bars.append(len(self.subpaths))
                    xs, ys, zs = [x0, x1], [y0, y1], [z, z]
                else:
                    xs.append(x1)
                    ys.append(y1)
                    zs.append(z)
            if len(xs) != 0:
                self.subpaths.append((xs, ys, zs))
            self.subpath_index_bars.append(len(self.subpaths))
            # print(self.subpath_index_bars)
            # print(self.segs)
    """
    def plot(self, color='blue', ax=None):
        # plot the whole part in 3D
        if not ax:
            fig, ax = create_axis(projection='3d')
        assert(self.n_segs > 0)
        self._compute_subpaths()
        for xs, ys, zs in self.subpaths:
            ax.plot(xs, ys, zs)
        return fig, ax

    def plot_layers(self, min_layer, max_layer, ax=None):
        # plot the layers in [min_layer, max_layer) in 3D
        if (min_layer >= max_layer or min_layer < 1 or max_layer >
                self.n_layers + 1):
            raise LayerError("Layer number is invalid!")
        self._compute_subpaths()
        if not ax:
            fig, ax = create_axis(projection='3d')
        left, right = (self.subpath_index_bars[min_layer - 1],
                       self.subpath_index_bars[max_layer - 1])
        for xs, ys, zs in self.subpaths[left: right]:
            ax.plot(xs, ys, zs)
        return fig, ax

    def plot_layer(self, layer=1, ax=None):
        # plot a specific layer in 2D
        # make sure layer is in [1, self.n_layers]
        # layer = max(layer, 1)
        # layer = min(self.n_layers, layer)
        if layer < 1 or layer > self.n_layers:
            raise LayerError("Layer number is invalid!")
        self._compute_subpaths()
        if not ax:
            fig, ax = create_axis(projection='2d')
        left, right = (self.subpath_index_bars[layer - 1],
                       self.subpath_index_bars[layer])
        for xs, ys, _ in self.subpaths[left: right]:
            ax.plot(xs, ys)
        return fig, ax
    """
    def describe_mesh(self, max_length):
        """print basic information of meshing"""
        if not self.elements:
            self.mesh(max_length)
        self.mesh_lengths = [np.hypot(x1 - x0, y1 - y0) for x0, y0, x1, y1, _
                             in self.elements]
        series = pd.Series(self.mesh_lengths)
        print('1. Element length information:')
        print(series.describe())
        print('2. Number of layers: {:d}'.format(self.n_layers))
        data = {'# elements': np.array(self.elements_index_bars[1:]) -
                np.array(self.elements_index_bars[:-1]),
                'layer': np.arange(1, self.n_layers + 1),
                }
        df = pd.DataFrame(data)
        df = df.set_index('layer')
        print(df)

    def describe(self):
        """print basic information of process plan"""
        if not self.summary:
            self.lengths = [np.hypot(x1 - x0, y1 - y0) for x0, y0, x1, y1, _
                            in self.segs]
            series = pd.Series(self.lengths)
            self.summary = series.describe()
        print('1. Line segments information: ')
        print(self.summary)
        print('2. Number of layers: {:d}'.format(self.n_layers))
        self._compute_subpaths()
        # print(len(self.seg_index_bars))
        # print(len(self.subpath_index_bars))
        data = {'# of segments': np.array(self.seg_index_bars[1:]) -
                np.array(self.seg_index_bars[:-1]),
                'layer': np.arange(1, self.n_layers + 1),
                '# of subpaths': np.array(self.subpath_index_bars[1:]) -
                np.array(self.subpath_index_bars[:-1]),
                }
        df = pd.DataFrame(data)
        df = df.set_index('layer')
        print(df)
        print('3. Other information: ')
        print('Total path length equals {:0.4f}.'.format(sum(self.lengths)))
        # compute total travel lengths
        travels = []
        for i in range(len(self.subpaths) - 1):
            xsi, ysi, zsi = self.subpaths[i]
            xsj, ysj, zsj = self.subpaths[i + 1]
            travels.append(abs(xsj[0] - xsi[-1]) + abs(ysj[0] - ysi[-1])
                           + abs(zsj[0] - zsi[-1]))
        print("Total travel length equals {:0.4f}.".format(sum(travels)))
        if self.filetype == GcodeType.LPBF:
            print("Laser power range [{}, {}]".format(
                min(self.powers), max(self.powers)))
        print("Number of nozzle travels equals {:d}.".format(
            len(self.subpaths)))
        print("Number of subpaths equals {:d}.".format(len(self.subpaths)))
        print("X, Y and Z limits: [{:0.2f}, {:0.2f}] X [{:0.2f}, {:0.2f}] X [{:0.2f}, {:0.2f}]".format(
            *self.xyzlimits))
    """
    def animate_layer(self, layer=1, animation_time=5, outfile=None):

        #animate the printing of a specific layer in 2D

        if layer < 1 or layer > self.n_layers:
            raise LayerError("Layer number is invalid!")
        fig, ax = create_axis(projection='2d')
        if outfile:
            writer = create_movie_writer()
            writer.setup(fig, outfile=outfile, dpi=100)
        xmin, xmax, ymin, ymax, _, _ = self.xyzlimits
        # ax.set_xlim([xmin, xmax])
        # ax.set_ylim([ymin, ymax])
        ax.set_xlim(add_margin_to_axis_limits(xmin, xmax))
        ax.set_ylim(add_margin_to_axis_limits(ymin, ymax))
        left, right = (self.seg_index_bars[layer - 1],
                       self.seg_index_bars[layer])
        seg_lst = self.segs[left: right]
        lens = np.array([abs(x0 - x1) + abs(y0 - y1) for x0, y0, x1, y1, z in
                         seg_lst])
        times = lens / lens.sum() * animation_time
        # print(times.sum())
        for time, (x0, y0, x1, y1, _) in zip(times, seg_lst):
            ax.plot([x0, x1], [y0, y1], 'b-')
            plt.pause(time)
            if outfile:
                writer.grab_frame()
            plt.draw()
        if outfile:
            writer.finish()
            print('Creating movie {:s}'.format(outfile))
        plt.show()

    def animate_layers(self, min_layer, max_layer=None, outfile=None):

        #animation of the print process of multiple layers [min_layer,
        #max_layer)
        #implement with plt.pause() and plt.draw()

        if max_layer is None:
            max_layer = self.n_layers + 1
        if (min_layer >= max_layer or min_layer < 1 or max_layer >
                self.n_layers + 1):
            raise LayerError("Layer number is invalid!")
        left, right = (self.subpath_index_bars[min_layer - 1],
                       self.subpath_index_bars[max_layer - 1])
        fig, ax = create_axis(projection='3d')
        if outfile:
            writer = create_movie_writer()
            writer.setup(fig, outfile=outfile, dpi=100)
        xmin, xmax, ymin, ymax, zmin, zmax = self.xyzlimits
        ax.set_xlim([xmin, xmax])
        ax.set_ylim([ymin, ymax])
        if zmax > zmin:
            ax.set_zlim([zmin, zmax])
        for sub_path in self.subpaths[left:right]:
            xs, ys, zs = sub_path
            ax.plot(xs, ys, zs)
            if outfile:
                writer.grab_frame()
            plt.pause(0.1)
            plt.draw()
        if outfile:
            writer.finish()
            print('Creating movie {:s}'.format(outfile))
        plt.show()
    """
