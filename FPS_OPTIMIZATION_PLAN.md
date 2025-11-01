# FPS Optimization Plan - Unknown Person Alert System

## 🎯 Current State

- **Current FPS**: 50-60 FPS (GPU mode)
- **GPU**: NVIDIA A10-24Q (24GB, Compute 8.6)
- **Model**: InsightFace buffalo_l
- **Detection Size**: 640x640
- **Frame Skip**: 0 (process every frame)
- **Bottlenecks**:
  1. Large detection input size (640x640)
  2. Processing every single frame
  3. Sequential processing pipeline
  4. No batch processing for multiple faces
  5. Heavy buffalo_l model

## 🚀 Target Goals

- **Primary Goal**: 80-120 FPS (40-100% improvement)
- **Constraint**: Maintain current accuracy
- **Acceptable Trade-off**: Minimal latency increase (< 100ms)

---

## 📋 Optimization Strategies

### **TIER 1: Quick Wins (Config Changes Only)**

#### 1️⃣ Reduce Detection Input Size
**Change**: `DET_SIZE: (640, 640) → (480, 480)`

**Rationale**:
- Detection size determines input to face detection network
- 640x640 can detect faces as small as 24x24 pixels
- 480x480 can detect faces as small as 18x18 pixels (still excellent)
- 25% reduction in input pixels = 20-30% faster detection

**Impact**:
- ✅ **FPS Gain**: +15-20 FPS (60 → 75-80 FPS)
- ✅ **Accuracy Impact**: Minimal (only affects faces < 20x20 pixels)
- ✅ **Detection Range**: Still excellent for normal surveillance distances
- ✅ **Implementation**: 1 line change in `config.py`

**Test Before/After**:
```python
# Before: DET_SIZE = (640, 640)
# After:  DET_SIZE = (480, 480)
# Verify: Check smallest face detected still works
```

---

#### 2️⃣ Smart Frame Skipping
**Change**: `FRAME_SKIP: 0 → 1` (process every 2nd frame)

**Rationale**:
- Video at 60 FPS means new frame every 16.7ms
- Person movement in 33ms (2 frames) is minimal
- Processing 30 FPS is still real-time
- Human perception: 24 FPS is smooth
- Unknown person detection doesn't need 60 FPS

**Impact**:
- ✅ **FPS Gain**: 2x throughput (60 → 120 FPS processing speed)
- ✅ **Effective FPS**: 30 FPS actual processing (still real-time)
- ✅ **Accuracy Impact**: NONE (still catches all faces)
- ✅ **Detection Delay**: +33ms (imperceptible)
- ✅ **Implementation**: 1 line change in `config.py`

**Spatial-Temporal Compatibility**:
- ✅ IoU calculation still works (same face position in 33ms)
- ✅ Temporal window (2s) remains effective
- ✅ May need to adjust `TEMPORAL_WINDOW_SECONDS: 2.0 → 3.0`

**Progressive Options**:
```python
FRAME_SKIP = 0  # Process ALL frames (60/60 = 60 FPS)
FRAME_SKIP = 1  # Process every 2nd (60/2 = 30 FPS) - RECOMMENDED
FRAME_SKIP = 2  # Process every 3rd (60/3 = 20 FPS) - Aggressive
```

---

### **TIER 2: Code Optimizations (Moderate Effort)**

#### 3️⃣ Batch Face Recognition
**Current**: Process each face embedding individually
**Optimized**: Batch process all faces in one GPU call

**Implementation**:
```python
# BEFORE (in face_recognizer.py):
for face in faces:
    embedding = self.app.get(img)[0].embedding
    person_id, name, score = self.recognize_face(embedding)

# AFTER:
# 1. Extract all embeddings in one call
all_faces = self.app.get(img)  # Already batched!
embeddings = [face.embedding for face in all_faces]

# 2. Batch compute similarities
# Use numpy broadcasting for all comparisons at once
batch_similarities = np.dot(embeddings, known_embeddings_matrix.T)
```

**Impact**:
- ✅ **FPS Gain**: +15-20 FPS (better GPU utilization)
- ✅ **Accuracy Impact**: NONE (same computations)
- ✅ **Code Changes**: Moderate (refactor recognition logic)
- ✅ **Complexity**: Low-Medium

**Effort**: 1-2 hours

---

