# SLIDE CONTENT COPY-PASTE CHEAT SHEET (WEEK 2 PROGRESS REPORT - 6 SLIDES)
**Target PowerPoint File:** `D:\Thesis\weekly report w2.pptx` (or duplicate the Week 1 template)  
**Topic:** Week 2 Progress Report - Multimodal AI Prototype Polish & ROS 2 / SLAM Infrastructure Bring-Up  
**Student:** Huynh Chien (Huỳnh Chiến) | **Advisor:** Mr. Lanh (Thầy Lành)  

---

## 🪟 SLIDE 1: TITLE & EXECUTIVE SUMMARY

| Slide Location | Content to Copy (Paste below) |
| :--- | :--- |
| **Main Title** | **WEEKLY PROGRESS REPORT - WEEK 2: MULTIMODAL AI PROTOTYPE POLISH & ROS 2 / SLAM ROBOT INFRASTRUCTURE BRING-UP** |
| **Subtitle** | Course: Graduation Thesis (Pre-Thesis Phase)<br>Advisor: **Mr. Lanh (Thầy Lành)**<br>Student: **Huynh Chien (Huỳnh Chiến)** |
| **Weekly Summary (3 Bullets)** | • **Robot Subsystem Bring-Up on WSL 2:** Established ROS 2 Lyrical on Ubuntu 26.04, connected Gazebo 3D simulation, verified real-time sensor streams (LiDAR `/scan`, Odometry `/odom`, TF tree) via teleoperation, and validated **SLAM Toolbox & Nav2** compatibility.<br>• **Computer Vision & Multi-Object Tracking (MOT):** Integrated a zero-lag camera thread, YOLOv8n ($53\text{ FPS}$ on CPU), and an IoU + Centroid tracker assigning persistent Track IDs, enabling proactive citizen greetings without spam repeats.<br>• **Adaptive Web Search Fallback & Guardrail:** Implemented intelligent web search for queries outside local DB (with mandatory Disclaimer and URL citations), casual banter handling, and sub-millisecond ($< 0.1\text{ ms}$) noise filtering. |

---

## 🪟 SLIDE 2: WEEK 2 OBJECTIVES & HYBRID DUAL-SUBSYSTEM ARCHITECTURE

| Slide Text Box | Content to Copy (Paste below) |
| :--- | :--- |
| **Slide Title** | **WEEK 2 OBJECTIVES & HYBRID DUAL-SUBSYSTEM ARCHITECTURE** |
| **Left Box: Week 2 Objectives** | **1. Core Research Milestones Completed in Week 2:**<br>• Install, configure, and verify robot simulation bring-up: ROS 2 Lyrical, Gazebo Sim, SLAM Toolbox, and Nav2 stack on Ubuntu 26.04 (WSL 2). Perform teleop sensor checks.<br>• Upgrade the AI Prototype from single-turn local Q&A into an **Intelligent Multimodal Assistant** (Voice STT/TTS + Computer Vision + Multi-tier Intent Guardrail + Adaptive Web Search Fallback for unindexed knowledge).<br>• Attain a **100% Pass Rate across all 6 automated test suites**. |
| **Right Box: Hybrid Architecture** | **2. Hybrid Distributed Architecture Design (Windows 11 + WSL 2):**<br>• **Subsystem 1 (Windows 11):** Executes Human-Machine Interaction (HMI: Mic, Speaker, Camera, Faster-Whisper, ChromaDB RAG, Gemini LLM, Guardrail).<br>• **Subsystem 2 (WSL 2 Ubuntu):** Executes deterministic real-time robotics tasks (ROS 2 Lyrical, LiDAR, Odometry, TF transformations, Nav2 path planning).<br>• **Compute Decoupling:** Isolates heavy multimodal reasoning from high-frequency motor control loops, laying the groundwork for the upcoming IPC Bridge Layer. |

---

## 🪟 SLIDE 3: ROBOT SUBSYSTEM: BRING-UP, MOTION & BOTTLENECK ANALYSIS (ROS 2 & GAZEBO)

