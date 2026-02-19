# AGENTS.md

## 1. 프로젝트 목적과 운영 원칙

### 1.1 목적
이 워크스페이스의 목적은 로봇 카페 환경에서 Intel RealSense D455f RGB 입력을 사용해 MoGeV2 기반 Metric Depth와 PointCloud를 실시간 생성하는 ROS 2 노드를 안정적으로 운영하는 것이다. 개발은 macOS(Codex)에서 진행하고, 빌드/실행/성능 검증은 Jetson Orin NX(ROS 2 Humble, JetPack 6.x)에서 수행한다.

### 1.2 운영 원칙
- 문서는 항상 `As-Is(현재)`와 `To-Be(목표)`를 분리해서 기록한다.
- 코드 기준 사실을 우선 기록하고, 의도/목표는 별도 섹션으로 분리한다.
- 절대 경로는 코드/런치/파라미터 기본값에서 금지하고, ROS 파라미터 또는 패키지 share 경로 기반으로 해석한다.
- 문서 내 파일 경로는 워크스페이스 상대경로를 기본으로 하고, 환경별 루트는 명령 예시의 `WS_ROOT`로 주입한다.
- 구현 항목은 반드시 `대상 파일`, `완료 기준(DoD)`, `검증 명령`을 함께 유지한다.
- 로봇 카페 물리 환경 특성(반사, 저텍스처, 카메라 하향 설치)을 알고리즘/후처리 설계의 제약으로 취급한다.

## 2. 환경 스냅샷 (As-Is, 기준일: 2026-02-19)

### 2.1 개발/배포 환경

| 항목 | As-Is |
|---|---|
| 개발 환경 | macOS (Apple Silicon), CUDA/TensorRT 미탑재 |
| 배포 환경 | Jetson Orin NX, Ubuntu 22.04, ROS 2 Humble, JetPack 6.x |
| TensorRT | 목표 8.6.2 (JetPack 6 기본) |
| 포크 기반 | `ika-rwth-aachen/ros2-moge-trt` |

### 2.2 현재 상태 요약 (코드 기준)

| 구분 | As-Is (현재 코드) | 근거 파일 |
|---|---|---|
| 입력 이미지 타입 | `sensor_msgs/msg/CompressedImage` 구독 | `src/ros2-moge-trt/moge-trt/src/moge_trt_node/moge_trt_node.cpp` |
| 동기화 방식 | `ApproximateTime(CompressedImage, CameraInfo)` | `src/ros2-moge-trt/moge-trt/include/moge_trt/moge_trt_node.hpp` |
| 내부 토픽 | `~/input/image`, `~/input/camera_info`, `~/output/*` | `src/ros2-moge-trt/moge-trt/src/moge_trt_node/moge_trt_node.cpp` |
| 기본 launch remap | ZED compressed 토픽으로 remap, rosbag play 내장 | `src/ros2-moge-trt/moge-trt/launch/moge_trt.launch.py` |
| ONNX 경로 파라미터 | `config/moge_trt.param.yaml`에 절대 경로 사용 중 | `src/ros2-moge-trt/moge-trt/config/moge_trt.param.yaml` |
| TensorRT workspace API | `setMemoryPoolLimit` + `setMaxWorkspaceSize` 버전 가드 사용 중 | `src/ros2-moge-trt/moge-trt/src/tensorrt_common/tensorrt_common.cpp` |
| Shift recovery | L1(중앙값 기반) 사용 중 | `src/ros2-moge-trt/moge-trt/src/tensorrt_moge/tensorrt_moge.cpp` |

### 2.3 물리 환경 제약 (로봇 카페)
- 센서 배치 및 시야각: `robot-cafe-physical-structure-sensing.mmd`
- 전체 레이아웃/작업 흐름: `robot-cafe-physical-structure-plan.mmd`
- 카메라: 외벽 상단 중앙, 약 35도 하향.
- 관측면: 검정 철제 + 내장 디스플레이(반사/저텍스처)로 아웃라이어 발생 가능성이 높다.

## 3. 목표 아키텍처 (To-Be: Robot Cafe + RealSense D455f + Jetson Humble)

