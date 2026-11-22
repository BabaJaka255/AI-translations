import sys, numpy as np, stable_retro as retro
from PIL import Image
em=retro.RetroEmulator(sys.argv[1])
em.add_cheat('7E0AAC01')
for i in range(int(sys.argv[3])):
    em.set_button_mask(np.zeros(12,np.uint8),0); em.step()
Image.fromarray(em.get_screen()).resize((512,448),Image.NEAREST).save(sys.argv[2])