#### 4️⃣ Asynchronous Pipeline
**Current**: Sequential (detect frame N → recognize frame N → repeat)
**Optimized**: Pipelined (detect frame N+1 while recognizing frame N)

**Architecture**:
```
Thread 1 (Detection):     [Detect F1] [Detect F2] [Detect F3] ...
                              ↓           ↓           ↓
Queue:                    [F1 faces] [F2 faces] [F3 faces]
                              ↓           ↓           ↓
Thread 2 (Recognition):   [Recog F1 ] [Recog F2 ] [Recog F3 ] ...
```

**Implementation**:
```python
from queue import Queue
from threading import Thread

detection_queue = Queue(maxsize=3)
recognition_queue = Queue(maxsize=3)

def detection_worker(video_stream):
    while True:
        frame = video_stream.read()
        faces = face_detector.detect(frame)
        detection_queue.put((frame, faces))

def recognition_worker():
    while True:
        frame, faces = detection_queue.get()
        results = face_recognizer.recognize_batch(faces)
        recognition_queue.put((frame, results))
```

**Impact**:
- ✅ **FPS Gain**: +20-30 FPS (parallel processing)
- ✅ **Accuracy Impact**: NONE
- ✅ **Latency**: +33-66ms (one frame delay)
- ✅ **Complexity**: Medium

**Effort**: 2-3 hours

---

### **TIER 3: Advanced Optimizations (High Effort)**

#### 5️⃣ TensorRT Optimization
**Change**: Convert ONNX models → TensorRT engines

**What is TensorRT**:
- NVIDIA's inference optimizer
- Fuses layers, optimizes memory
- Uses Tensor Cores on A10 GPU
- Custom kernels for your specific GPU

**Implementation Steps**:
```bash
# 1. Install TensorRT
pip install tensorrt

# 2. Convert ONNX → TensorRT
trtexec --onnx=model.onnx \
        --saveEngine=model.trt \
        --fp16 \
        --workspace=4096

# 3. Update InsightFace to use TensorRT provider
providers = [
    ('TensorrtExecutionProvider', {
        'device_id': 0,
        'trt_fp16_enable': True,
        'trt_max_workspace_size': 4294967296
    })
]
```

**Impact**:
- ✅ **FPS Gain**: +30-50 FPS (50-80% faster)
- ✅ **Accuracy Impact**: Minimal with FP16
- ✅ **GPU**: Optimized for A10 architecture
- ✅ **Complexity**: High

**Challenges**:
- Need to export InsightFace models
- TensorRT compatibility testing
- FP16 calibration for accuracy

**Effort**: 4-6 hours

---

#### 6️⃣ Hybrid Detection + Tracking
**Strategy**: Full detection every N frames, lightweight tracking in between

**Architecture**:
```
Frame 1:  [FULL DETECTION] → 5 faces detected
Frame 2:  [TRACK] → Update positions with optical flow
Frame 3:  [TRACK] → Update positions
Frame 4:  [TRACK] → Update positions
Frame 5:  [TRACK] → Update positions
Frame 6:  [FULL DETECTION] → Verify/update tracks
```

**Implementation**:
```python
# Use OpenCV's CSRT or KCF tracker
import cv2

trackers = []

# Every 5 frames: Full detection
if frame_count % 5 == 0:
    faces = face_detector.detect(frame)
    # Reset trackers
    trackers = [cv2.TrackerCSRT_create() for _ in faces]
    for tracker, face in zip(trackers, faces):
        tracker.init(frame, face.bbox)
else:
    # Lightweight tracking
    for tracker in trackers:
        success, bbox = tracker.update(frame)
        if success:
            # Use tracked bbox for recognition
```

**Impact**:
- ✅ **FPS Gain**: 3-5x (detect 20% of frames)
- ✅ **Effective FPS**: 150-300 FPS
- ✅ **Accuracy**: Slight decrease (tracker drift)
- ✅ **Trade-off**: Periodic full detection maintains accuracy

**Challenges**:
- Tracker can lose face if movement is fast
- Need to handle tracker failures
- Re-detection every N frames adds complexity

**Effort**: 4-6 hours

---

## 🎯 Recommended Implementation Plan

### **Phase 1: Quick Wins (5 minutes)**
**Changes**:
1. `DET_SIZE = (480, 480)`
2. `FRAME_SKIP = 1`
3. `TEMPORAL_WINDOW_SECONDS = 3.0` (adjust for frame skip)

**Expected Result**: **100-120 FPS**

