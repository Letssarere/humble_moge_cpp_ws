# MIT License
#
# Copyright (c) 2025 Institute for Automotive Engineering (ika), RWTH Aachen University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import LogInfo
from launch.actions import OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _resolve_onnx_path(onnx_path, package_share_dir):
    expanded_onnx_path = os.path.expanduser(onnx_path.strip())
    if os.path.isabs(expanded_onnx_path):
        return os.path.abspath(expanded_onnx_path)

    return os.path.abspath(os.path.join(package_share_dir, expanded_onnx_path))


def _create_moge_trt_node(context):
    params_file = LaunchConfiguration("params_file").perform(context).strip()
    onnx_path = LaunchConfiguration("onnx_path").perform(context).strip()
    package_share_dir = get_package_share_directory("moge_trt")

    if not params_file or not os.path.isfile(params_file):
        raise RuntimeError(f"Parameter file not found: '{params_file}'")
    if not onnx_path:
        raise RuntimeError("Launch argument 'onnx_path' must not be empty.")

    resolved_onnx_path = _resolve_onnx_path(onnx_path, package_share_dir)

    if not os.path.isfile(resolved_onnx_path):
        raise RuntimeError(
            f"ONNX file not found: '{resolved_onnx_path}'. "
            "Provide a valid onnx_path (absolute path or package-share relative path)."
        )

    return [
        LogInfo(msg=f"[moge_trt] Using ONNX model: {resolved_onnx_path}"),
        Node(
            package="moge_trt",
            executable="moge_trt_main",
            name="moge_trt",
            output="screen",
            remappings=[
                ("~/input/image", "/camera/color/image_raw"),
                ("~/input/camera_info", "/camera/color/camera_info"),
                ("~/output/depth_image", "/moge_trt/output/depth_image"),
                ("~/output/point_cloud", "/moge_trt/output/point_cloud"),
            ],
            parameters=[params_file, {"onnx_path": resolved_onnx_path}],
        ),
    ]


def generate_launch_description():
    moge_trt_dir = get_package_share_directory("moge_trt")
    default_params_file = os.path.join(moge_trt_dir, "config", "moge_trt.param.yaml")

    params_file_arg = DeclareLaunchArgument(
        "params_file",
        default_value=default_params_file,
        description="Path to parameter file for moge_trt",
    )
    onnx_path_arg = DeclareLaunchArgument(
        "onnx_path",
        default_value="models/moge-2_vits_normal_291x518_dynamo_sim.onnx",
        description=(
            "ONNX path. Absolute path is used as-is. Relative path is resolved "
            "against the moge_trt package share directory."
        ),
    )

    return LaunchDescription([
        params_file_arg,
        onnx_path_arg,
        OpaqueFunction(function=_create_moge_trt_node),
    ])
