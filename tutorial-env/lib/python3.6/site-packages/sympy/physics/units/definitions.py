from sympy import Rational, pi, sqrt, sympify, S
from sympy.physics.units.quantities import Quantity
from sympy.physics.units.dimensions import (
    acceleration, action, amount_of_substance, capacitance, charge,
    conductance, current, energy, force, frequency, information, impedance, inductance,
    length, luminous_intensity, magnetic_density, magnetic_flux, mass, power,
    pressure, temperature, time, velocity, voltage)
from sympy.physics.units.dimensions import dimsys_default, Dimension
from sympy.physics.units.prefixes import (
    centi, deci, kilo, micro, milli, nano, pico,
    kibi, mebi, gibi, tebi, pebi, exbi)

One = S.One

#### UNITS ####

# Dimensionless:

percent = percents = Quantity("percent", latex_repr=r"\%")
percent.set_dimension(One)
percent.set_scale_factor(Rational(1, 100))

permille = Quantity("permille")
permille.set_dimension(One)
permille.set_scale_factor(Rational(1, 1000))


# Angular units (dimensionless)

rad = radian = radians = Quantity("radian", abbrev="rad")
radian.set_dimension(One)
radian.set_scale_factor(One)

deg = degree = degrees = Quantity("degree", abbrev="deg", latex_repr=r"^\circ")
degree.set_dimension(One)
degree.set_scale_factor(pi/180)

sr = steradian = steradians = Quantity("steradian", abbrev="sr")
steradian.set_dimension(One)
steradian.set_scale_factor(One)

mil = angular_mil = angular_mils = Quantity("angular_mil", abbrev="mil")
angular_mil.set_dimension(One)
angular_mil.set_scale_factor(2*pi/6400)


# Base units:

m = meter = meters = Quantity("meter", abbrev="m")
meter.set_dimension(length)
meter.set_scale_factor(One)

# NOTE: the `kilogram` has scale factor of 1 in SI.
# The current state of the code assumes SI unit dimensions, in
# the future this module will be modified in order to be unit system-neutral
# (that is, support all kinds of unit systems).
kg = kilogram = kilograms = Quantity("kilogram", abbrev="kg")
kilogram.set_dimension(mass)
kilogram.set_scale_factor(One)

s = second = seconds = Quantity("second", abbrev="s")
second.set_dimension(time)
second.set_scale_factor(One)

A = ampere = amperes = Quantity("ampere", abbrev='A')
ampere.set_dimension(current)
ampere.set_scale_factor(One)

K = kelvin = kelvins = Quantity("kelvin", abbrev='K')
kelvin.set_dimension(temperature)
kelvin.set_scale_factor(One)

mol = mole = moles = Quantity("mole", abbrev="mol")
mole.set_dimension(amount_of_substance)
mole.set_scale_factor(One)

cd = candela = candelas = Quantity("candela", abbrev="cd")
candela.set_dimension(luminous_intensity)
candela.set_scale_factor(One)

g = gram = grams = Quantity("gram", abbrev="g")
gram.set_dimension(mass)
gram.set_scale_factor(kilogram/kilo)

mg = milligram = milligrams = Quantity("milligram", abbrev="mg")
milligram.set_dimension(mass)
milligram.set_scale_factor(milli*gram)

ug = microgram = micrograms = Quantity("microgram", abbrev="ug", latex_repr=r"\mu\text{g}")
microgram.set_dimension(mass)
microgram.set_scale_factor(micro*gram)


# derived units
newton = newtons = N = Quantity("newton", abbrev="N")
newton.set_dimension(force)
newton.set_scale_factor(kilogram*meter/second**2)

joule = joules = J = Quantity("joule", abbrev="J")
joule.set_dimension(energy)
joule.set_scale_factor(newton*meter)

watt = watts = W = Quantity("watt", abbrev="W")
watt.set_dimension(power)
watt.set_scale_factor(joule/second)

pascal = pascals = Pa = pa = Quantity("pascal", abbrev="Pa")
pascal.set_dimension(pressure)
pascal.set_scale_factor(newton/meter**2)

