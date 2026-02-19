# MoGe ONNX Models

This directory should contain the MoGe ONNX model files.

## Required Files

Place your MoGe ONNX model file here:
- `moge-2_vits_normal_291x518_dynamo_sim.onnx` (default)
- Or provide another ONNX path via launch argument.

## Model Format

Expected model specifications:
- **Input**: RGB image, shape [1, 3, H, W], type float32, range [0, 1]
- **Outputs**:
  - `points`: 3D points [1, H, W, 3]
  - `mask`: validity mask [1, H, W]
  - `metric_scale`: depth scale factor [1]

## Installation

After building the package, this directory will be installed to:
```
/path/to/install/share/moge_trt/models/
```

The node will look for models at the path specified in the parameter file.

## Manual Model Placement

Download the model file manually and place it in:

```text
<workspace>/src/ros2-moge-trt/moge-trt/models/
```

Example in this workspace:

```text
/Users/junho/humble_moge_cpp_ws/src/ros2-moge-trt/moge-trt/models/moge-2_vits_normal_291x518_dynamo_sim.onnx
```

Launch usage:

```bash
ros2 launch moge_trt robot_cafe.launch.py \
  onnx_path:=models/moge-2_vits_normal_291x518_dynamo_sim.onnx
```

Path resolution rule:
- Absolute `onnx_path`: used as-is.
- Relative `onnx_path`: resolved against `get_package_share_directory("moge_trt")`.

If the resolved file does not exist, launch fails immediately (fail-fast).

## Engine Cache Behavior

TensorRT engine cache is created automatically from ONNX when needed.

- First run: ONNX is loaded and engine build runs if no cache exists.
- Re-run: cached engine load (build skipped when cache exists).
