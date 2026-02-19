# Interview Preparation — ArduPilot SITL DevOps Pipeline

Use this document to prepare for DevOps interviews. Every answer below is tied to real work you did in this project.

---

## Part 1: Project-Specific Questions

### "Tell me about your project."

> I built a CI/CD pipeline for ArduPilot drone firmware. The pipeline containerizes the SITL simulator in Docker, runs it inside GitHub Actions, and executes automated MAVLink health-check tests on every push. If the simulator fails to produce a valid heartbeat, the pipeline blocks the merge. The goal was to demonstrate how DevOps practices — containerization, CI automation, and automated testing — apply to safety-critical embedded systems like drones.

### "Why DevOps for drone software?"

> Drone firmware has real-world safety consequences. A regression in flight control code can crash a $10,000 drone or injure someone. DevOps practices catch these regressions early — before the code ever reaches hardware. In my project, the CI pipeline validates firmware health automatically. No human needs to manually test each change. This is the same approach companies like ArduPilot and PX4 use internally.

### "Why SITL instead of a real drone?"

> Three reasons:
> 1. **Cost** — real drones cost $500+. SITL runs on any laptop for free.
> 2. **Safety** — a bug in CI doesn't crash a physical object.
> 3. **CI compatibility** — you can't plug a drone into a GitHub Actions runner. SITL runs in Docker, which runs anywhere.
>
> SITL runs the **exact same firmware binary** as a real drone. The only difference is the physics engine. This makes it the industry standard for drone CI testing.

### "Why did you choose a quadcopter?"

> ArduCopter (quadcopter) is the most commonly used ArduPilot vehicle type. It has the largest community, most documentation, and most stable SITL support. Choosing it eliminates unnecessary complexity — the project is about DevOps, not drone engineering. I could swap to ArduPlane or ArduRover by changing one line in `start_sitl.sh`.

### "Why not cloud? Why no Kubernetes?"

> Scope discipline. This project proves DevOps fundamentals: containerization, CI, and automated testing. Adding AWS/K8s would add infrastructure management complexity without improving the core pipeline. For a fresher project, it's better to have a **working simple pipeline** than a half-built complex one. If I were to extend this, I'd add Terraform for infra-as-code and K8s for multi-SITL orchestration — but only after the basics are proven.

---

## Part 2: DevOps Concept Questions

### "What is CI/CD and how does your project implement it?"

> **CI (Continuous Integration):** Automatically build and test code on every commit. My project does this — every push to `main` triggers a Docker build + SITL test suite.
>
> **CD (Continuous Delivery):** Automatically deploy validated code to a target environment. My project does NOT do this because deploying to a physical drone requires hardware. But the pipeline is structured so a deployment step could be appended after the test stage.

### "What is Docker and why did you use it?"

> Docker packages an application and all its dependencies into an isolated container. ArduPilot SITL requires 50+ Linux packages, specific Python versions, and a compiled C++ binary. Without Docker, every developer and every CI runner would need to install all of these manually — leading to "works on my machine" problems. Docker eliminates this by defining the entire environment in a single `Dockerfile`.

### "What is a Dockerfile? Walk me through yours."

> A Dockerfile is a script that defines how to build a container image. Mine does:
> 1. Starts from `ubuntu:22.04` (base OS)
> 2. Installs build dependencies (gcc, python, git, etc.)
> 3. Clones ArduPilot source at a pinned version tag (`Copter-4.5.7`)
> 4. Installs Python packages (pymavlink, MAVProxy)
> 5. Compiles the ArduCopter SITL binary using `waf`
> 6. Copies in the startup script
> 7. Exposes port 5760 for MAVLink connections
> 8. Defines a health check that tests TCP connectivity

### "What is docker-compose and why use it?"

> `docker-compose` defines multi-container applications in a YAML file. Even though I only have one service (SITL), I use Compose because:
> 1. It's cleaner than long `docker run` commands
> 2. It defines health checks declaratively
> 3. It's the standard for CI pipelines (`docker compose up -d` / `docker compose down`)
> 4. It's extensible — I can add services (database, monitoring) without changing the workflow

### "Explain GitHub Actions. How does your pipeline work?"

