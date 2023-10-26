from qfluentwidgets import QConfig, ConfigItem, OptionsConfigItem, BoolValidator, OptionsValidator
from qfluentwidgets.common import ConfigValidator


class BetterRangeValidator(ConfigValidator):
    """ A validator for the BetterRangeConfigItem.

        Parameters:
        * min: The minimum value.
        * max: The maximum value.
        * step: The step size.
    """
    def __init__(self, min, max, step=1):
        self.min = min
        self.max = max
        self.step = step
        self.range = (min, max)

    def validate(self, value):
        try:
            return self.min <= float(value) <= self.max
        except:
            return False

    def correct(self, value):
        try:
            return str(min(max(self.min, int(float(value)/self.step)*self.step), self.max))
        except:
            return str(self.min)

class BetterRangeConfigItem(ConfigItem):
    """ A config item with a range.

        Parameters:
        * caption: The caption of the config item.
        * content: The content of the config item.
        * value: The value of the config item.
        * validator: The validator of the config item.
    """

    @property
    def range(self):
        return self.validator.range

    @property
    def step(self):
        return self.validator.step

    def __str__(self):
        return f'{self.__class__.__name__}[range={self.range}, value={self.value}]'


class Config(QConfig):
    """ The config of the simulation. """

    # Canvas
    config_canvas_size = BetterRangeConfigItem(
        'Canvas', 'Canvas size',
        500000, BetterRangeValidator(1000, 10000000)
    )
    config_framerate = BetterRangeConfigItem(
        'Canvas', 'Step wait time (ms)',
        100, BetterRangeValidator(1, 60000)
    )
    config_num_predatory = BetterRangeConfigItem(
        'Canvas', 'Number of predators',
        20, BetterRangeValidator(1, 100000)
    )
    config_num_prey = BetterRangeConfigItem(
        'Canvas', 'Number of preys',
        200, BetterRangeValidator(1, 100000)
    )
    config_k_predatory = BetterRangeConfigItem(
        'Canvas', 'Repulsion parameter of predators',
        0.1, BetterRangeValidator(0., 1., 0.001)
    )
    config_k_prey = BetterRangeConfigItem(
        'Canvas', 'Repulsion parameter of preys',
        0.1, BetterRangeValidator(0., 1., 0.001)
    )
    config_v_prey = BetterRangeConfigItem(
        'Canvas', 'Velocity of preys',
        20, BetterRangeValidator(10, 100000)
    )
    config_v_predatory = BetterRangeConfigItem(
        'Canvas', 'Velocity of predators',
        20, BetterRangeValidator(10, 100000)
    )
    config_bound = BetterRangeConfigItem(
        'Canvas', 'Initial generation boundaries',
        0.5, BetterRangeValidator(0.001, 100., 0.001)
    )
    config_max_turning_angle = BetterRangeConfigItem(
        'Canvas', 'Maximum turning angle',
        30, BetterRangeValidator(1, 180)
    )

    # Plot 1
    config_plot1_show = ConfigItem(
        'Simulation plot', 'Show plot',
        True, BoolValidator()
    )
    config_plot1_framerate = BetterRangeConfigItem(
        'Simulation plot', 'Update interval',
        1, BetterRangeValidator(1, 1000)
    )
    config_plot1_marker = OptionsConfigItem(
        'Simulation plot', 'Markers',
        'Arrows', OptionsValidator(['Arrows', 'Dots'])
    )
    config_plot1_marker_size = BetterRangeConfigItem(
        'Simulation plot', 'Marker size',
        6, BetterRangeValidator(1, 100)
    )
    config_plot1_scroll = ConfigItem(
        'Simulation plot', 'Enable auto-scrolling',
        True, BoolValidator()
    )

    # Plot 2
    config_plot2_show = ConfigItem(
        'Group polarization plot', 'Show plot',
        True, BoolValidator()
    )
    config_plot2_target = OptionsConfigItem(
        'Group polarization plot', 'Target',
        'Preys', OptionsValidator(['Preys', 'Predators'])
    )
    config_plot2_framerate = BetterRangeConfigItem(
        'Group polarization plot', 'Update interval',
        10, BetterRangeValidator(1, 1000)
    )

    # Plot 3
    config_plot3_show = ConfigItem(
        'Correlation function plot', 'Show plot',
        True, BoolValidator()
    )
    config_plot3_target = OptionsConfigItem(
        'Correlation function plot', 'Target',
        'Preys', OptionsValidator(['Preys', 'Predators'])
    )
    config_plot3_framerate = BetterRangeConfigItem(
        'Correlation function plot', 'Update interval',
        100, BetterRangeValidator(1, 1000)
    )
    config_plot3_sample = BetterRangeConfigItem(
        'Correlation function plot', 'Sample size',
        20, BetterRangeValidator(1, 1000)
    )
    config_resolution = BetterRangeConfigItem(
        'Correlation function plot', 'Resolution',
        100, BetterRangeValidator(10, 1000)
    )
    config_crop = BetterRangeConfigItem(
        'Correlation function plot', 'Crop area',
        0.1, BetterRangeValidator(0.001, 1., 0.001)
    )

    # Plot 4
    config_plot4_show = ConfigItem(
        'Average distance plot', 'Show plot',
        True, BoolValidator()
    )
    config_plot4_target = OptionsConfigItem(
        'Average distance plot', 'Target',
        'Preys', OptionsValidator(['Preys', 'Predators'])
    )
    config_plot4_framerate = BetterRangeConfigItem(
        'Average distance plot', 'Update interval',
        10, BetterRangeValidator(1, 1000)
    )

    # Experimental
    config_dpi_scale = OptionsConfigItem(
        'Experimental', 'DPI scaling settings',
        'Auto', OptionsValidator(['Auto', '1', '1.25', '1.5', '1.75', '2']),
        restart=True
    )
    config_output = ConfigItem(
        'Experimental', 'Output',
        False, BoolValidator()
    )
