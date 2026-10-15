# Thumbnail size rounds up by default

**Tags:** thumbnail, graphql, breaking change

Thumbnails exist only in a fixed set of sizes (32 to 4096, doubling). A requested `size` that is
not one of them has to be matched to one, and the `sizeRounding` argument on thumbnail fields
chooses how: `NEAREST` picks the closest size, `UP` the smallest size not smaller than requested.

From Saleor 3.24 the default is `UP`; `NEAREST` is opt-in. We trade image quality for client
performance: `NEAREST` can return fewer pixels than requested (`1500` gives `1024`), and the
browser stretches the image to fill its slot, which looks blurry. Merchants reported this as a
Saleor bug, not as a mistake in the size they asked for. `UP` never returns fewer pixels than
requested, so a client asking for the size it displays gets a sharp image. The cost is bandwidth:
in the worst case (`1025` gives `2048`) the image has four times the pixels. Clients that care
more about bytes than sharpness can pass `NEAREST`.

`sizeRounding` was introduced in 3.23 with `NEAREST` as the default, because changing what an
existing query returns in a patch release is a breaking change. 3.23 lets clients opt in to `UP`;
3.24 flips the default and lets them opt back out.
