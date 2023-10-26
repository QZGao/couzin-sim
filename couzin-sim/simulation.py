import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal


class Simulation:
    """ Simulation class

        Parameters:
        * num_preys: number of preys
        * num_predators: number of predators
        * canvas_size: size of the canvas
        * gen_bound: generation bound
        * speed_preys: speed of preys
        * speed_predators: speed of predators
        * repulse_factor_preys: repulsion factor of preys
        * repulse_factor_predators: repulsion factor of predators
        * max_turning_angle: maximum turning angle
    """

    def __init__(self, num_preys, num_predators, canvas_size, gen_bound, speed_preys, speed_predators, repulse_factor_preys, repulse_factor_predators, max_turning_angle):
        self.reset(num_preys, num_predators, canvas_size, gen_bound, speed_preys, speed_predators, repulse_factor_preys, repulse_factor_predators, max_turning_angle)

    def reset(self, num_preys, num_predators, canvas_size, gen_bound, speed_preys, speed_predators, repulse_factor_preys, repulse_factor_predators, max_turning_angle):
        # Set simulation parameters
        self.num_preys = num_preys
        self.num_predators = num_predators
        self.canvas_size = canvas_size
        self.gen_bound = gen_bound
        self.speed_preys = speed_preys
        self.speed_predators = speed_predators
        self.repulse_factor_preys = repulse_factor_preys
        self.repulse_factor_predators = repulse_factor_predators
        self.max_turning_angle = max_turning_angle

        # Initialize preys and predators
        self.init_preys()
        self.init_predators()

    # Initialize preys
    def init_preys(self):
        self.preys = np.random.uniform(
            (0.5 - self.gen_bound) * self.canvas_size,
            (0.5 + self.gen_bound) * self.canvas_size,
            size=(self.num_preys, 2)
        )
        self.preys_speeds = np.random.normal(0, 1, size=(self.num_preys, 2))
        self.preys_speeds = self.speed_preys * self.preys_speeds / np.linalg.norm(self.preys_speeds, axis=1,
                                                                                  keepdims=True)
        self.preys_eaten = np.zeros(self.num_preys, dtype=bool)

    # Initialize predators
    def init_predators(self):
        self.predators = np.random.uniform(
            (0.5 - self.gen_bound) * self.canvas_size,
            (0.5 + self.gen_bound) * self.canvas_size,
            size=(self.num_predators, 2)
        )
        self.predators_speeds = np.random.normal(0, 1, size=(self.num_predators, 2))
        self.predators_speeds = self.speed_predators * self.predators_speeds / np.linalg.norm(self.predators_speeds,
                                                                                              axis=1, keepdims=True)

    # Distance squared
    def distances(self, pos_A, pos_B):
        """ Calculate distances between A and B

            Parameters:
            * pos_A: (N, 2) array of positions of A
            * pos_B: (M, 2) array of positions of B

            Returns:
            * (N, M) array of distances between A and B
        """
        # Calculate distances between A and B
        dx = pos_B[:, 0] - pos_A[:, 0, np.newaxis]
        dx = np.where(dx > self.canvas_size / 2, dx - self.canvas_size, dx)
        dx = np.where(dx < -self.canvas_size / 2, dx + self.canvas_size, dx)
        dy = pos_B[:, 1] - pos_A[:, 1, np.newaxis]
        dy = np.where(dy > self.canvas_size / 2, dy - self.canvas_size, dy)
        dy = np.where(dy < -self.canvas_size / 2, dy + self.canvas_size, dy)
        distances = dx ** 2 + dy ** 2
        return distances, dx, dy


    def attract(self, pos_A, pos_B, k, isSame):
        """ Calculate the attraction force from B to A

            Parameters:
            * pos_A: (N, 2) array of positions of A
            * pos_B: (M, 2) array of positions of B
            * k: number of closest B to follow
            * isSame: whether A and B are the same

            Returns:
            * (N, 2) array of attraction forces from B to A
        """
        d2, dx, dy = self.distances(pos_A, pos_B)

        # Filter out eaten preys: set their distances to infinity
        if len(pos_B) == self.num_preys:
            d2[:, self.preys_eaten] = self.canvas_size * 100
        # Filter out itself: set self-distances to infinity
        if isSame:
            np.fill_diagonal(d2, self.canvas_size * 100)

        # Find the closest B to follow for each A
        num_closest = min(len(pos_B), k)
        closest_idxs = np.argpartition(d2, num_closest - 1, axis=1)[:, :num_closest]
        closest_dx = dx[np.arange(len(pos_A))[:, np.newaxis], closest_idxs]
        closest_dy = dy[np.arange(len(pos_A))[:, np.newaxis], closest_idxs]

        d3 = d2[np.arange(len(pos_A))[:, np.newaxis], closest_idxs] ** (3 / 2)  # |d|^3
        d3[d3 == 0] = 1e-5  # Avoid division by zero

        dn2 = np.sum(np.stack([closest_dx, closest_dy], axis=2), axis=1) / d3.sum(axis=1)[:, np.newaxis]  # d / |d|^3
        dn2_norm = np.linalg.norm(dn2, axis=1)
        return dn2 / dn2_norm[:, np.newaxis]


    def repulse(self, pos_A, pos_B, k, isSame):
        """ Calculate the repulsion force from B to A

            Parameters:
            * pos_A: (N, 2) array of positions of A
            * pos_B: (M, 2) array of positions of B
            * k: number of closest B to follow
            * isSame: whether A and B are the same

            Returns:
            * (N, 2) array of repulsion forces from B to A
        """
        return -self.attract(pos_A, pos_B, k, isSame)


    def turning(self, old_speed: np.ndarray, new_speed: np.ndarray, norm_speed: float, max_turning_angle: float):
        """ Limit the turning angle of new_speed to the maximum allowed turning angle

            Parameters:
            * old_speed: (N, 2) array of old speeds
            * new_speed: (N, 2) array of new speeds
            * norm_speed: norm of speeds
            * max_turning_angle: maximum allowed turning angle

            Return:
            * (N, 2) array of new speeds with limited turning angle
        """
        # Compute the angle between old_speed and new_speed
        cos_theta = np.sum(old_speed * new_speed, axis=1) / np.linalg.norm(old_speed, axis=1) / np.linalg.norm(
            new_speed, axis=1)
        theta = np.arccos(np.clip(cos_theta, -1, 1))

        # Check invalid theta
        theta[np.isnan(theta) | (theta == 0)] = 1e-5

        # Limit the turning angle to the maximum allowed turning angle
        max_theta = np.clip(theta, 0, max_turning_angle)
        alpha = max_theta / theta

        # Compute the new speed with limited turning angle
        new_speed_limited = alpha[:, np.newaxis] * new_speed + (1 - alpha[:, np.newaxis]) * old_speed

        # Normalize the resulting vector to ensure it has the same norm as the original vectors
        new_norms = np.linalg.norm(new_speed_limited, axis=1)
        new_direction = new_speed_limited / new_norms[:, np.newaxis]

        return new_direction * norm_speed



    def update_preys(self):
        """ Update preys' positions and speeds
        """
        self.preys += self.preys_speeds
        self.preys %= self.canvas_size

        # Find the closest predator to dodge
        new_speeds = self.repulse(self.preys, self.predators, 1, False)

        # Find the closest prey to dodge too
        new_speeds += self.repulse(self.preys, self.preys, 3, True) * self.repulse_factor_preys
        new_speeds /= np.linalg.norm(new_speeds, axis=1)[:, np.newaxis]  # Normalize

        # Add noise
        new_speeds += np.random.normal(0, 1e-3, (self.num_preys, 2))
        new_speeds /= np.linalg.norm(new_speeds, axis=1)[:, np.newaxis]  # Normalize

        # Update speeds
        self.preys_speeds = self.turning(self.preys_speeds,
                                         new_speeds,
                                         self.speed_preys,
                                         self.max_turning_angle)

    def update_predators(self):
        """ Update predators' positions and speeds
        """
        self.predators += self.predators_speeds
        self.predators %= self.canvas_size

        # Eat preys
        prey_distances, _, _ = self.distances(self.predators, self.preys)
        preys_within_range = np.any(prey_distances < self.speed_predators ** 2, axis=0)
        self.preys_eaten[preys_within_range] = True

        # If all preys are eaten
        if self.all_preys_eaten():
            return

        # Find the closest prey to pursue
        new_speeds = self.attract(self.predators, self.preys, 1, False)

        # Find the closest predator to dodge
        new_speeds += self.repulse(self.predators, self.predators, 3, True) * self.repulse_factor_predators
        new_speeds /= np.linalg.norm(new_speeds, axis=1)[:, np.newaxis]  # Normalize

        # Add noise
        new_speeds += np.random.normal(0, 1e-3, (self.num_predators, 2))
        new_speeds /= np.linalg.norm(new_speeds, axis=1)[:, np.newaxis]  # Normalize

        self.predators_speeds = self.turning(self.predators_speeds,
                                             new_speeds,
                                             self.speed_predators,
                                             self.max_turning_angle)

    def update(self):
        """ Update the positions and speeds of preys and predators
        """
        self.update_preys()
        self.update_predators()

    def all_preys_eaten(self):
        """ Check if all preys are eaten
        """
        return np.all(self.preys_eaten)

    def current_num_preys(self):
        """ Return the current number of preys alive
        """
        return np.sum(~self.preys_eaten)