> GitHub Actions is a CI/CD platform built into GitHub. My pipeline is defined in `.github/workflows/ci.yml` and runs on every push to `main`. The steps are:
> 1. **Checkout** code
> 2. **Build** Docker image (with layer caching to speed up rebuilds)
> 3. **Start** SITL container in detached mode
> 4. **Health check** — polls port 5760 every 10s until SITL is ready (max 180s)
> 5. **Run tests** — pytest executes 4 MAVLink validation checks
> 6. **Teardown** — containers are removed; logs are uploaded as artifacts if tests fail

### "What is MAVLink?"

> MAVLink is a lightweight binary protocol for communicating with drones. Think of it as HTTP for UAVs. A ground control station sends commands (arm, takeoff, navigate) and the drone sends telemetry (heartbeat, GPS, battery). In my project, the test script uses pymavlink to connect to SITL and verify it's sending heartbeat messages — proving the simulator is alive and functional.

### "What happens when your pipeline fails?"

> 1. The GitHub Actions run shows a red ❌
> 2. If branch protection is enabled, the PR cannot be merged
> 3. Container logs are uploaded as artifacts for debugging
> 4. The developer reviews the logs, fixes the issue, and pushes again
> 5. This is the "fail fast" principle — catch problems before they reach production

### "How would you extend this project?"

> In priority order:
> 1. **Trivy** — scan the Docker image for known vulnerabilities
> 2. **Takeoff test** — send ARM + TAKEOFF commands via MAVLink and verify altitude
> 3. **GHCR** — push the built image to GitHub Container Registry for reuse
> 4. **Branch protection** — require CI pass before merge to `main`
> 5. **Notifications** — Slack/Discord webhook on pipeline failure
> 6. **Multi-vehicle** — Docker Compose `--scale sitl=3` for swarm simulation

---

## Part 3: Troubleshooting Questions

### "Your Docker build is taking 15 minutes. How would you speed it up?"

> 1. **Layer caching** — already implemented. Docker caches unchanged layers.
> 2. **Pre-built binary** — compile SITL once, store the binary in a Docker registry, and pull it instead of building from source.
> 3. **Multi-stage build** — use a builder stage for compilation and a smaller runtime stage for execution.
> 4. **GitHub Actions cache** — use `actions/cache` to persist Docker build layers between runs (already implemented).

### "SITL starts but tests fail. How do you debug?"

> 1. Check container logs: `docker compose logs`
> 2. Check health status: `docker ps` — is SITL healthy?
> 3. Try manual connection: `python -c "from pymavlink import mavutil; m = mavutil.mavlink_connection('tcp:localhost:5760'); print(m.wait_heartbeat())"`
> 4. Check if port 5760 is actually open: `netstat -an | grep 5760`
> 5. In CI: download the uploaded log artifacts from the Actions run

### "What's the difference between SITL and HIL?"

> - **SITL** (Software-In-The-Loop): Everything runs in software. No hardware needed. Used for CI.
> - **HIL** (Hardware-In-The-Loop): Real autopilot hardware connected to a simulated environment. Used for integration testing before flight.
> - My project uses SITL because HIL requires physical hardware that can't run inside Docker or GitHub Actions.

---

## Part 4: Behavioral / Design Questions

### "Why did you scope the project this way?"

> I had 3 days and zero prior DevOps experience. I chose to build a complete, working pipeline over a feature-rich but broken one. Every component — Docker, CI, tests, README — is functional and demonstrable. I explicitly cut Kubernetes, cloud, and advanced flight logic because they would have been half-implemented and unconvincing in an interview.

### "What would you do differently?"

> 1. Use a pre-built SITL Docker image from Docker Hub instead of compiling from source — would cut build time from 15 min to 2 min.
> 2. Add branch protection rules from the start.
> 3. Add a simple takeoff test alongside the heartbeat test for a more impressive demo.

### "What did you learn?"

> 1. Docker is not just "run a container" — writing a good Dockerfile with layer ordering, health checks, and pinned versions is a skill.
> 2. CI pipelines need to handle timing — SITL takes time to boot, so you need health checks and retries.
> 3. Drone firmware CI is structurally identical to any other CI — the application doesn't matter, the automation pattern is the same.
