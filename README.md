## Kubernetes & Terraform (added)
Files added:
- `k8s/deployment.yaml` - Kubernetes Deployment for the employee app
- `k8s/service.yaml` - ClusterIP Service to expose the app inside the cluster
- `k8s/ingress.yaml` - Optional Ingress object (assumes nginx ingress controller)
- `k8s/prometheus.yml` - Simple Prometheus deployment and service
- `k8s/grafana.yml` - Grafana deployment and service
- `terraform/main.tf` - Terraform script to provision an AWS EC2 instance and security group
- `terraform/variables.tf` - Terraform variables
- `terraform/outputs.tf` - Terraform outputs

### Quick notes
- The Terraform AWS AMI and region variables may need to be updated based on your target region.
- The Terraform user_data expects the application image to be available in a container registry (replace `<your_registry>/employee-app:latest`).
- Prometheus/Grafana manifests are minimal and intended for lab/demo use only — do not use in production without hardening.
- For Kubernetes, build the Docker image locally and `kubectl apply -f k8s/` after loading the image into your cluster (e.g., `minikube image load employee-app:latest` for minikube) or push to a registry.
