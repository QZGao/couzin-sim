import numpy as np
from math import ceil
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.offsetbox import AnchoredText

from PyQt5.QtCore import Qt
from qfluentwidgets import InfoBar, InfoBarPosition

from simulation import Simulation, Calc_corr


class MplCanvas(FigureCanvas):
    """ Main matplotlib canvas

        Parameters:
        * parent: parent widget
        * width: width of the canvas
        * height: height of the canvas
        * dpi: dpi of the canvas
    """

    def __init__(self, parent=None, width=16, height=16, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        # self.fig.tight_layout(rect=(0.05, 0.05, 0.95, 0.95))

        FigureCanvas.__init__(self, self.fig)
        self.parent = parent

        # Parameters
        self.canvas_size = int(self.parent.cfg.config_canvas_size.value)
        self.num_predatory = int(self.parent.cfg.config_num_predatory.value)
        self.num_prey = int(self.parent.cfg.config_num_prey.value)
        self.k_predatory = float(self.parent.cfg.config_k_predatory.value)
        self.k_prey = float(self.parent.cfg.config_k_prey.value)
        self.v_prey = int(self.parent.cfg.config_v_prey.value)
        self.v_predatory = int(self.parent.cfg.config_v_predatory.value)
        self.resolution = int(self.parent.cfg.config_resolution.value)
        self.crop = float(self.parent.cfg.config_crop.value)
        self.gen_bound = float(self.parent.cfg.config_bound.value) / 100
        self.max_turning_angle = int(self.parent.cfg.config_max_turning_angle.value) / 180 * np.pi

        # Initialize
        self.simulation = Simulation(self.num_prey, self.num_predatory, self.canvas_size, self.gen_bound, self.v_prey,
                                     self.v_predatory, self.k_prey, self.k_predatory, self.max_turning_angle)

        # Plot axes status
        self.ax1 = self.fig.add_subplot(221)
        self.ax1.set_xlim(0, self.canvas_size)
        self.ax1.set_ylim(0, self.canvas_size)
        self.plot1_status = self.parent.cfg.config_plot1_show.value
        self.plot1_framerate = int(self.parent.cfg.config_plot1_framerate.value)

        self.ax2 = self.fig.add_subplot(222)
        self.ax2.set_ylim(0, 1)
        self.ax2.set_xlim(0, 100)
        self.plot2_status = self.parent.cfg.config_plot2_show.value
        self.plot2_framerate = int(self.parent.cfg.config_plot2_framerate.value)
        self.last_p = 0.
        self.plot2_caught_label_shown = False

        self.ax3 = self.fig.add_subplot(223)
        self.ax3.set_ylim(-1, 1)
        self.ax3.set_xlim(0, self.crop * self.canvas_size)
        self.plot3_status = self.parent.cfg.config_plot3_show.value
        self.plot3_framerate = int(self.parent.cfg.config_plot3_framerate.value)
        self.plot3_sample = int(self.parent.cfg.config_plot3_sample.value)
        self.con_corr_list = []
        self.thread_list = []

        self.ax4 = self.fig.add_subplot(224)
        self.ax4.set_ylim(0, 5000)
        self.ax4.set_xlim(0, 100)
        self.plot4_status = self.parent.cfg.config_plot4_show.value
        self.plot4_framerate = int(self.parent.cfg.config_plot4_framerate.value)
        self.last_dis = 0.
        self.dis_upperbound = 5000

        self.fig.tight_layout(pad=7)

    def updateCanvas(self, time: int):
        """ Update canvas

            Parameters:
            * time: current time
        """

        if self.plot1_status:
            if time % self.plot1_framerate == 0:
                self.plot1(time,
                           self.simulation.predators,
                           self.simulation.preys,
                           self.simulation.predators_speeds,
                           self.simulation.preys_speeds,
                           self.canvas_size)

        if time % self.plot2_framerate == 0:
            if self.parent.cfg.config_plot2_target.value == 'Predators':
                self.plot2(time,
                           self.simulation.predators_speeds,
                           self.simulation.speed_predators,
                           self.simulation.num_predators)

            else:
                self.plot2(time,
                           self.simulation.preys_speeds,
                           self.simulation.speed_preys,
                           self.simulation.num_preys)

        if self.plot3_status:
            if len(self.con_corr_list) >= self.plot3_sample:
                self.plot3(time, self.con_corr_list)
                self.con_corr_list = []

        if time % self.plot4_framerate == 0:
            if self.parent.cfg.config_plot4_target.value == 'Predators':
                distances, _, _ = self.simulation.distances(self.simulation.predators, self.simulation.predators)
            else:
                distances, _, _ = self.simulation.distances(self.simulation.preys, self.simulation.preys)

            distances = np.sqrt(distances)
            num = np.shape(distances)[0]
            dis = np.sum(distances) / (num * (num - 1) / 2)
            self.plot4(time, dis)

        if self.plot3_status:
            if time % self.plot3_framerate >= (self.plot3_framerate - self.plot3_sample):
                if self.parent.cfg.config_plot3_target.value == 'Predators':
                    self.thread_list.append(Calc_corr(self.simulation.predators,
                                                      self.simulation.predators_speeds,
                                                      self.simulation.num_predators,
                                                      self.canvas_size,
                                                      self.resolution, self.crop))
                else:
                    self.thread_list.append(Calc_corr(self.simulation.preys,
                                                      self.simulation.preys_speeds,
                                                      self.simulation.num_preys,
                                                      self.canvas_size,
                                                      self.resolution, self.crop))
                self.thread_list[-1].signal.connect(self.calc_corr_callback)
                self.thread_list[-1].start()

                at = AnchoredText(f"Sampling ({len(self.con_corr_list) / self.plot3_sample * 100 :.0f}%)",
                                  prop=dict(size=15), frameon=True, loc='center')
                at.patch.set_boxstyle("round,pad=0.,rounding_size=0.2")
                self.ax3.add_artist(at)

        old_num_preys = self.simulation.current_num_preys()
        self.simulation.update()
        new_num_preys = self.simulation.current_num_preys()

        if old_num_preys > new_num_preys:

            word_choice = f'{self.num_prey - old_num_preys + 1} - {self.num_prey - new_num_preys} were'
            if old_num_preys - new_num_preys == 1:
                word_choice = f'{self.num_prey - new_num_preys} was'

            InfoBar.success(
                title='Caught',
                content=f"At step {time}, prey No. {word_choice} caught.",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_LEFT,
                duration=2000,
                parent=self
            )

            # Write event to output
            if bool(self.parent.cfg.config_output.value):
                with open('output/event.txt', 'a', encoding='utf-8') as f:
                    f.write(f"Caught: Time = {time}, Remain = {new_num_preys}\n")

            self.plot2_caught(time)

        if self.simulation.all_preys_eaten():
            InfoBar.success(
                title='All caught',
                content=f"At step {time}, all preys were caught.",
                orient=Qt.Horizontal,
                isClosable=True,  # disable close button
                position=InfoBarPosition.TOP_LEFT,
                duration=2000,
                parent=self
            )

            # Write event to output
            if bool(self.parent.cfg.config_output.value):
                with open('output/event.txt', 'a', encoding='utf-8') as f:
                    f.write(f"Caught: Time = {time}, Remain = none\n")

            try:
                self.plot1(time,
                           self.simulation.predators,
                           self.simulation.preys,
                           self.simulation.preys_speeds,
                           self.simulation.predators_speeds,
                           self.canvas_size)
            except:
                pass
            return True

        return False

    # Plot 1: Simulation
    def plot1(self, time: int, Pos_predator: np.ndarray, Pos_prey: np.ndarray, Vel_predator: np.ndarray,
              Vel_prey: np.ndarray, r: int):
        """ Plot the simulation of the predator-prey system.

            Parameters:
            * time: The current time.
            * Pos_predator: (N, 2) array of the positions of the predators.
            * Pos_prey: (N, 2) array of the positions of the preys.
            * Vel_predator: (N, 2) array of the velocities of the predators.
            * Vel_prey: (N, 2) array of the velocities of the preys.
            * r: The radius of the predators and the preys.
        """

        # Output to file
        if bool(self.parent.cfg.config_output.value):
            with open('output/plot1.txt', 'a', encoding='utf-8') as f:
                f.write(
                    f'Time: {time}\nPredators: {Pos_predator}\nPreys: {Pos_prey}\nPredators speeds: {Vel_predator}\nPreys speeds: {Vel_prey}\n')

        self.ax1.clear()

        # Delete eaten preys
        Pos_prey = np.delete(Pos_prey, self.simulation.preys_eaten, axis=0)
        Vel_prey = np.delete(Vel_prey, self.simulation.preys_eaten, axis=0)

        marker_size = int(self.parent.cfg.config_plot1_marker_size.value)
        if self.parent.cfg.config_plot1_marker.value == 'Arrows':
            self.ax1.quiver(Pos_predator[:, 0], Pos_predator[:, 1], Vel_predator[:, 0], Vel_predator[:, 1], color='red',
                            width=marker_size * 8e-4)
            self.ax1.quiver(Pos_prey[:, 0], Pos_prey[:, 1], Vel_prey[:, 0], Vel_prey[:, 1], color='black',
                            width=marker_size * 8e-4)
        else:
            self.ax1.scatter(Pos_predator[:, 0], Pos_predator[:, 1], color='red', alpha=0.5, s=marker_size * 2)
            self.ax1.scatter(Pos_prey[:, 0], Pos_prey[:, 1], color='green', alpha=0.5, s=marker_size * 2)

        if bool(self.parent.cfg.config_plot1_scroll.value):
            try:
                pos_left = np.nanmin([np.nanmin(Pos_predator[:, 0]), np.nanmin(Pos_prey[:, 0])])
                if not np.isfinite(pos_left):
                    pos_left = 0
                pos_right = np.nanmax([np.nanmax(Pos_predator[:, 0]), np.nanmax(Pos_prey[:, 0])])
                if not np.isfinite(pos_right):
                    pos_right = r
                pos_top = np.nanmin([np.nanmin(Pos_predator[:, 1]), np.nanmin(Pos_prey[:, 1])])
                if not np.isfinite(pos_top):
                    pos_top = 0
                pos_bottom = np.nanmax([np.nanmax(Pos_predator[:, 1]), np.nanmax(Pos_prey[:, 1])])
                if not np.isfinite(pos_bottom):
                    pos_bottom = r

                pos_lr = pos_right - pos_left
                pos_tb = pos_bottom - pos_top
                pos_left = max(0, pos_left - pos_lr * 0.05)
                pos_right = min(r, pos_right + pos_lr * 0.05)
                pos_top = max(0, pos_top - pos_tb * 0.05)
                pos_bottom = min(r, pos_bottom + pos_tb * 0.05)

                self.ax1.set_xlim(pos_left, pos_right)
                self.ax1.set_ylim(pos_top, pos_bottom)
            except:
                pass
        else:
            self.ax1.set_xlim(0, r)
            self.ax1.set_ylim(0, r)

        self.ax1.set_xlabel('$x$')
        self.ax1.set_ylabel('$y$')
        self.ax1.set_title(f'Simulation (Time: {time})')
        self.draw_idle()

    # Plot 2: Group polarization
    def plot2(self, time: int, vel: np.ndarray, v: float, num: int):
        """ Plot the group polarization of the predators / preys.

            Parameters:
            * time: The current time.
            * vel: (N, 2) array of the velocities of the predators / preys.
            * v: The speed of the predators / preys.
            * num: The number of the predators / preys.
        """

        p = np.linalg.norm(np.sum(vel / v, axis=0)) / num

        # Output to file
        if bool(self.parent.cfg.config_output.value):
            with open('output/plot2.txt', 'a', encoding='utf-8') as f:
                f.write(f'{time},{p}\n')

        self.ax2.plot([time - self.plot2_framerate, time], [self.last_p, p], color='C0')
        self.last_p = p
        right_most = ceil(time / 100) * 100

        self.ax2.set_xlim(max(right_most - 1000, 0), right_most)
        self.ax2.set_xlabel('Time $t$')
        self.ax2.set_ylabel('Polarization')
        if self.parent.cfg.config_plot2_target.value == 'Predators':
            self.ax2.set_title('Group polarization of predators')
        else:
            self.ax2.set_title('Group polarization of preys')
        self.draw_idle()

    def plot2_caught(self, time: int):
        """ Plot the vertical line on ax2 when a prey is caught.

            Parameters:
            * time: The current time.
        """

        if self.plot2_caught_label_shown:
            self.ax2.vlines(time, ymin=0, ymax=1, ls='--', lw=1, color='C1')
        else:
            self.ax2.vlines(time, ymin=0, ymax=1, ls='--', lw=1, color='C1', label='A prey getting caught')
            self.ax2.legend()
            self.plot2_caught_label_shown = True
        self.draw_idle()

    # Plot 3: Correlation function
    def plot3(self, time: int, con_corr_list: list):
        """ Plot the correlation function of the predators / preys.

            Parameters:
            * con_corr_list: A list of the correlation functions of the predators / preys.
        """
        self.ax3.clear()

        con_corr = np.mean(con_corr_list, axis=0)

        # Output to file
        if bool(self.parent.cfg.config_output.value):
            with open('output/plot3.txt', 'a', encoding='utf-8') as f:
                f.write(f'Time: {time}\n{con_corr}\n')

        x2 = np.linspace(0, self.canvas_size * self.crop, self.resolution)
        self.ax3.clear()
        self.ax3.plot(x2, con_corr)
        y_lower, y_upper = self.ax3.get_ylim()
        if self.parent.cfg.config_plot4_target.value == 'Predators':
            label = 'Average distance between predators'
        else:
            label = 'Average distance between preys'
        self.ax3.vlines(self.last_dis, ymin=y_lower, ymax=y_upper, ls='--', lw=1, color='C1', label=label)
        self.ax3.hlines(0, xmin=0, xmax=self.canvas_size * self.crop, ls=':', lw=1, color='black')
        self.ax3.legend()
        self.ax3.set_xlim(0, self.canvas_size * self.crop)
        self.ax3.set_ylim(y_lower, y_upper)
        self.ax3.set_xlabel('Distance $R$')
        self.ax3.set_ylabel('Correlation $C(R)$')
        if self.parent.cfg.config_plot3_target.value == 'Predators':
            self.ax3.set_title('Correlation function of predators')
        else:
            self.ax3.set_title('Correlation function of preys')
        self.draw_idle()

    def calc_corr_callback(self, con_corr: np.ndarray):
        """ Callback function for calculating the correlation function.

            Parameters:
            * con_corr: The correlation function of the predators / preys.
        """
        self.con_corr_list.append(con_corr)

    # Plot 4: Average distance
    def plot4(self, time: int, dis: float):
        """ Plot the average distance of the predators / preys.

            Parameters:
            * time: The current time.
            * dis: The average distance of the predators / preys.
        """

        # Output to file
        if bool(self.parent.cfg.config_output.value):
            with open('output/plot4.txt', 'a', encoding='utf-8') as f:
                f.write(f'{time},{dis}\n')

        self.dis_upperbound = max(self.dis_upperbound, dis)
        self.ax4.plot([time - self.plot4_framerate, time], [self.last_dis, dis], color='C0')
        self.last_dis = dis
        right_most = ceil(time / 100) * 100
        self.ax4.set_xlim(max(right_most - 1000, 0), right_most)
        self.ax4.set_ylim(0, self.dis_upperbound + 200)
        self.ax4.set_xlabel('Time $t$')
        self.ax4.set_ylabel('Average distance')
        if self.parent.cfg.config_plot4_target.value == 'Predators':
            self.ax4.set_title('Average distance between predators')
        else:
            self.ax4.set_title('Average distance between preys')
        self.draw_idle()

    # Show or hide plots
    def changePlotStatus(self, plot, status):
        if plot == 1:
            self.plot1_status = status
            self.ax1.set_visible(status)
        elif plot == 2:
            self.plot2_status = status
            self.ax2.set_visible(status)
        elif plot == 3:
            self.plot3_status = status
            self.ax3.set_visible(status)
        elif plot == 4:
            self.plot4_status = status
            self.ax4.set_visible(status)

        self.draw_idle()