class Calc_corr(QThread):
    """ Calculate the correlation function of the system

        Parameters:
        * pos: (N, 2) array of positions
        * vel: (N, 2) array of velocities
        * num: number of particles
        * canvas_size: size of the canvas
        * resolution: resolution of the correlation function
    """

    signal = pyqtSignal(np.ndarray)

    def __init__(self, pos: np.ndarray, vel: np.ndarray, num: int, canvas_size: int, resolution: int, crop: int):
        super(Calc_corr, self).__init__()
        self.pos = pos # Eaten preys have already deleted before assigning to this variable
        self.vel = vel
        self.num = num
        self.canvas_size = canvas_size
        self.resolution = resolution
        self.crop = crop

    def __del__(self):
        self.wait()

    def dirac(self, x, epsilon=1e-6):
        return 0.5 + 0.5 * np.tanh (x / epsilon)

    def run(self):
        con_corr = np.zeros(self.resolution)

        delta_vel = self.vel - np.sum(self.vel, axis=0) / self.num
        delta_phi = delta_vel / np.sqrt(np.sum(delta_vel * delta_vel, axis=0) / self.num)

        # Calculate distances
        dx = self.pos[:, 0] - self.pos[:, 0, np.newaxis]
        dx = np.where(dx > self.canvas_size / 2, dx - self.canvas_size, dx)
        dx = np.where(dx < -self.canvas_size / 2, dx + self.canvas_size, dx)
        dy = self.pos[:, 1] - self.pos[:, 1, np.newaxis]
        dy = np.where(dy > self.canvas_size / 2, dy - self.canvas_size, dy)
        dy = np.where(dy < -self.canvas_size / 2, dy + self.canvas_size, dy)
        distances = np.sqrt(dx ** 2 + dy ** 2)

        # List of R as variables
        var_r = np.arange(self.resolution) * (self.canvas_size * self.crop / self.resolution)
        var_r = var_r[:, np.newaxis, np.newaxis]

        # Calculate correlation function
        matrix_phi = np.dot(delta_phi, delta_phi.T)
        np.fill_diagonal(matrix_phi, 0)
        result_matrix = matrix_phi * self.dirac(var_r - distances)

        con_corr = np.sum(result_matrix, axis=(1,2)) / np.sum(self.dirac(var_r - distances), axis=(1,2))

        self.signal.emit(con_corr)
