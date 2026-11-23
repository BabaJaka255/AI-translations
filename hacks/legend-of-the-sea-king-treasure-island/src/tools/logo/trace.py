"""Lettering traced from the localized logos: silhouettes of 'The Sea King' (unreleased Sea King GB title screen)
and of 'The' / 'King' (Legend of the River King GB box logo), as float masks at reference resolution."""
import numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi

def gb_mask():
    a = np.array(Image.open('ref_sea.png').convert('RGB')).astype(int)[85:290, 50:710]
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    tan = (R > 165) & (G > 95) & (G < 175) & (B < 110) & (R - B > 90)
    red = (R > 165) & (G < 95) & (B < 90)
    m = tan | red
    m = ndi.binary_closing(m, np.ones((3, 3), bool))
    # the thin tan contour line round the logo: anything thinner than about one GB pixel goes
    core = ndi.binary_erosion(m, iterations=4)
    lab, n = ndi.label(m)
    keep = np.unique(lab[core]); keep = keep[keep > 0]
    m = np.isin(lab, keep)
    m = ndi.binary_opening(m, iterations=3) | (m & ndi.binary_dilation(ndi.binary_opening(m, iterations=3), iterations=4))
    return m

if __name__ == '__main__':
    m = gb_mask()
    Image.fromarray((m * 255).astype(np.uint8)).resize((1320, 410), Image.NEAREST).save('v_gbmask.png')
