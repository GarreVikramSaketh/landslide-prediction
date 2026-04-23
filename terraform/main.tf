provider "aws" {
  region = "us-east-1"
}

resource "aws_instance" "devops_server" {
  ami           = "ami-0c02fb55956c7d316"
  instance_type = "t2.micro"
  key_name      = "landslide-key"   # 👈 ADD THIS LINE HERE

  tags = {
    Name = "Landslide-DevOps"
  }
}

resource "aws_eip" "devops_ip" {
  instance = aws_instance.devops_server.id
  domain   = "vpc"
}

output "public_ip" {
  value = aws_eip.devops_ip.public_ip
}