### 3.1 목표 상태 요약

| 구분 | To-Be (목표 상태) |
|---|---|
| Source Node | `realsense2_camera_node` |
| 입력 이미지 타입 | `sensor_msgs/msg/Image` (Raw) |
| 입력 토픽 | `/camera/color/image_raw`, `/camera/color/camera_info` |
| 출력 토픽 | `/moge_trt/output/depth_image`, `/moge_trt/output/point_cloud` |
| 출력 타입 | `Image(32FC1)`, `PointCloud2` |
| 알고리즘 정책 | L1 기반 shift recovery 유지 |
| 배포 기준 | Jetson Orin NX + TensorRT 8.6 호환 |

### 3.2 목표 데이터 흐름
`RealSense RGB Raw + CameraInfo -> moge_trt node -> depth_image(32FC1) + point_cloud`

## 4. 인터페이스 계약 (토픽/파라미터/런치)

### 4.1 토픽 계약

| 계층 | 이름 | 타입 | 계약 |
|---|---|---|---|
| 내부 입력 | `~/input/image` | `sensor_msgs/msg/Image` | Raw 이미지 구독 |
| 내부 입력 | `~/input/camera_info` | `sensor_msgs/msg/CameraInfo` | Intrinsics 필수 |
| 내부 출력 | `~/output/depth_image` | `sensor_msgs/msg/Image` | `32FC1` metric depth |
| 내부 출력 | `~/output/point_cloud` | `sensor_msgs/msg/PointCloud2` | 색상 포함 가능 |
| 외부 remap(표준) | `~/input/image -> /camera/color/image_raw` | - | `robot_cafe.launch.py` 기본값 |
| 외부 remap(표준) | `~/input/camera_info -> /camera/color/camera_info` | - | `robot_cafe.launch.py` 기본값 |
| 외부 remap(권장) | `~/output/depth_image -> /moge_trt/output/depth_image` | - | 시각화/디버깅 일관성 |
| 외부 remap(권장) | `~/output/point_cloud -> /moge_trt/output/point_cloud` | - | 시각화/디버깅 일관성 |

### 4.2 파라미터 계약

| 파라미터 | 타입 | 허용값/범위 | 기본값 | 의미 |
|---|---|---|---|---|
| `onnx_path` | string | 상대 경로 또는 launch 주입 경로 | `models/moge-2_vits_normal_291x518.onnx` | MoGe ONNX 경로 |
| `precision` | string | `fp16`, `fp32` | `fp16` | 추론 정밀도 |
| `point_cloud_downsample_factor` | int | `>=1` | `10` | PointCloud 다운샘플 |
| `colorize_point_cloud` | bool | `true`, `false` | `true` | RGB point cloud 여부 |
| `enable_debug` | bool | `true`, `false` | `false` | 디버그 depth publish |
| `debug_filepath` | string | 쓰기 가능한 경로 | `/tmp/moge_debug/` | 디버그 이미지 저장 경로 |

경로 정책:
- 코드/기본 파라미터는 절대 경로를 기본값으로 두지 않는다.
- 모델 경로는 launch 파라미터 또는 패키지 share 경로로 주입한다.
- 현재 `config/moge_trt.param.yaml`의 절대 경로는 제거 대상이다.

### 4.3 런치 계약
- 신규 파일: `launch/robot_cafe.launch.py`
- 목적: RealSense 기반 표준 remap, rosbag/특정 센서 의존 제거, 배포형 실행 엔트리 제공
- 최소 요구:
  - `moge_trt_main` 노드 실행
  - 표준 remap 적용
  - `params_file` 오버라이드 지원

## 5. Gap 분석 표 (현재 대비 목표)

