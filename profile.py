import geni.portal as portal
import geni.rspec.pg as pg

pc = portal.Context()
request = pc.makeRequestRSpec()

# Create one node (type and image selected via the CloudLab UI)
node = request.RawPC("node-0")

# Add startup service to install Docker, QEMU, and run the container
node.addService(pg.Execute(shell="bash", command="""
sudo apt-get update &&
sudo apt-get install -y docker.io qemu-user-static binfmt-support &&
sudo systemctl start docker &&
sudo docker run --rm --privileged multiarch/qemu-user-static --reset -p yes &&
sudo docker pull teacher-llm-runner &&
sudo docker run -d -p 6000:5003 \
  -e GH_RUNNER_TOKEN="A5TUEX3UICMUUBRVPFH2XFDH3WHSI" \
  -e GH_RUNNER_REPO_URL="https://github.com/AutoGraderLLM" \
  -e GH_RUNNER_NAME="teacher-llm-runner" \
  -e GH_RUNNER_LABELS="self-hosted,docker" \
  --name my-teacher-llm-runner teacher-llm-runner
"""))

pc.printRequestRSpec()
