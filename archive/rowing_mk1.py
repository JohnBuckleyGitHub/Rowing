

class boat(object):
    def __init__(self, count):
        self.mass = 92.5 * count + 146
        self.res_alpha = 4 + .75 * count  # N s²/m²
        self.pos = 0
        self.vel = 0
        self.acc = 0
        self.time = 0
        self.oar = oar(self, 8)
        self.stroke_rate = 30
        self.dist_last = 0
        self.pull_time = 0

    def stroke(self, prop_force, distance, fractions):
        d_step_dist = distance / fractions
        oar_dist_step = d_step_dist / self.oar.ratio
        oar = self.oar
        # max_oar_speed = oar.max_oar_speed(prop_force)
        # print(max_oar_speed)
        oar.speed = self.vel
        oar.dist = 0
        begin_time = self.time
        self.dist_last = self.pos
        for i in range(fractions):
            self.drive_force = oar.drag_force()
            oar.acc = (prop_force * oar.ratio - self.drive_force) / (oar.mass * oar.count)
            oar.speed = ((oar.speed**2 + 2 * oar.acc * oar_dist_step) ** 0.5)
            oar.dist += oar_dist_step
            if abs(oar.acc) > .00001:
                time_step = (-oar.speed + (oar.speed**2 + 2 * oar.acc * oar_dist_step)**.5) / (oar.acc)
            else:
                time_step = oar_dist_step / oar.speed
            resistance_force = self.res_alpha * self.vel**2
            # print('s ', oar.speed, oar.acc, time_step, resistance_force)
            self.acc = (self.drive_force - resistance_force) / self.mass
            self.pos += self.vel * time_step + .5 * self.acc * (time_step ** 2)
            self.vel += self.acc * time_step
            self.time += time_step
            # if (i % 50000) == 0:
            #     self.print_status('Stroke')
        self.print_status('FStroke')
        self.pull_time = self.time - begin_time

    def recover(self, duration, fractions):
        t_step = duration / fractions
        for i in range(fractions):
            resistance_force = -self.res_alpha * self.vel**2
            self.acc = resistance_force / self.mass
            self.time += t_step
            self.pos += self.vel * t_step + .5 * self.acc * t_step**2
            self.vel += self.acc * t_step
        print("Recover:", "{:10.2f}".format(self.time), "{:10.2f}".format(self.pos),
              "{:10.2f}".format(self.vel), "{:10.2f}".format(self.acc))

    def row(self, stroke_count):
        stroke_duration = 60 / self.stroke_rate
        for i in range(stroke_count):
            self.stroke(1000, 1.6, 100000)
            self.recover(stroke_duration - self.pull_time, 10)

    def print_status(self, label):
        print(label + ": ", "{:10.2f}".format(self.time), "{:10.2f}".format(self.pos-self.dist_last),
              "{:10.2f}".format(self.vel), "{:10.2f}".format(self.acc))
        print('o:', "{:10.2f}".format(self.oar.dist), "{:10.2f}".format(self.oar.speed-self.vel),
              "{:10.0f}".format(self.drive_force), "{:10.4f}".format(self.pull_time))


class oar(object):
    def __init__(self, boat, oar_count):
        self.boat = boat
        self.dims()
        self.count = oar_count
        self.oar_cd = 20
        self.calc_alpha()
        self.speed = 0
        self.dist = 0

    def dims(self):
        self.mass = 2.5
        self.oar_area = .124
        self.length = 3.76
        self.handle = 0.1
        self.ratio = .5 
        self.blade_length = .5
        eff_length = (self.length - (self.handle + self.blade_length)/2)
        self.handle_arm = eff_length / (1 + self.ratio)
        self.blade_arm = eff_length - self.handle_arm

    def calc_alpha(self):
        self.alpha = .5 * 997 * self.oar_cd * self.oar_area

    def drag_force(self):
        rel_vel = self.speed - self.boat.vel
        if rel_vel != 0:
            force = (self.count * self.alpha * (rel_vel ** 2) * (rel_vel) / abs(rel_vel))
        else:
            force = 0
        return force

    def max_oar_speed(self, force):
        return (force / self.alpha) ** .5
