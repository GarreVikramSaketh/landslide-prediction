provider "aws" {
  region = "ap-south-1"
}

resource "aws_instance" "devops_server" {
  ami           = "ami-0f5ee92e2d63afc18"   # Amazon Linux (update if needed)
  instance_type = "t2.micro"

  tags = {
    Name = "DevOps-Server"
  }
}