hertz = hz = Hz = Quantity("hertz", abbrev="Hz")
hertz.set_dimension(frequency)
hertz.set_scale_factor(One)


# MKSA extension to MKS: derived units

coulomb = coulombs = C = Quantity("coulomb", abbrev='C')
coulomb.set_dimension(charge)
coulomb.set_scale_factor(One)

volt = volts = v = V = Quantity("volt", abbrev='V')
volt.set_dimension(voltage)
volt.set_scale_factor(joule/coulomb)

ohm = ohms = Quantity("ohm", abbrev='ohm', latex_repr=r"\Omega")
ohm.set_dimension(impedance)
ohm.set_scale_factor(volt/ampere)

siemens = S = mho = mhos = Quantity("siemens", abbrev='S')
siemens.set_dimension(conductance)
siemens.set_scale_factor(ampere/volt)

farad = farads = F = Quantity("farad", abbrev='F')
farad.set_dimension(capacitance)
farad.set_scale_factor(coulomb/volt)

henry = henrys = H = Quantity("henry", abbrev='H')
henry.set_dimension(inductance)
henry.set_scale_factor(volt*second/ampere)

tesla = teslas = T = Quantity("tesla", abbrev='T')
tesla.set_dimension(magnetic_density)
tesla.set_scale_factor(volt*second/meter**2)

weber = webers = Wb = wb = Quantity("weber", abbrev='Wb')
weber.set_dimension(magnetic_flux)
weber.set_scale_factor(joule/ampere)


# Other derived units:

optical_power = dioptre = diopter = D = Quantity("dioptre")
dioptre.set_dimension(1/length)
dioptre.set_scale_factor(1/meter)

lux = lx = Quantity("lux", abbrev="lx")
lux.set_dimension(luminous_intensity/length**2)
lux.set_scale_factor(steradian*candela/meter**2)

# katal is the SI unit of catalytic activity
katal = kat = Quantity("katal", abbrev="kat")
katal.set_dimension(amount_of_substance/time)
katal.set_scale_factor(mol/second)

# gray is the SI unit of absorbed dose
gray = Gy = Quantity("gray")
gray.set_dimension(energy/mass)
gray.set_scale_factor(meter**2/second**2)

# becquerel is the SI unit of radioactivity
becquerel = Bq = Quantity("becquerel", abbrev="Bq")
becquerel.set_dimension(1/time)
becquerel.set_scale_factor(1/second)


# Common length units

km = kilometer = kilometers = Quantity("kilometer", abbrev="km")
kilometer.set_dimension(length)
kilometer.set_scale_factor(kilo*meter)

dm = decimeter = decimeters = Quantity("decimeter", abbrev="dm")
decimeter.set_dimension(length)
decimeter.set_scale_factor(deci*meter)

cm = centimeter = centimeters = Quantity("centimeter", abbrev="cm")
centimeter.set_dimension(length)
centimeter.set_scale_factor(centi*meter)

mm = millimeter = millimeters = Quantity("millimeter", abbrev="mm")
millimeter.set_dimension(length)
millimeter.set_scale_factor(milli*meter)

um = micrometer = micrometers = micron = microns = \
    Quantity("micrometer", abbrev="um", latex_repr=r'\mu\text{m}')
micrometer.set_dimension(length)
micrometer.set_scale_factor(micro*meter)

nm = nanometer = nanometers = Quantity("nanometer", abbrev="nm")
nanometer.set_dimension(length)
nanometer.set_scale_factor(nano*meter)

pm = picometer = picometers = Quantity("picometer", abbrev="pm")
picometer.set_dimension(length)
picometer.set_scale_factor(pico*meter)


ft = foot = feet = Quantity("foot", abbrev="ft")
foot.set_dimension(length)
foot.set_scale_factor(Rational(3048, 10000)*meter)

inch = inches = Quantity("inch")
inch.set_dimension(length)
inch.set_scale_factor(foot/12)

yd = yard = yards = Quantity("yard", abbrev="yd")
yard.set_dimension(length)
yard.set_scale_factor(3*feet)

