import geni.portal as portal
import geni.rspec.pg as pg

pc = portal.Context()
request = pc.makeRequestRSpec()

# Create one RawPC node and automatically set the disk image to Ubuntu 22.04
node = request.RawPC("node-0")
node.disk_image = "urn:publicid:IDN+utah.cloudlab.us+image+ubuntu22-04-64"

# Add startup service to install Docker, QEMU, Python, and run the container
node.addService(pg.Execute(shell="bash", command="""
sudo apt-get update &&
sudo apt-get install -y docker.io qemu-user-static binfmt-support python3 python3-pip &&
sudo systemctl start docker &&
sudo docker run --rm --privileged multiarch/qemu-user-static --reset -p yes &&
# Pull the autograding container image (ensure this image is available)
sudo docker pull teacher-llm-runner &&
# Run the container mapping container port 5003 to host port 8080
sudo docker run -d -p 8080:5003 \
  -e GH_RUNNER_TOKEN="A5TUEX6XLQCUYO2TF5G3MCLH3WK3S" \
  -e GH_RUNNER_REPO_URL="https://github.com/AutoGraderLLM" \
  -e GH_RUNNER_NAME="teacher-llm-runner" \
  -e GH_RUNNER_LABELS="self-hosted,docker" \
  --name my-teacher-llm-runner teacher-llm-runner
"""))

pc.printRequestRSpec()