| Slide Text Box | Content to Copy (Paste below) |
| :--- | :--- |
| **Slide Title** | **ROBOT SUBSYSTEM: BRING-UP, MOTION & BOTTLENECK ANALYSIS (ROS 2 & GAZEBO)** |
| **Left Box: Gazebo Simulation & Motion Verification** | **1. 3D Simulation Environment & Motion Verification:**<br>• **TurtleBot3 Waffle Model:** Successfully spawned into `turtlebot3_world` with differential drive kinematics, 2D planar LiDAR sensor, and coordinate frame tree (TF).<br>• **`ros_gz_bridge` Data Bridge:** Real-time velocity and sensor message translation between ROS 2 Lyrical and Gazebo Sim 10.5.0.<br>• **Teleoperation Drive Check (`teleop_keyboard`):** Streamed `/cmd_vel` velocity commands from the terminal, successfully driving the robot forward and rotating in-place in simulation. |
| **Right Box: Bottleneck Analysis & SLAM/Nav2 Roadmap** | **2. Bottleneck Analysis & SLAM / Nav2 Roadmap:**<br>• **RTF Bottleneck Diagnosis ($\sim 35\%$):** Verified via `nvidia-smi` that the RTX 3050 ($4\text{ GB}$) is active, yet the Real-Time Factor (RTF) is throttled to $\sim 35\%$ due to NVIDIA Optimus hybrid display routing (`Disp.A: Off`) and WSLg D3D12 virtualization overhead.<br>• **Decoupled Architecture Solution:** Offload 3D simulation to headless background compute, delegating real-time visualization strictly to **RViz2** (lightweight 2D point clouds at 60 FPS, eliminating frame bottlenecks).<br>• **Prepared SLAM & Nav2 Framework:** Deployed `slam_toolbox` and `nav2_bringup`, fully ready for perimeter room mapping and waypoint navigation. |

---

## 🪟 SLIDE 4: COMPUTER VISION & MULTI-OBJECT TRACKING (MOT & PROACTIVE GREETING)

| Slide Text Box | Content to Copy (Paste below) |
| :--- | :--- |
| **Slide Title** | **COMPUTER VISION & MULTI-OBJECT TRACKING (MOT & PROACTIVE GREETING)** |
| **Left Box: Zero-Lag Camera & YOLOv8** | **1. Real-Time Zero-Lag Camera Stream & Perception:**<br>• Implemented a multi-threaded `VideoCaptureThread` running a background worker with `buffer_size = 1`, completely eliminating OpenCV frame-buffer latency.<br>• Deployed an optimized **YOLOv8n** model achieving **$53\text{ FPS}$** ($\sim 18.8\text{ ms}$ on standard CPU), instantly detecting citizens and documents.<br>• **Multimodal VQA:** When a citizen asks about a document, the camera captures an instant snapshot and routes it to Gemini 2.5 Flash for multimodal visual inspection. |
| **Right Box: MOT Tracking & Smart Greeting** | **2. Pure-Python MOT Tracker & Greeting Spam Elimination:**<br>• **`PersonTracker` Algorithm:** Combines Intersection over Union (IoU) and Centroid Distance matching, assigning persistent **Track IDs** without brittle C++ dependencies.<br>• **Spam Greeting Elimination:** Tracks `is_greeted = True` state; seated citizens are greeted **strictly once**, eliminating annoying 20-second cooldown repeat loops.<br>• **Real-World Edge Case Handling:** Welcomes incoming citizens when users swap seats; greets groups collectively (`count > 1`); and pauses proactive greetings during active conversations (Session Lock). |

---

## 🪟 SLIDE 5: ADAPTIVE WEB SEARCH FALLBACK & MULTI-TIER GUARDRAIL