mi = mile = miles = Quantity("mile")
mile.set_dimension(length)
mile.set_scale_factor(5280*feet)

nmi = nautical_mile = nautical_miles = Quantity("nautical_mile")
nautical_mile.set_dimension(length)
nautical_mile.set_scale_factor(6076*feet)


# Common volume and area units

l = liter = liters = Quantity("liter")
liter.set_dimension(length**3)
liter.set_scale_factor(meter**3 / 1000)

dl = deciliter = deciliters = Quantity("deciliter")
deciliter.set_dimension(length**3)
deciliter.set_scale_factor(liter / 10)

cl = centiliter = centiliters = Quantity("centiliter")
centiliter.set_dimension(length**3)
centiliter.set_scale_factor(liter / 100)

ml = milliliter = milliliters = Quantity("milliliter")
milliliter.set_dimension(length**3)
milliliter.set_scale_factor(liter / 1000)


# Common time units

ms = millisecond = milliseconds = Quantity("millisecond", abbrev="ms")
millisecond.set_dimension(time)
millisecond.set_scale_factor(milli*second)

us = microsecond = microseconds = Quantity("microsecond", abbrev="us", latex_repr=r'\mu\text{s}')
microsecond.set_dimension(time)
microsecond.set_scale_factor(micro*second)

ns = nanosecond = nanoseconds = Quantity("nanosecond", abbrev="ns")
nanosecond.set_dimension(time)
nanosecond.set_scale_factor(nano*second)

ps = picosecond = picoseconds = Quantity("picosecond", abbrev="ps")
picosecond.set_dimension(time)
picosecond.set_scale_factor(pico*second)


minute = minutes = Quantity("minute")
minute.set_dimension(time)
minute.set_scale_factor(60*second)

h = hour = hours = Quantity("hour")
hour.set_dimension(time)
hour.set_scale_factor(60*minute)

day = days = Quantity("day")
day.set_dimension(time)
day.set_scale_factor(24*hour)


anomalistic_year = anomalistic_years = Quantity("anomalistic_year")
anomalistic_year.set_dimension(time)
anomalistic_year.set_scale_factor(365.259636*day)

sidereal_year = sidereal_years = Quantity("sidereal_year")
sidereal_year.set_dimension(time)
sidereal_year.set_scale_factor(31558149.540)

tropical_year = tropical_years = Quantity("tropical_year")
tropical_year.set_dimension(time)
tropical_year.set_scale_factor(365.24219*day)

common_year = common_years = Quantity("common_year")
common_year.set_dimension(time)
common_year.set_scale_factor(365*day)

julian_year = julian_years = Quantity("julian_year")
julian_year.set_dimension(time)
julian_year.set_scale_factor((365 + One/4)*day)

draconic_year = draconic_years = Quantity("draconic_year")
draconic_year.set_dimension(time)
draconic_year.set_scale_factor(346.62*day)

gaussian_year = gaussian_years = Quantity("gaussian_year")
gaussian_year.set_dimension(time)
gaussian_year.set_scale_factor(365.2568983*day)

full_moon_cycle = full_moon_cycles = Quantity("full_moon_cycle")
full_moon_cycle.set_dimension(time)
full_moon_cycle.set_scale_factor(411.78443029*day)


year = years = tropical_year

#### CONSTANTS ####

# Newton constant
G = gravitational_constant = Quantity("gravitational_constant", abbrev="G")
gravitational_constant.set_dimension(length**3*mass**-1*time**-2)
gravitational_constant.set_scale_factor(6.67408e-11*m**3/(kg*s**2))

# speed of light
c = speed_of_light = Quantity("speed_of_light", abbrev="c")
speed_of_light.set_dimension(velocity)
speed_of_light.set_scale_factor(299792458*meter/second)

# Reduced Planck constant
hbar = Quantity("hbar", abbrev="hbar")
hbar.set_dimension(action)
hbar.set_scale_factor(1.05457266e-34*joule*second)

