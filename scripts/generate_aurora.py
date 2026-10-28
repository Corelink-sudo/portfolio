"""Pre-render the hero's original green ribbons; Pillow is a build-only tool.

Run: python -m pip install Pillow && python scripts/generate_aurora.py
The browser animates this small texture, not a viewport-sized SVG blur filter.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

WIDTH, HEIGHT = 1440, 900
RIBBONS = [
    ([(-180, 480), (180, 80), (420, 790), (820, 360),
      (1220, -70), (1210, 20), (1630, 250)], 65, .55),
    ([(-180, 620), (200, 280), (520, 850), (900, 470),
      (1280, 90), (1260, 140), (1630, 400)], 32, .65),
    ([(-100, 430), (200, 130), (550, 650), (900, 300),
      (1250, -50), (1320, 100), (1620, 200)], 8, .8),
]
STOPS = [(0, (59, 165, 67), 0), (.3, (59, 165, 67), .65),
         (.65, (139, 187, 51), .85), (1, (59, 165, 67), 0)]


def bezier(points):
    result = []
    for start in (0, 3):
        p = points[start:start + 4]
        for i in range(301):
            t = i / 300
            result.append(tuple(sum(weight * point[axis] for weight, point in zip(
                ((1-t)**3, 3*(1-t)**2*t, 3*(1-t)*t*t, t**3), p
            )) for axis in (0, 1)))
    return result


def main():
    glow = Image.new("L", (WIDTH, HEIGHT))
    for points, width, opacity in RIBBONS:
        layer = Image.new("L", glow.size)
        ImageDraw.Draw(layer).line(bezier(points), fill=round(255 * opacity),
                                   width=width, joint="curve")
        layer = layer.filter(ImageFilter.GaussianBlur(18))
        from PIL import ImageChops
        glow = ImageChops.screen(glow, layer)
    strip = Image.new("RGBA", (WIDTH, 1))
    for x in range(WIDTH):
        t = x / (WIDTH - 1)
        for (a, c1, o1), (b, c2, o2) in zip(STOPS, STOPS[1:]):
            if a <= t <= b:
                f = (t - a) / (b - a)
                strip.putpixel((x, 0), (*[round(c1[k] + (c2[k]-c1[k])*f)
                                          for k in range(3)], round(255*(o1+(o2-o1)*f))))
                break
    result = strip.resize((WIDTH, HEIGHT))
    from PIL import ImageChops
    result.putalpha(ImageChops.multiply(result.getchannel("A"), glow))
    result = result.resize((960, 600), Image.Resampling.LANCZOS)
    destination = Path(__file__).resolve().parents[1] / "assets" / "aurora.webp"
    result.save(destination, "WEBP", quality=90, method=6)
    print(f"Saved {destination.name}: {destination.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
