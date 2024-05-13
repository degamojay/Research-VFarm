import matplotlib.pyplot as plt
from PIL import Image, ImageFilter
import numpy as np

class VolumetricRepresentation:
    def __init__(self, image_path):
        self.fig = self.create_volumetric_visualization(image_path)

    def create_volumetric_visualization(self, image_path):
        original_image = Image.open(image_path).convert('L')
        processed_image = original_image.filter(ImageFilter.FIND_EDGES)
        image_array = 255 - np.array(processed_image)

        # Generate X, Y coordinates for the grid
        x, y = np.meshgrid(np.arange(image_array.shape[1]), np.arange(image_array.shape[0]))

        # Plot the surface
        fig = plt.figure(figsize=(6, 6))
        ax = fig.add_subplot(111, projection='3d')
        ax.plot_surface(x, y, image_array, cmap='viridis')

        return fig