| Slide Text Box | Content to Copy (Paste below) |
| :--- | :--- |
| **Slide Title** | **ADAPTIVE WEB SEARCH FALLBACK & MULTI-TIER GUARDRAIL** |
| **Left Box: 4-Tier Guardrail Architecture** | **1. Sub-Millisecond ($< 0.1\text{ ms}$) Multi-Tier Safety Guardrail:**<br>• **Tier 1 (Noise & Profanity Gate):** Filters Whisper hallucination fillers (*"alo"*, *"um"*, *"1 2 3"*) and issues polite civility warnings for offensive language.<br>• **Tier 2 (Persona Chit-Chat):** Delivers witty, public-service aligned responses for casual banter (*"who are you"*, *"do you have a boyfriend"*, *"sing a song"*), **gently guiding users back to public procedures**.<br>• **Tier 3 (Out-of-Scope Deflection):** Deflects off-topic queries (recipes, gaming, math homework) without calling cloud APIs.<br>• **100% Cost & Latency Savings:** Reduces response latency from $3\text{ s}$ down to **$0.09\text{ ms}$** for trolling/chitchat. |
| **Right Box: Adaptive Web Search Fallback** | **2. Adaptive Web Search Fallback for Out-of-Database Queries:**<br>• **Triggered on Low Similarity (Score $< 0.55$):** Instead of a blunt refusal, automatically launches intelligent web search via Tavily AI.<br>• **Two-Pronged Adaptive Routing (`is_admin`):**<br>  - *Unindexed Public Procedures:* Restricts search scope strictly to verified government portals (`.gov.vn`, `chinhphu.vn`, `luatvietnam.vn`).<br>  - *Civic Utility Queries (e.g. Weather):* Expands to open web search with live calendar injection for real-time forecasts.<br>• **Legal Transparency & Safety:** Automatically attaches a mandatory **Disclaimer Warning Box** and verbatim **URL Source Citations**. |

---

## 🪟 SLIDE 6: QUANTITATIVE BENCHMARKS & WEEK 3 ROADMAP (MIDTERM SPRINT)

| Slide Text Box | Content to Copy (Paste below) |
| :--- | :--- |
| **Slide Title** | **QUANTITATIVE BENCHMARKS & WEEK 3 ROADMAP (MIDTERM SPRINT)** |
| **Top Box: Benchmark Data** | *(Copy and paste the quantitative validation table below)* |
| **Bottom Box: Week 3 Roadmap** | **WEEK 3 RESEARCH ROADMAP (MIDTERM SPRINT - POLISH & ROBUSTNESS):**<br>1. **Multi-Turn Contextual Dialogue Memory:** Implement a 3-turn sliding window memory, maintaining conversation context for follow-up questions (*"how much is it"*, *"where do I go"*, *"how long does it take"*).<br>2. **Robot Touchscreen Web UI:** Build an interactive frontend (Streamlit / Web) displaying live avatar emotions, camera stream with bounding boxes, and grounded legal citations.<br>3. **Enrich One-Stop Administrative Knowledge:** Ingest frequently requested civil procedures (Marriage registration, Birth certificate, Driver's license renewal).<br>4. **Full 2D Map Scanning in Simulation:** Drive TurtleBot3 to serialize a complete static occupancy grid map (`my_map.yaml` & `my_map.pgm`) in Gazebo. |

---

### 📊 TABLE TO PASTE INTO SLIDE 6 (WEEK 2 EMPIRICAL VALIDATION BENCHMARKS):

| Subsystem / Feature | Engineering Mechanism | Measured Latency | Pass Rate / Validation |
| :--- | :--- | :---: | :---: |
| **Speech Recognition (STT)** | Faster-Whisper Base (CUDA FP16) | $0.28\text{ -- }0.45\text{ s}$ | 100% (Accurate Vietnamese phonetics) |
| **Safety Guardrail & Filter** | Pure Regex State Machine (4 Tiers) | **$0.09\text{ ms}$** | **100% (22/22 unit test cases PASS)** |
| **Internal RAG Retrieval & LLM** | ChromaDB + Gemini 2.5 Flash | $1.8\text{ -- }2.3\text{ s}$ | 100% (Strict legal citations, 0% hallucination) |
| **Live Weather Fallback** | Tavily Search + Realtime Temporal Date | $2.1\text{ -- }2.8\text{ s}$ | 100% (Includes warning box & URL citations) |
| **Computer Vision (Perception)** | Zero-Lag Camera + YOLOv8n (CPU) | **$18.8\text{ ms}$ ($53\text{ FPS}$)** | 100% (Instant real-time citizen detection) |
| **MOT Tracking & Anti-Spam** | Pure-Python IoU Tracker (Track ID) | **$0.08\text{ ms}$** | 100% (Strict single-greeting state persistence) |
| **Robot Hardware & Teleop** | Gazebo Sim + Teleop + RViz2 (WSL 2) | Real-time stream | 100% (Flawless `/scan`, `/odom`, and TF pipeline) |
