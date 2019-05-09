#!/usr/bin/env python
"""
Builds all flags into a single sprite image (along with some css).
"""
import os
import re

from PIL import Image

re_flag_file = re.compile(r"[a-z]{2}.gif$")
FLAG_X, FLAG_Y = 16, 11


def main():
    flag_path = os.path.join(os.path.dirname(__file__), "static", "flags")
    files = os.listdir(flag_path)
    img = Image.new("RGBA", (26 * FLAG_X, 26 * FLAG_Y))
    for name in files:
        if not re_flag_file.match(name):
            continue
        x = (ord(name[0]) - 97) * FLAG_X
        y = (ord(name[1]) - 97) * FLAG_Y
        flag_img = Image.open(os.path.join(flag_path, name))
        img.paste(flag_img, (x, y))
    img.save(os.path.join(flag_path, "sprite-hq.png"))
    img = img.quantize(method=2, kmeans=1)
    img.save(os.path.join(flag_path, "sprite.png"))
    css_file = open(os.path.join(flag_path, "sprite.css"), "w")
    css_hq_file = open(os.path.join(flag_path, "sprite-hq.css"), "w")
    initial_css = (
        ".flag-sprite {display: inline-block;width:%(x)spx;height:%(y)spx;"
        "image-rendering:-moz-crisp-edges;image-rendering:pixelated;"
        "image-rendering:-o-crisp-edges;"
        "-ms-interpolation-mode:nearest-neighbor;"
        "background-image:url('%%s')}" % {"x": FLAG_X, "y": FLAG_Y}
    )
    css_file.write(initial_css % "sprite.png")
    write_coords(css_file, FLAG_X, FLAG_Y)
    css_hq_file.write(initial_css % "sprite-hq.png")
    write_coords(css_hq_file, FLAG_X, FLAG_Y)
    for mult in range(2, 5):
        css_hq_file.write(
            "\n.flag%sx {background-size:%spx %spx}"
            "\n.flag%sx.flag-sprite {width:%spx;height:%spx;}"
            % (
                mult,
                26 * FLAG_X * mult,
                26 * FLAG_Y * mult,
                mult,
                FLAG_X * mult,
                FLAG_Y * mult,
            )
        )
        write_coords(
            css_hq_file, FLAG_X * mult, FLAG_Y * mult, prefix=".flag%sx" % mult
        )


def write_coords(css_file, width, height, prefix=""):
    for i in range(26):
        x, y = i * width, i * height
        if x:
            x = "-{}px".format(x)
        if y:
            y = "-{}px".format(y)
        code = chr(i + 97)
        css_file.write("\n%s.flag-%s {background-position-x:%s}" % (prefix, code, x))
        css_file.write("\n%s.flag-_%s {background-position-y:%s}" % (prefix, code, y))


if __name__ == "__main__":
    main()
