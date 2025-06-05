# Cerberus

to work with open cv with gstreamer on

conda activate cerberus

# Install Python headers
conda install cmake numpy

# Clone OpenCV
git clone https://github.com/opencv/opencv.git
cd opencv
mkdir build && cd build

# Configure with GStreamer
cmake -D CMAKE_BUILD_TYPE=Release \
      -D CMAKE_INSTALL_PREFIX=$CONDA_PREFIX \
      -D PYTHON_EXECUTABLE=$(which python) \
      -D WITH_GSTREAMER=ON \
      -D BUILD_opencv_python3=ON \
      -D OPENCV_GENERATE_PKGCONFIG=ON \
      ..

make -j$(nproc)
make install
