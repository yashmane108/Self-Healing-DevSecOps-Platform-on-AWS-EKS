provider "aws" {
  region = "us-east-1"
}

resource "aws_security_group" "demo_sg" {
  name        = "terraform-demo-sg"
  description = "Demo SG for drift testing"

  ingress {
    from_ort   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "TerraformDemoSGG"
  }
}
