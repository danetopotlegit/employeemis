terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

provider "digitalocean" {
  token = var.ssh_fingerprint
}

resource "digitalocean_droplet" "jenkins_vm" {
  name   = "jenkins-test-vm"
  region = "fra1"                   # Frankfurt region (you can change)
  size   = "s-1vcpu-1gb"            # VM size
  image  = "ubuntu-22-04-x64"       # Ubuntu image
  ssh_keys = [var.ssh_fingerprint]  # SSH key fingerprint added to your DO account
}
