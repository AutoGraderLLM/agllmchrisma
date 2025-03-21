  # Import the Portal object.
  import geni.portal as portal
  # Import the ProtoGENI library.
  import geni.rspec.pg as pg

  # Create a portal context.
  pc = portal.Context()

  # Create a Request object to start building the RSpec.
  request = pc.makeRequestRSpec()

  # Add a raw PC to the request.
  node = request.RawPC("node-0")

  # Specify the disk image.
  node.disk_image = "urn:publicid:IDN+emulab.net+image+UBUNTU20-64-STD"

  # Install Docker and run the container.
  node.addService(pg.Execute(shell="bash", command="""
    sudo apt-get update &&
    sudo apt-get install -y docker.io &&
    sudo systemctl start docker &&
    sudo docker run your-docker-image
  """))

  # Print the RSpec to the enclosing page.
  pc.printRequestRSpec()
