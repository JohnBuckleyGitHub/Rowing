import math
import kustom_widgets as kw
import active_excel
import copy


class boat(object):
    def __init__(self, count):
        self.mass_rowers = 92.5 * count
        self.mass_boat = 18.25 * count
        self.mass = 92.5 * count + 146
        self.res_alpha = 4 + .75 * count  # N s²/m²
        self.oar = oar(self, 8, 'coppel')
        self.stroke_rate = 30
        self.dist_last = 0
        self.pull_time = 0
        self.__init_record_params__()

    def recover(self, duration, fractions):
        t_step = duration / fractions
        for i in range(fractions):
            resistance_force = -self.res_alpha * self.speed**2
            self.acc = resistance_force / self.mass
            self.time += t_step
            self.pos += self.speed * t_step + .5 * self.acc * t_step**2
            self.speed += self.acc * t_step
        print("Recover:", "{:10.2f}".format(self.time), "{:10.2f}".format(self.pos),
              "{:10.2f}".format(self.speed), "{:10.2f}".format(self.acc))

    def __init_record_params__(self):
        self.speed = 6
        self.pos = 0
        self.time = 0
        self.record = []
        self.diplay_channels = {}
        self.diplay_channels[self] = ['time', 'pos', 'speed', 'acc']
        self.diplay_channels[self.oar] = ['deg', 'deg_speed', 'deg_acc', 'tang_speed', 'fluid_speed', 'pos_x', 'pos_y',
                                          'blade_vel_rel_x', 'blade_vel_y', 'blade_vel_x', 'deg_blade_vel_ref',
                                          'deg_oa', 'blade_fluid_normal_force', 'blade_fluid_axial_force',
                                          'blade_prop_force', 'deg_step', 'inertia_reaction_at_blade', 'cn', 'ca']

    def __record_list__(self):
        temp_dict = {}
        for t in self.diplay_channels.items():
            for channel in t[1]:
                temp_dict[channel] = getattr(t[0], channel)
        self.record.append(temp_dict)

    def compile_record(self):
        self.results = {}
        for i, rdict in enumerate(self.record):
            for t in self.diplay_channels.items():
                for channel in t[1]:
                    try:
                        self.results[channel].append(rdict[channel])
                    except KeyError:
                        self.results[channel] = [rdict[channel]]

    def get_state_params(self):
        self.state_params = (self.time, self.pos, self.speed, self.acc)
        print_params = ["{:.4f}".format(p) for p in self.state_params]
        return print_params

    def single_stroke(self, start_angle, end_angle):
        self.start_angle = d2r(start_angle, True)
        self.end_angle = d2r(end_angle, True)
        self.pull_force = 400
        self.max_vel_diff = .01
        self.min_ang_step = d2r(.001)
        self.max_ang_step = d2r(.5)
        self.__init_record_params__()
        self.stroke()
        # self.stroke_divisions = stroke_divisions

    def stroke(self):
        oar = self.oar
        oar.ang = r_semi(self.start_angle)
        oar.ang_speed = oar.__calc_zero_aoa__() / oar.blade_arm
        self.blade_applied_force = self.pull_force * oar.ratio * self.oar.count
        termination = 'count'
        for i in range(2000):
            oar.calc_blade_fluid_forces()
            oar.ang_acc = ((self.blade_applied_force - oar.blade_fluid_normal_force) /
                           (oar.inertia_total/oar.blade_arm + self.mass_rowers * self.oar.ratio *
                            self.rower_movement()))
            oar_ang_step = self.calc_angular_step()
            oar.ang = r_semi(oar.ang + oar_ang_step)
            oar.ang_speed = ((oar.ang_speed**2 + 2 * oar.ang_acc * oar_ang_step) ** 0.5)
            if abs(oar.ang_acc) > .00001:
                time_step = (-oar.ang_speed + (oar.ang_speed**2 + 2 * oar.ang_acc * oar_ang_step)**.5) / (oar.ang_acc)
            else:
                time_step = oar_ang_step / oar.ang_speed
            oar.calc_blade_prop_forces()
            resistance_force = -self.res_alpha * self.speed**2
            self.acc = (oar.blade_prop_force - resistance_force) / self.mass
            self.pos += self.speed * time_step + .5 * self.acc * (time_step ** 2)
            self.speed += self.acc * time_step
            self.time += time_step
            self.oar.params_2_deg()
            self.__record_list__()
            if oar.ang > self.end_angle:
                termination = 'angle'
                break
        print("Termination from " + termination)
        self.compile_record()
        print(self.time)
        print(self.pos)
        print(self.speed)

    def calc_angular_step(self):
        oar_ang_step = self.max_vel_diff / (2 * abs(self.oar.ang_acc))
        if oar_ang_step < self.min_ang_step:
            oar_ang_step = self.min_ang_step
        elif oar_ang_step > self.max_ang_step:
            oar_ang_step = self.max_ang_step
        self.oar.ang_step = oar_ang_step
        return oar_ang_step

    def rower_movement(self):
        return .5


class rower(object):
    def __init__(self, mass):
        self.mass = mass
        self.slide_distance = 0.65

    def __init_pos_profile__(self):
        pass


