import geni.portal as portal
import geni.rspec.pg as pg

pc = portal.Context()
request = pc.makeRequestRSpec()

# Create one RawPC node and set the disk image to Ubuntu 22.04 64-bit (x86_64)
node = request.RawPC("node-0")
node.disk_image = "urn:publicid:IDN+utah.cloudlab.us+image+ubuntu22-04-64"

# Add startup service to install Docker and Python, but do not pull or run any container.
node.addService(pg.Execute(shell="bash", command="""
sudo apt-get update &&
sudo apt-get install -y docker.io python3 python3-pip &&
sudo systemctl start docker
"""))

pc.printRequestRSpec()