**Testing**:
```bash
# 1. Update config
# 2. Restart app
# 3. Monitor FPS in UI
# 4. Verify unknown detection still works
# 5. Check spatial-temporal matching logs
```

---

### **Phase 2: Batch Processing (1-2 hours)**
**Changes**:
1. Refactor `face_recognizer.py` for batch processing
2. Use numpy broadcasting for similarity computation
3. Add batch size parameter

**Expected Result**: **120-140 FPS**

**Implementation Checklist**:
- [ ] Update `recognize_face()` to `recognize_batch()`
- [ ] Use matrix multiplication for all-to-all similarities
- [ ] Test with multiple faces per frame
- [ ] Verify accuracy maintained

---

### **Phase 3: Async Pipeline (2-3 hours)**
**Changes**:
1. Add threading with queues
2. Separate detection and recognition workers
3. Handle synchronization

**Expected Result**: **150-180 FPS**

**Implementation Checklist**:
- [ ] Create worker threads
- [ ] Add thread-safe queues
- [ ] Handle graceful shutdown
- [ ] Add error handling for queue full/empty
- [ ] Test for race conditions

---

### **Phase 4: Advanced (4-8 hours, Optional)**
**Changes**:
1. TensorRT conversion
2. Hybrid detection + tracking

**Expected Result**: **200-300 FPS**

**Risk**: Higher complexity, may introduce bugs

---

## 📊 Performance Projections

| Phase | Changes | Expected FPS | Effort | Risk |
|-------|---------|-------------|--------|------|
| **Current** | - | 50-60 FPS | - | - |
| **Phase 1** | Config only | 100-120 FPS | 5 min | ⚠️ Low |
| **Phase 2** | Batch processing | 120-140 FPS | 1-2 hrs | ⚠️ Low |
| **Phase 3** | Async pipeline | 150-180 FPS | 2-3 hrs | ⚠️⚠️ Medium |
| **Phase 4** | TensorRT + Tracking | 200-300 FPS | 4-8 hrs | ⚠️⚠️⚠️ High |

---

## ✅ Success Criteria

**Phase 1**:
- ✅ FPS >= 100
- ✅ No false negatives (unknown persons still detected)
- ✅ Spatial-temporal matching still works
- ✅ No increase in duplicate alerts

**Phase 2**:
- ✅ FPS >= 120
- ✅ Recognition accuracy maintained
- ✅ No race conditions

**Phase 3**:
- ✅ FPS >= 150
- ✅ Latency < 100ms
- ✅ Stable operation (no crashes)

---

## 🛠️ Testing Protocol

### Before Optimization:
```bash
# 1. Measure baseline
python benchmark.py --video test_video.mp4 --duration 60

# 2. Record metrics
# - Average FPS
# - Unknown detections count
# - Duplicate count
# - Spatial-temporal matches
```

### After Each Phase:
```bash
# 1. Run same benchmark
# 2. Compare metrics
# 3. Verify accuracy maintained
# 4. Check for regressions
```

### Accuracy Verification:
```bash
# Count should be similar before/after:
grep "Alert: Unknown person" backend.log | wc -l
grep "🎯.*spatial-temporal boost" backend.log | wc -l

# Duplicates should remain low:
ls snapshots/ | wc -l
```

---

## 📝 Implementation Notes

### Phase 1 Config Changes:
```python
# backend/config.py

# Detection optimization
DET_SIZE = (480, 480)  # Was: (640, 640)

# Frame processing
FRAME_SKIP = 1  # Was: 0 (process every 2nd frame)

# Spatial-temporal adjustment
TEMPORAL_WINDOW_SECONDS = 3.0  # Was: 2.0 (compensate for frame skip)
```

### Monitoring Commands:
```bash
# Watch FPS in real-time
tail -f backend/backend.log | grep "FPS:"

# Monitor GPU utilization
watch -n 1 nvidia-smi

# Count spatial-temporal matches
watch -n 2 "grep '🎯' backend/backend.log | wc -l"
```

---

## 🎓 Key Insights

1. **Frame Skip is Free**: No accuracy loss, 2x speedup
2. **Detection Size**: Minor trade-off, significant gain
3. **Batch Processing**: GPU utilization matters
4. **Async**: Parallelism with minimal latency
5. **Your GPU**: A10 is powerful, can handle more

**Recommendation**: Start with Phase 1 (5 min, low risk, big gain)