class oar(object):
    def __init__(self, boat, oar_count, oar_coeffs):
        self.boat = boat
        self.count = oar_count
        self.dims()
        self.__init_params__()
        self.__init_coeff__(oar_coeffs)
        self.calc_alpha()
        # self.oar_cn = 20
        # self.calc_alpha()

    def __init_params__(self):
        self.ang = None
        self.pos = None  # should be removed at some point
        self.ang_speed = None
        self.ang_acc = None
        self.tang_speed = None
        self.blade_vel_rel_x = None
        self.blade_vel_y = None
        self.blade_vel_x = None
        self.ang_blade_vel_ref = None
        self.ang_oa = None
        self.fluid_speed = None
        self.f_cn = None
        self.f_ca = None
        self.pos_x = None
        self.pos_y = None
        self.blade_fluid_normal_force = None
        self.blade_fluid_axial_force = None
        self.blade_prop_force = None
        self.blade_side_force = None

    def params_2_deg(self):
        attr = copy.copy(vars(self))
        for a in attr:
            if a[:3] == 'ang':
                new_attr = 'deg' + a[3:]
                setattr(self, new_attr, r2d(getattr(self, a)))

    def get_state_params(self):
        self.params_2_deg()
        self.state_params = (self.deg, self.ang_speed, self.ang_acc, self.tang_speed, self.fluid_speed, 1,
                             self.blade_vel_rel_x, self.blade_vel_y, self.blade_vel_x, self.deg_blade_vel_ref_angle,
                             self.deg_oa, self.blade_prop_force)
        print_params = ["{:.3f}".format(p) for p in self.state_params]
        return print_params

    def dims(self):
        self.mass = 2.5 * self.count
        self.blade_area = .124 * self.count
        self.length = 3.81
        self.handle = 0.1
        self.ratio = .5
        self.blade_length = .5
        self.blade_mass = .5
        self.calc_shaft_properties()

    def calc_shaft_properties(self):
        self.effec_length = (self.length - (self.handle + self.blade_length)/2)
        self.handle_arm = self.ratio * self.effec_length / (1 + self.ratio)
        self.blade_arm = self.effec_length - self.handle_arm
        shaft_mass = self.mass - self.blade_mass
        handle_arm_mass = shaft_mass/(1 + self.ratio)
        blade_arm_mass = shaft_mass/(1 - self.ratio)
        self.inertia_total = (handle_arm_mass * (self.handle_arm**2) / 3 + blade_arm_mass * (self.blade_arm**2) / 3 +
                              self.blade_mass * (((self.blade_length**2) / 12) + self.blade_arm**2))
        self.inertia_diff = (-handle_arm_mass * (self.handle_arm**2) / 3 + blade_arm_mass * (self.blade_arm**2) / 3 +
                             self.blade_mass * (((self.blade_length**2) / 12) + self.blade_arm**2))

    def calc_aoa(self, angle, oar_speed):
        self.ang = d2r(angle, True)
        self.speed = oar_speed
        self.__calc_aoa__()
        # print(self.current_state())

    def __calc_aoa__(self):
        self.tang_speed = self.ang_speed * self.blade_arm
        self.blade_vel_rel_x = - self.tang_speed * math.sin(self.ang)
        self.blade_vel_y = self.tang_speed * math.cos(self.ang)
        self.blade_vel_x = self.boat.speed + self.blade_vel_rel_x
        self.ang_blade_vel_ref = math.atan2(self.blade_vel_y, self.blade_vel_x)
        self.ang_oa = r_semi(self.ang_blade_vel_ref - self.ang)
        self.fluid_speed = kw.pythag(self.blade_vel_y, self.blade_vel_x)
        self.pos_x = self.boat.pos + self.blade_arm * math.cos(self.ang)
        self.pos_y = self.blade_arm * math.sin(self.ang)

    def __calc_zero_aoa__(self):
        ang = r_semi(self.ang)
        zero_aoa_speed = self.boat.speed * math.tan(ang) / (math.sin(ang) * math.tan(ang) + math.cos(ang))
        return zero_aoa_speed

    def __init_coeff__(self, filename):
        if filename[-4:-3] is not '.':
            filename += '.csv'
        self.f_cn = kw.function_from_csv(filename, 'deg', 'Cn')
        self.f_ca = kw.function_from_csv(filename, 'deg', 'Ca')

    def calc_alpha(self):
        self.alpha = .5 * 997 * self.blade_area

    def calc_blade_fluid_forces(self):
        self.__calc_aoa__()
        self.cn = self.f_cn(r2d(self.ang_oa))
        self.ca = self.f_ca(r2d(self.ang_oa))
        self.blade_fluid_normal_force = self.alpha * self.f_cn(r2d(self.ang_oa)) * self.fluid_speed ** 2
        self.blade_fluid_axial_force = self.alpha * self.f_ca(r2d(self.ang_oa)) * self.fluid_speed ** 2

    def calc_blade_prop_forces(self):
        sin_a, cos_a = math.sin(self.ang), math.cos(self.ang)
        self.inertia_reaction_at_blade = self.inertia_total * self.ang_acc / self.blade_arm
        self.blade_prop_force = (self.blade_fluid_normal_force * sin_a + self.blade_fluid_axial_force * cos_a +
                                 self.inertia_diff * self.ang_acc * sin_a / self.blade_arm)
        self.blade_side_force = (self.blade_fluid_normal_force * cos_a + self.blade_fluid_axial_force * sin_a +
                                 self.inertia_diff * self.ang_acc * cos_a / self.blade_arm)

    # def current_state(self):
    #     return (self.boat.speed, self.speed, self.ang_d(), self.oar_rel_x, self.oar_y, self.oar_x, self.ang_blade_vel_ref,
    #             self.ang_oa, self.fluid_speed)


def r2d(radians):
    if radians is not None:
        return radians * 180 / math.pi


def d2r(degrees, semi=False):
    if degrees is not None:
        if semi:
            degrees = d180(degrees)
        return degrees * math.pi / 180


def d180(degrees):
    if abs(degrees) > 180:
        return degrees - (360) * degrees / abs(degrees)
    return degrees


def r_semi(radians):
    if radians is not None:
        return d2r(r2d(radians), True)