# Planck constant
planck = Quantity("planck", abbrev="h")
planck.set_dimension(action)
planck.set_scale_factor(2*pi*hbar)

# Electronvolt
eV = electronvolt = electronvolts = Quantity("electronvolt", abbrev="eV")
electronvolt.set_dimension(energy)
electronvolt.set_scale_factor(1.60219e-19*joule)

# Avogadro number
avogadro_number = Quantity("avogadro_number")
avogadro_number.set_dimension(One)
avogadro_number.set_scale_factor(6.022140857e23)

# Avogadro constant
avogadro = avogadro_constant = Quantity("avogadro_constant")
avogadro_constant.set_dimension(amount_of_substance**-1)
avogadro_constant.set_scale_factor(avogadro_number / mol)

# Boltzmann constant
boltzmann = boltzmann_constant = Quantity("boltzmann_constant")
boltzmann_constant.set_dimension(energy/temperature)
boltzmann_constant.set_scale_factor(1.38064852e-23*joule/kelvin)

# Stefan-Boltzmann constant
stefan = stefan_boltzmann_constant = Quantity("stefan_boltzmann_constant")
stefan_boltzmann_constant.set_dimension(energy*time**-1*length**-2*temperature**-4)
stefan_boltzmann_constant.set_scale_factor(5.670367e-8*joule/(s*m**2*kelvin**4))

# Atomic mass
amu = amus = atomic_mass_unit = atomic_mass_constant = Quantity("atomic_mass_constant")
atomic_mass_constant.set_dimension(mass)
atomic_mass_constant.set_scale_factor(1.660539040e-24*gram)

# Molar gas constant
R = molar_gas_constant = Quantity("molar_gas_constant", abbrev="R")
molar_gas_constant.set_dimension(energy/(temperature * amount_of_substance))
molar_gas_constant.set_scale_factor(8.3144598*joule/kelvin/mol)

# Faraday constant
faraday_constant = Quantity("faraday_constant")
faraday_constant.set_dimension(charge/amount_of_substance)
faraday_constant.set_scale_factor(96485.33289*C/mol)

# Josephson constant
josephson_constant = Quantity("josephson_constant", abbrev="K_j")
josephson_constant.set_dimension(frequency/voltage)
josephson_constant.set_scale_factor(483597.8525e9*hertz/V)

# Von Klitzing constant
von_klitzing_constant = Quantity("von_klitzing_constant", abbrev="R_k")
von_klitzing_constant.set_dimension(voltage/current)
von_klitzing_constant.set_scale_factor(25812.8074555*ohm)

# Acceleration due to gravity (on the Earth surface)
gee = gees = acceleration_due_to_gravity = Quantity("acceleration_due_to_gravity", abbrev="g")
acceleration_due_to_gravity.set_dimension(acceleration)
acceleration_due_to_gravity.set_scale_factor(9.80665*meter/second**2)

# magnetic constant:
u0 = magnetic_constant = vacuum_permeability = Quantity("magnetic_constant")
magnetic_constant.set_dimension(force/current**2)
magnetic_constant.set_scale_factor(4*pi/10**7 * newton/ampere**2)

# electric constat:
e0 = electric_constant = vacuum_permittivity = Quantity("vacuum_permittivity")
vacuum_permittivity.set_dimension(capacitance/length)
vacuum_permittivity.set_scale_factor(1/(u0 * c**2))

# vacuum impedance:
Z0 = vacuum_impedance = Quantity("vacuum_impedance", abbrev='Z_0', latex_repr=r'Z_{0}')
vacuum_impedance.set_dimension(impedance)
vacuum_impedance.set_scale_factor(u0 * c)

# Coulomb's constant:
coulomb_constant = coulombs_constant = electric_force_constant = \
    Quantity("coulomb_constant", abbrev="k_e")
coulomb_constant.set_dimension(force*length**2/charge**2)
coulomb_constant.set_scale_factor(1/(4*pi*vacuum_permittivity))


atmosphere = atmospheres = atm = Quantity("atmosphere", abbrev="atm")
atmosphere.set_dimension(pressure)
atmosphere.set_scale_factor(101325 * pascal)


