r'''
===============
Hough transform
===============

The Hough transform in its simplest form is a `method to detect
straight lines <http://en.wikipedia.org/wiki/Hough_transform>`__.

In the following example, we construct an image with a line
intersection.  We then use the Hough transform to explore a parameter
space for straight lines that may run through the image.

Algorithm overview
------------------

Usually, lines are parameterised as :math:`y = mx + c`, with a
gradient :math:`m` and y-intercept `c`.  However, this would mean that
:math:`m` goes to infinity for vertical lines.  Instead, we therefore
construct a segment perpendicular to the line, leading to the origin.
The line is represented by the length of that segment, :math:`r`, and
the angle it makes with the x-axis, :math:`\theta`.

The Hough transform constructs a histogram array representing the
parameter space (i.e., an :math:`M \times N` matrix, for :math:`M`
different values of the radius and :math:`N` different values of
:math:`\theta`).  For each parameter combination, :math:`r` and
:math:`\theta`, we then find the number of non-zero pixels in the
input image that would fall close to the corresponding line, and
increment the array at position :math:`(r, \theta)` appropriately.

We can think of each non-zero pixel "voting" for potential line
candidates.  The local maxima in the resulting histogram indicates the
parameters of the most probably lines.  In our example, the maxima
occur at 45 and 135 degrees, corresponding to the normal vector
angles of each line.

Another approach is the Progressive Probabilistic Hough Transform
[1]_.  It is based on the assumption that using a random subset of
voting points give a good approximation to the actual result, and that
lines can be extracted during the voting process by walking along
connected components.  This returns the beginning and end of each
line segment, which is useful.

The function `probabilistic_hough` has three parameters: a general
threshold that is applied to the Hough accumulator, a minimum line
length and the line gap that influences line merging.  In the example
below, we find lines longer than 10 with a gap less than 3 pixels.

References
----------

.. [1] C. Galamhos, J. Matas and J. Kittler,"Progressive probabilistic
       Hough transform for line detection", in IEEE Computer Society
       Conference on Computer Vision and Pattern Recognition, 1999.

.. [2] Duda, R. O. and P. E. Hart, "Use of the Hough Transformation to
       Detect Lines and Curves in Pictures," Comm. ACM, Vol. 15,
       pp. 11-15 (January, 1972)

'''
import numpy as np

from skimage.transform import hough_line, hough_line_peaks
from skimage.feature import canny
from skimage.draw import line
from skimage import data

import matplotlib.pyplot as plt
from matplotlib import cm


# Constructing test image
image = np.zeros((200, 200))
idx = np.arange(25, 175)
image[idx, idx] = 255
image[line(175, 25, 25, 175)] = 255

# image[line(50, 60, 50, 140)] = 255
# image[line(50, 100, 150, 100)] = 255


# Classic straight-line Hough transform
# Set a precision of 0.5 degree.
tested_angles = np.linspace(-np.pi / 2, np.pi / 2, 360, endpoint=False)
h, theta, d = hough_line(image, theta=tested_angles)

# Generating figure 1
fig, axes = plt.subplots(1, 3, figsize=(20, 10))
ax = axes.ravel()

ax[0].imshow(image, cmap=cm.gray)
ax[0].set_title('Input image')
ax[0].set_axis_off()

angle_step = 0.5 * np.diff(theta).mean()
d_step = 0.5 * np.diff(d).mean()
bounds = [np.rad2deg(theta[0] - angle_step),
          np.rad2deg(theta[-1] + angle_step),
          d[-1] + d_step, d[0] - d_step]
ax[1].imshow(np.log(1 + h), extent=bounds, cmap=cm.gray)
ax[1].grid(True)
ax[1].set_title('Hough transform')
ax[1].set_xlabel('Angles (degrees)')
ax[1].set_ylabel('Distance (pixels)')
ax[1].axis('image')

ax[2].imshow(image, cmap=cm.gray)
ax[2].set_ylim((image.shape[0], 0))
ax[2].set_axis_off()
ax[2].set_title('Detected lines')

c = 0

for _, angle, dist in zip(*hough_line_peaks(h, theta, d)):
    if c == 0:
        (x0, y0) = dist * np.array([np.cos(angle), np.sin(angle)])
        ax[2].axline((x0, y0), slope=np.tan(angle + np.pi / 2), color='r',  linewidth=2)
        c = 1
    else:
        (x0, y0) = dist * np.array([np.cos(angle), np.sin(angle)])
        ax[2].axline((x0, y0), slope=np.tan(angle + np.pi / 2), color='b',  linewidth=2)
    print("Angle: ", angle)
    print("Cosinus: ", np.cos(angle))
    print("Sinus: ", np.sin(angle))
    print("Sistance: ", dist)
    print("X0: ", x0)
    print("Y0: ", y0)
    print("Slope:", np.tan(angle + np.pi/2))
    print("______")

plt.savefig("Hough")
plt.show()