| ID | Gap | As-Is | To-Be | 우선순위 | 대상 파일 |
|---|---|---|---|---|---|
| G1 | 입력 이미지 타입 불일치 | CompressedImage | Raw Image | Critical | `moge_trt_node.hpp`, `moge_trt_node.cpp` |
| G2 | 기본 launch가 ZED/rosbag 전제 | ZED compressed remap + rosbag play | RealSense 표준 launch | Critical | `launch/moge_trt.launch.py`, `launch/robot_cafe.launch.py` |
| G3 | RealSense 전용 launch 부재 | 없음 | `robot_cafe.launch.py` 추가 | Critical | `launch/robot_cafe.launch.py` |
| G4 | 절대 ONNX 경로 잔존 | 절대 경로 사용 | 상대/주입 경로로 통일 | High | `config/moge_trt.param.yaml` |
| G5 | TensorRT 8.6 문구 불명확 | “지원 여부 확인 필요” 중심 | 버전 가드 존재 + 실빌드 검증 명시 | High | `AGENTS.md`, `tensorrt_common.cpp` |
| G6 | Jetson 경로/링크 검증 부족 | 일반 탐색 중심 CMake | Jetson 실기 빌드 기준 검증 | High | `CMakeLists.txt` |
| G7 | 다운샘플 성능 기준 부재 | 파라미터만 존재 | FPS/지연 기준 포함 최적화 | Medium | `tensorrt_moge.cpp` |

## 6. 우선순위 실행 계획 (Critical/High/Medium)

### 6.1 [Critical] Raw 이미지 구독 전환
- 대상 파일:
  - `src/ros2-moge-trt/moge-trt/include/moge_trt/moge_trt_node.hpp`
  - `src/ros2-moge-trt/moge-trt/src/moge_trt_node/moge_trt_node.cpp`
- 완료 기준(DoD):
  - `CompressedImage` 의존 제거 또는 선택적 지원.
  - 메인 콜백 입력이 `sensor_msgs::msg::Image` 기준으로 동작.
  - camera_info 동기화가 유지된다.
- 검증 명령(Jetson):
  ```bash
  colcon build --packages-select moge_trt --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
  source install/setup.bash
  ros2 node info /moge_trt
  ros2 topic info /camera/color/image_raw
  ```

### 6.2 [Critical] RealSense 표준 launch 추가
- 대상 파일:
  - `src/ros2-moge-trt/moge-trt/launch/robot_cafe.launch.py`
- 완료 기준(DoD):
  - `~/input/image -> /camera/color/image_raw`
  - `~/input/camera_info -> /camera/color/camera_info`
  - 출력 remap은 `/moge_trt/output/*`로 통일.
- 검증 명령(Jetson):
  ```bash
  ros2 launch moge_trt robot_cafe.launch.py
  ros2 topic list | rg "camera/color|moge_trt/output"
  ```

### 6.3 [High] 절대 경로 제거 및 경로 주입 정리
- 대상 파일:
  - `src/ros2-moge-trt/moge-trt/config/moge_trt.param.yaml`
  - `src/ros2-moge-trt/moge-trt/launch/robot_cafe.launch.py`
- 완료 기준(DoD):
  - `onnx_path` 절대 경로 제거.
  - launch/파라미터를 통해 모델 경로를 주입 가능.
- 검증 명령(Jetson):
  ```bash
  rg -n "/docker-ros/ws|^\\s*onnx_path:\\s*/" src/ros2-moge-trt/moge-trt/config src/ros2-moge-trt/moge-trt/launch
  ```

### 6.4 [High] TensorRT 8.6 호환성 문서/코드 검증
- 대상 파일:
  - `src/ros2-moge-trt/moge-trt/src/tensorrt_common/tensorrt_common.cpp`
  - `src/ros2-moge-trt/moge-trt/CMakeLists.txt`
- 완료 기준(DoD):
  - `setMemoryPoolLimit`/`setMaxWorkspaceSize` 버전 가드 유지 확인.
  - Jetson 빌드 성공 여부를 기준으로 실제 호환성 판정.
- 검증 명령(Jetson):
  ```bash
  rg -n "setMemoryPoolLimit|setMaxWorkspaceSize|enqueueV3" src/ros2-moge-trt/moge-trt/src/tensorrt_common/tensorrt_common.cpp
  colcon build --packages-select moge_trt --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
  ```

### 6.5 [Medium] PointCloud 다운샘플 최적화
- 대상 파일:
  - `src/ros2-moge-trt/moge-trt/src/tensorrt_moge/tensorrt_moge.cpp`
