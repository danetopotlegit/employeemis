output "vm_ip" {
  value = digitalocean_droplet.jenkins_vm.ipv4_address
}