kPa = kilopascal = Quantity("kilopascal", abbrev="kPa")
kilopascal.set_dimension(pressure)
kilopascal.set_scale_factor(kilo*Pa)

bar = bars = Quantity("bar", abbrev="bar")
bar.set_dimension(pressure)
bar.set_scale_factor(100*kPa)

pound = pounds = Quantity("pound")  # exact
pound.set_dimension(mass)
pound.set_scale_factor(Rational(45359237, 100000000) * kg)

psi = Quantity("psi")
psi.set_dimension(pressure)
psi.set_scale_factor(pound * gee / inch ** 2)

dHg0 = 13.5951  # approx value at 0 C
mmHg = torr = Quantity("mmHg")
mmHg.set_dimension(pressure)
mmHg.set_scale_factor(dHg0 * acceleration_due_to_gravity * kilogram / meter**2)

mmu = mmus = milli_mass_unit = Quantity("milli_mass_unit")
milli_mass_unit.set_dimension(mass)
milli_mass_unit.set_scale_factor(atomic_mass_unit/1000)

quart = quarts = Quantity("quart")
quart.set_dimension(length**3)
quart.set_scale_factor(Rational(231, 4) * inch**3)


# Other convenient units and magnitudes

ly = lightyear = lightyears = Quantity("lightyear", abbrev="ly")
lightyear.set_dimension(length)
lightyear.set_scale_factor(speed_of_light*julian_year)

au = astronomical_unit = astronomical_units = Quantity("astronomical_unit", abbrev="AU")
astronomical_unit.set_dimension(length)
astronomical_unit.set_scale_factor(149597870691*meter)


# Fundamental Planck units:
planck_mass = Quantity("planck_mass", abbrev="m_P", latex_repr=r'm_\text{P}')
planck_mass.set_dimension(mass)
planck_mass.set_scale_factor(sqrt(hbar*speed_of_light/G))

planck_time = Quantity("planck_time", abbrev="t_P", latex_repr=r't_\text{P}')
planck_time.set_dimension(time)
planck_time.set_scale_factor(sqrt(hbar*G/speed_of_light**5))

planck_temperature = Quantity("planck_temperature", abbrev="T_P",
                              latex_repr=r'T_\text{P}')
planck_temperature.set_dimension(temperature)
planck_temperature.set_scale_factor(sqrt(hbar*speed_of_light**5/G/boltzmann**2))

planck_length = Quantity("planck_length", abbrev="l_P", latex_repr=r'l_\text{P}')
planck_length.set_dimension(length)
planck_length.set_scale_factor(sqrt(hbar*G/speed_of_light**3))

planck_charge = Quantity("planck_charge", abbrev="q_P", latex_repr=r'q_\text{P}')
planck_charge.set_dimension(charge)
planck_charge.set_scale_factor(sqrt(4*pi*electric_constant*hbar*speed_of_light))


# Derived Planck units:
planck_area = Quantity("planck_area")
planck_area.set_dimension(length**2)
planck_area.set_scale_factor(planck_length**2)

planck_volume = Quantity("planck_volume")
planck_volume.set_dimension(length**3)
planck_volume.set_scale_factor(planck_length**3)

planck_momentum = Quantity("planck_momentum")
planck_momentum.set_dimension(mass*velocity)
planck_momentum.set_scale_factor(planck_mass * speed_of_light)

planck_energy = Quantity("planck_energy", abbrev="E_P", latex_repr=r'E_\text{P}')
planck_energy.set_dimension(energy)
planck_energy.set_scale_factor(planck_mass * speed_of_light**2)

planck_force = Quantity("planck_force", abbrev="F_P", latex_repr=r'F_\text{P}')
planck_force.set_dimension(force)
planck_force.set_scale_factor(planck_energy / planck_length)

planck_power = Quantity("planck_power", abbrev="P_P", latex_repr=r'P_\text{P}')
planck_power.set_dimension(power)
planck_power.set_scale_factor(planck_energy / planck_time)

