# Copyright 2013-2015 Pervasive Displays, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#   http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied.  See the License for the specific language
# governing permissions and limitations under the License.


import sys
import os
import time
from PIL import Image
from PIL import ImageOps
from EPD import EPD


def main(argv):
    epd = EPD()

    for file_name in argv:
        if not os.path.exists(file_name):
            sys.exit('error: image file{f:s} does not exist'.format(f=file_name))
        print('display: {f:s}'.format(f=file_name))
        display_file(epd, file_name)


def display_file(epd, file_name):
    """display centre of image then resized image"""

    image = Image.open(file_name)
    image = ImageOps.grayscale(image)

    rs = image.resize((epd.width, epd.height))
    bw = rs.convert("1", dither=Image.FLOYDSTEINBERG)

    epd.display(bw.rotate(180))
    epd.update()

# main
if "__main__" == __name__:
    if len(sys.argv) < 2:
        sys.exit('usage: {p:s} image-file'.format(p=sys.argv[0]))
    main(sys.argv[1:])
