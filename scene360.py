from manimlib.scene.scene_file_writer import SceneFileWriter
from manimlib.scene.scene import Scene
from manimlib.camera.camera import CameraFrame
from manimlib.constants import *
import os
from PIL import Image
import subprocess as sp
import numpy as np


def rotate_by_matrix(self: CameraFrame, matrix):
    curr_rot_T = self.get_inverse_camera_rotation_matrix()
    new_rot_T = np.dot(matrix.T, curr_rot_T)
    self.inverse_camera_rotation_matrix = [list(i) for i in new_rot_T]
    return self


CameraFrame.rotate_by_matrix = rotate_by_matrix


class SceneFileWriter360(SceneFileWriter):
    def print_file_ready_message(self, file_path):
        print(f"\nFile ready at {file_path}\n")
        stem, ext = os.path.splitext(file_path)
        print(f"You can use `ffmpeg -i {file_path} -vf v360=c3x2:e {stem}_360{ext}`\n"
              "to convert it to a 360-degree video")

    def open_movie_pipe(self, file_path):
        # This function is modified from manimlib/scene/scene_file_writer.py
        stem, ext = os.path.splitext(file_path)
        self.final_file_path = file_path
        self.temp_file_path = stem + "_temp" + ext

        fps = self.scene.camera.frame_rate
        width, height = self.scene.camera.get_pixel_shape()
        # The following two lines are added
        width = height*3
        height = height*2

        command = [
            FFMPEG_BIN,
            '-y',  # overwrite output file if it exists
            '-f', 'rawvideo',
            '-s', f'{width}x{height}',  # size of one frame
            '-pix_fmt', 'rgba',
            '-r', str(fps),  # frames per second
            '-i', '-',  # The imput comes from a pipe
            '-vf', 'vflip',
            '-an',  # Tells FFMPEG not to expect any audio
            '-loglevel', 'error',
        ]
        if self.movie_file_extension == ".mov":
            # This is if the background of the exported
            # video should be transparent.
            command += [
                '-vcodec', 'qtrle',
            ]
        elif self.movie_file_extension == ".gif":
            command += []
        else:
            command += [
                '-vcodec', 'libx264',
                '-pix_fmt', 'yuv420p',
            ]
        command += [self.temp_file_path]
        self.writing_process = sp.Popen(command, stdin=sp.PIPE)

    def write_frame(self, imgs, pixel_shape):
        if self.write_to_movie:
            siz = pixel_shape[1]
            img = Image.new(mode='RGBA', size=(siz*3, siz*2))
            for i, j in enumerate(imgs):
                img.paste(im=j, box=(i % 3*siz, i//3*siz))
            self.writing_process.stdin.write(
                img.transpose(Image.FLIP_TOP_BOTTOM).tobytes())


class Scene360(Scene):
    CONFIG = {
        "camera_config": {
            "frame_config": {
                "frame_shape": (0.1, 0.1),
                "focal_distance": 0.5
            },
            "samples": 4
        }
    }

    def __init__(self, **kwargs):
        if "camera_config" in kwargs and "pixel_height" in kwargs["camera_config"]:
            kwargs["camera_config"]["pixel_width"] = kwargs["camera_config"]["pixel_height"]
        super().__init__(**kwargs)
        self.file_writer = SceneFileWriter360(
            self, **self.file_writer_config)

    def emit_frame(self):
        def get_img(camera):
            img = camera.get_image()
            return img
        if not self.skip_animations:
            pixel_shape = self.camera.get_pixel_shape()
            frame = self.camera.frame
            icrm = np.array(frame.get_inverse_camera_rotation_matrix())
            imgs = []

            def capture(matrix, is_front=False):
                euler_angles = frame.get_euler_angles().copy()
                frame.refresh_rotation_matrix()
                frame.rotate_by_matrix(matrix)
                shift=(-np.dot(np.matrix(frame.get_inverse_camera_rotation_matrix()).I,
                             frame.get_focal_distance()*np.array([0, 0, 1]))).tolist()[0]
                frame.shift(shift)
                self.camera.clear()
                self.camera.capture(*self.mobjects)
                imgs.append(get_img(self.camera))
                frame.shift(-np.array(shift))
                frame.set_euler_angles(*euler_angles)
            capture(np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]]))  # right
            capture(np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]]))  # left
            capture(np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]]))  # top
            capture(np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]]))  # bottom
            capture(np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]), True)  # front
            capture(np.array([[-1, 0, 0], [0, 1, 0], [0, 0, -1]]))  # back
            self.file_writer.write_frame(imgs, pixel_shape)
