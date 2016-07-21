

class boat(object):
    def __init__(self):
        self.mass = 84
        self.res_alpha = 3.5  # N s²/m²
        self.pos = 0
        self.vel = 0
        self.acc = 0
        self.time = 0
        self.oar = oar()

    def stroke(self, prop_force, distance, fractions):
        d_step_dist = distance / fractions
        for i in range(fractions):
            boat_dist = d_step_dist / self.oar.ratio
            resistance_force = self.res_alpha * self.vel**2
            self.acc = ((prop_force * self.oar.ratio) - resistance_force) / self.mass
            self.time += (-self.vel + (self.vel**2 + 2 * self.acc * boat_dist)**.5) / (2 * boat_dist)
            self.vel = (self.vel**2 + 2 * self.acc * boat_dist) ** 0.5
            self.pos += boat_dist
            print("Stroke:", "{:10.2f}".format(self.time), "{:10.2f}".format(self.pos),
                  "{:10.2f}".format(self.vel), "{:10.2f}".format(self.acc))

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

    def row(self, count):
        for i in range(count):
            self.stroke(200, 1, 10)
            self.recover(1, 10)








class oar(object):
    def __init__(self):
        self.mass = 2
        self.ratio = 1