- 완료 기준(DoD):
  - 다운샘플 팩터 변경 시 출력 품질/속도 트레이드오프가 문서화.
  - 운영 기본값 확정(예: 2, 4, 8 중 택1).
- 검증 명령(Jetson):
  ```bash
  ros2 topic hz /moge_trt/output/depth_image
  ros2 topic hz /moge_trt/output/point_cloud
  ```

## 7. 플랫폼별 개발 규칙 (macOS vs Jetson)

| 항목 | macOS (Codex 개발) | Jetson (실행/검증) |
|---|---|---|
| 역할 | 코드 작성, 리팩터링, 문서화 | 빌드, 런타임 테스트, 성능 측정 |
| CUDA/TensorRT | 없음(컴파일 불가 전제) | 있음(정식 검증 환경) |
| ROS 확인 | 정적 코드 리뷰 중심 | `ros2 topic/node/launch` 실측 |
| 최종 판정 | 문법/논리 정합성 | 빌드 성공 + 토픽 발행 + FPS |

공통 코딩 규칙:
- C++17, ROS 2 Component 설계 유지.
- 스마트 포인터/RAII 사용, raw pointer 최소화.
- CUDA 메모리는 `cuda_utils` 래퍼 기반으로 관리.
- 리포지토리 추적 파일에는 절대 경로를 기본값으로 고정하지 않는다.

## 8. 검증 체크리스트 (문서/코드/런타임)

### 8.1 문서 무결성
- [ ] Markdown 코드블록이 모두 열림/닫힘 쌍을 갖는다.
- [ ] 파일명/경로/토픽명이 실제 리포지토리와 일치한다.
- [ ] As-Is와 To-Be가 서로 혼합되지 않고 분리되어 있다.

### 8.2 코드 정합성
- [ ] 입력 타입이 `sensor_msgs/msg/Image` 기준으로 정리되어 있다.
- [ ] launch remap이 RealSense 기준으로 반영되어 있다.
- [ ] 절대 ONNX 경로가 기본 설정에서 제거되어 있다.
- [ ] TensorRT 버전 가드가 유지되고 빌드 로그 기준 오류가 없다.

### 8.3 런타임 수용 기준 (후속 구현 완료 후)
- [ ] `ros2 topic info /camera/color/image_raw`에서 실제 publisher 확인.
- [ ] `ros2 node info /moge_trt`에서 예상 구독/발행 토픽 확인.
- [ ] `/moge_trt/output/depth_image` 발행 확인.
- [ ] `/moge_trt/output/point_cloud` 발행 확인.
- [ ] RViz2에서 깊이/포인트클라우드 시각 확인.

## 9. 참조 파일 인덱스 (워크스페이스 상대경로)
- `AGENTS.md`
- `robot-cafe-physical-structure-sensing.mmd`
- `robot-cafe-physical-structure-plan.mmd`
- `src/ros2-moge-trt/moge-trt/CMakeLists.txt`
- `src/ros2-moge-trt/moge-trt/package.xml`
- `src/ros2-moge-trt/moge-trt/config/moge_trt.param.yaml`
- `src/ros2-moge-trt/moge-trt/launch/moge_trt.launch.py`
- `src/ros2-moge-trt/moge-trt/include/moge_trt/moge_trt_node.hpp`
- `src/ros2-moge-trt/moge-trt/src/moge_trt_node/moge_trt_node.cpp`
- `src/ros2-moge-trt/moge-trt/src/tensorrt_moge/tensorrt_moge.cpp`
- `src/ros2-moge-trt/moge-trt/src/tensorrt_common/tensorrt_common.cpp`

## Jetson 빌드/실행/검증 명령 (배포 기준)
```bash
# workspace root
export WS_ROOT=~/humble_moge_cpp_ws
cd "$WS_ROOT"
colcon build --packages-select moge_trt --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/setup.bash

# launch (To-Be)
ros2 launch moge_trt robot_cafe.launch.py

# verify
ros2 node info /moge_trt
ros2 topic list | rg "camera/color|moge_trt/output"
ros2 topic hz /moge_trt/output/depth_image
ros2 topic hz /moge_trt/output/point_cloud
```