planck_density = Quantity("planck_density", abbrev="rho_P", latex_repr=r'\rho_\text{P}')
planck_density.set_dimension(mass/length**3)
planck_density.set_scale_factor(planck_mass / planck_length**3)

planck_energy_density = Quantity("planck_energy_density", abbrev="rho^E_P")
planck_energy_density.set_dimension(energy / length**3)
planck_energy_density.set_scale_factor(planck_energy / planck_length**3)

planck_intensity = Quantity("planck_intensity", abbrev="I_P", latex_repr=r'I_\text{P}')
planck_intensity.set_dimension(mass * time**(-3))
planck_intensity.set_scale_factor(planck_energy_density * speed_of_light)

planck_angular_frequency = Quantity("planck_angular_frequency", abbrev="omega_P",
                                    latex_repr=r'\omega_\text{P}')
planck_angular_frequency.set_dimension(1 / time)
planck_angular_frequency.set_scale_factor(1 / planck_time)

planck_pressure = Quantity("planck_pressure", abbrev="p_P", latex_repr=r'p_\text{P}')
planck_pressure.set_dimension(pressure)
planck_pressure.set_scale_factor(planck_force / planck_length**2)

planck_current = Quantity("planck_current", abbrev="I_P", latex_repr=r'I_\text{P}')
planck_current.set_dimension(current)
planck_current.set_scale_factor(planck_charge / planck_time)

planck_voltage = Quantity("planck_voltage", abbrev="V_P", latex_repr=r'V_\text{P}')
planck_voltage.set_dimension(voltage)
planck_voltage.set_scale_factor(planck_energy / planck_charge)

planck_impedance = Quantity("planck_impedance", abbrev="Z_P", latex_repr=r'Z_\text{P}')
planck_impedance.set_dimension(impedance)
planck_impedance.set_scale_factor(planck_voltage / planck_current)

planck_acceleration = Quantity("planck_acceleration", abbrev="a_P",
                               latex_repr=r'a_\text{P}')
planck_acceleration.set_dimension(acceleration)
planck_acceleration.set_scale_factor(speed_of_light / planck_time)


# Information theory units:
bit = bits = Quantity("bit")
bit.set_dimension(information)
bit.set_scale_factor(One)

byte = bytes = Quantity("byte")
byte.set_dimension(information)
byte.set_scale_factor(8*bit)

kibibyte = kibibytes = Quantity("kibibyte")
kibibyte.set_dimension(information)
kibibyte.set_scale_factor(kibi*byte)

mebibyte = mebibytes = Quantity("mebibyte")
mebibyte.set_dimension(information)
mebibyte.set_scale_factor(mebi*byte)

gibibyte = gibibytes = Quantity("gibibyte")
gibibyte.set_dimension(information)
gibibyte.set_scale_factor(gibi*byte)

tebibyte = tebibytes = Quantity("tebibyte")
tebibyte.set_dimension(information)
tebibyte.set_scale_factor(tebi*byte)

pebibyte = pebibytes = Quantity("pebibyte")
pebibyte.set_dimension(information)
pebibyte.set_scale_factor(pebi*byte)

exbibyte = exbibytes = Quantity("exbibyte")
exbibyte.set_dimension(information)
exbibyte.set_scale_factor(exbi*byte)

# Older units for radioactivity
curie = Ci = Quantity("curie", abbrev="Ci")
curie.set_dimension(1/time)
curie.set_scale_factor(37000000000*becquerel)

rutherford = Rd = Quantity("rutherford", abbrev="Rd")
rutherford.set_dimension(1/time)
rutherford.set_scale_factor(1000000*becquerel)

# check that scale factors are the right SI dimensions:
for _scale_factor, _dimension in zip(
        Quantity.SI_quantity_scale_factors.values(),
        Quantity.SI_quantity_dimension_map.values()):
    dimex = Quantity.get_dimensional_expr(_scale_factor)
    if dimex != 1:
        if not dimsys_default.equivalent_dims(_dimension, Dimension(dimex)):
            raise ValueError("quantity value and dimension mismatch")
del _scale_factor, _dimension
