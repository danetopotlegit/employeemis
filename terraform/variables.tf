variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "prefix" {
  type    = string
  default = "devsecops-workshop"
}

variable "ami" {
  type    = string
  # Default Amazon Linux 2 AMI for us-east-1 (may need updating per region)
  default = "ami-0c02fb55956c7d316"
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "public_key_path" {
  type    = string
  default = "~/.ssh/id_rsa.pub"
}
