#!/usr/bin/env python3
import tkinter as tk
import colour
from colour.appearance import InductionFactors_CIECAM16, XYZ_to_CIECAM16, CIECAM16_to_XYZ, CAM_Specification_CIECAM16
import numpy as np

PHI = 1.61803398874989484820458683436563811772030917980576286213544862270526046281890244970720720418939113748475

# Define the viewing conditions
# https://en.wikipedia.org/wiki/CIECAM02#Parameter_decision_table
# We use dim surrounding conditions, for usage "while viewing a television."
viewing_conditions = InductionFactors_CIECAM16(
    F=0.9,  # factor determining degree of adaptation
    c=0.59,  # Impact of surrounding
    N_c=0.9  # Chromatic induction factor
)

# The surround ratio for a dim setting should be between 0 and 0.15. We will
# use 0.075 Average consumer displays have a brightness of around 150 cd/m2.
# https://en.wikipedia.org/wiki/Candela_per_square_metre

# We use D65, the standard daylight illuminant, as it represents light from the
# sun at noon. This is 6503.51K. This is also the standard for sRGB and
# televisions. In candela/m^2 this is ~100.
# https://en.wikipedia.org/wiki/Standard_illuminant#White_points_of_standard_illuminants

# "If unknown, the adapting field can be assumed to have average reflectance
# ("gray world" assumption): LA = LW / 5."
# So L_A = (LW / 5) where LW is the average luminance of the scene.

# Adapting luminance and background luminance
L_A = 200 / 5 # Luminance of our target
Y_b = 150 / 5  # Background luminance in cd/m2, example value
# L_A = 65 # Luminance of our target
# Y_b = 24  # Background luminance in cd/m2, example value

# This is the D65 white point for the 10 degree observer.
# https://en.wikipedia.org/wiki/Standard_illuminant#D65_values
XYZ_w = np.array([94.811, 100.00, 107.304])

def hex_to_rgb(hx):
    return (int(hx[0:2],16)/255,int(hx[2:4],16)/255,int(hx[4:6],16)/255)

def rgb_to_xyz(rgb):
    return colour.sRGB_to_XYZ(rgb)

def xyz_to_ciecam16(xyz):
    return XYZ_to_CIECAM16(xyz, colour.TVS_ILLUMINANTS['CIE 1964 10 Degree Standard Observer']['D65'], L_A, Y_b, viewing_conditions)

def ciecam16_to_xyz(ciecam16):
    return CIECAM16_to_XYZ(ciecam16, colour.TVS_ILLUMINANTS['CIE 1964 10 Degree Standard Observer']['D65'], L_A, Y_b, viewing_conditions)

def xyz_to_rgb(xyz):
    return colour.XYZ_to_sRGB(xyz / 100, colour.CCS_ILLUMINANTS['CIE 1964 10 Degree Standard Observer']['D65'])

def rgb_to_hex(rgb):
    clamped = []
    for val in rgb:
        if val <= 0:
            clamped.append(0)
        elif val >= 1:
            clamped.append(255)
        else:
            clamped.append(int(round(val * 255)))

    return ''.join(f'{val:02x}' for val in clamped)

def wavelength_to_ciecam16(wavelength):
    return xyz_to_ciecam16(colour.wavelength_to_XYZ(wavelength))

def hex_to_ciecam16(hex_color):
    rgb_color = hex_to_rgb(hex_color)
    xyz_color = rgb_to_xyz(rgb_color)
    return xyz_to_ciecam16(xyz_color)

def ciecam16_to_hex(ciecam16_color):
    xyz_color = ciecam16_to_xyz(ciecam16_color)
    rgb_color = xyz_to_rgb(xyz_color)
    return rgb_to_hex(rgb_color)

def ciecam16_is_within_srgb(ciecam16_color):
    xyz_color = ciecam16_to_xyz(ciecam16_color)
    rgb_color = xyz_to_rgb(xyz_color)
    return all(0 <= val <= 1 for val in rgb_color)

def display_colors(color_matrix):
    print(color_matrix)
    root = tk.Tk()
    root.title("Color Swatch Grid")

    for row_index, row in enumerate(color_matrix):
        for col_index, color in enumerate(row):
            try:
                frame = tk.Frame(root, bg="#"+color, width=100, height=100)
                frame.grid(row=row_index, column=col_index)  # Position the frame in the grid
            except tk.TclError:
                print(f"Invalid color: {color}")

    root.mainloop()

def test():
    step = hex_to_rgb("4488ff")
    print(step)
    step = rgb_to_xyz(step)
    print(step)
    step = xyz_to_ciecam16(step)
    print(step)

    step = ciecam16_to_xyz(CAM_Specification_CIECAM16(
        J=50,
        C=50,
        h=180
    ))
    print(step)
    step = xyz_to_rgb(step)
    print(step)
    step = rgb_to_hex(step)
    print(step)

# Level 0 is the most yin (dark). To get yang (light), do 1 - yin.
def yin_level(level):
    return (1 / pow(PHI, level + 1)) / 2

def interesting_wavelengths():
    hues = []
    wavelengths = [417, 448, 450, 483, 514, 545, 568, 599, 630]

    for wavelength in wavelengths:
        hues.append("#" + ciecam16_to_hex(wavelength_to_ciecam16(wavelength)))

    display_colors(hues)

def wheel():
    slices = 6
    hues = []
    out_of_gamut = False

    for c in range(100, 0, -1):
        hues = []
        out_of_gamut = False
        for i in range(0, slices):
            selected = CAM_Specification_CIECAM16(
                J=50,
                C=c,
                h=(360 / slices) * i
            )

            if ciecam16_is_within_srgb(selected):
                hues.append(ciecam16_to_hex(selected))
            else:
                out_of_gamut = True
                break
        if not out_of_gamut:
            print("Solution found for C =", c)
            break

    # black 
    yin = (1 / PHI / PHI) / 2

    # white 
    yang = 1 - yin

    neutrals = [ciecam16_to_hex(CAM_Specification_CIECAM16(
        J=yin_level(2) * 100,
        C=0,
        h=0
    )),
    ciecam16_to_hex(CAM_Specification_CIECAM16(
        J=yin_level(1) * 100,
        C=0,
        h=0
    )),
    ciecam16_to_hex(CAM_Specification_CIECAM16(
        J=yin_level(0) * 100,
        C=0,
        h=0
    )),
    ciecam16_to_hex(CAM_Specification_CIECAM16(
        J=(1 - yin_level(0)) * 100,
        C=0,
        h=0
    )),
    ciecam16_to_hex(CAM_Specification_CIECAM16(
        J=(1 - yin_level(1)) * 100,
        C=0,
        h=0
    )),
    ciecam16_to_hex(CAM_Specification_CIECAM16(
        J=(1 - yin_level(2)) * 100,
        C=0,
        h=0
    ))]

    yinnest = yin_level(2)
    yangest = 1 - yinnest
    print(yangest, yinnest, (yangest + 0.05) / (yinnest + 0.05))

    display_colors([hues, neutrals])

def main():
    wheel()

main()
