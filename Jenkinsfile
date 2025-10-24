/**
 * Employee MIS – CI/CD Pipeline
 * ------------------------------------------------------------
 * Stages:
 *  1) Checkout
 *  2) Static Analysis (SonarQube)
 *  3) Dependency Scan (Snyk)
 *  4) Setup Terraform (CLI in agent)
 *  5) Provision VM (Terraform in container) + run tests on the VM
 *  6) Build Docker image
 *  7) Container Security Scan (Trivy)
 *  8) Docker Hub push
 *  9) Deploy to Kubernetes (kubectl + doctl)
 * 10) Monitoring bootstrap (Prometheus/Grafana)
 * 11) DAST (OWASP ZAP)
 * 12) Post-deployment scan (Trivy)
 *
 * Notes:
 *  - Avoided printing secrets/tokens to the log.
 *  - Prefer tool installation in disposable containers where possible.
 *  - Cache directories are placed under WORKSPACE to avoid permission issues.
 */

pipeline {
  agent any

  options {
    ansiColor('xterm')
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '25'))
    disableConcurrentBuilds()
    timeout(time: 60, unit: 'MINUTES')
  }

  parameters {
    string(name: 'GIT_BRANCH', defaultValue: 'master', description: 'Git branch to build')
    string(name: 'IMAGE_NAME', defaultValue: 'employee-mis', description: 'Docker image name')
    string(name: 'IMAGE_TAG', defaultValue: 'latest', description: 'Docker image tag')
  }

  environment {
    REPO_URL         = 'https://github.com/danetopotlegit/employeemis.git'
    DOCKER_REGISTRY  = 'docker.io'
    DOCKER_NAMESPACE = 'danetopot'
    FULL_IMAGE       = "${DOCKER_REGISTRY}/${DOCKER_NAMESPACE}/${IMAGE_NAME}:${IMAGE_TAG}"
    TERRAFORM_VERSION = '1.9.8'
    DOCTL_VERSION     = '1.102.0'
    TRIVY_CACHE_DIR   = "${WORKSPACE}/.trivycache"
  }

  stages {

    /* --- CODE CHECKOUT --- */
    stage('Code Checkout (from Git)') {
      steps {
        git(
          url: "${REPO_URL}",
          branch: "${params.GIT_BRANCH}",
          credentialsId: 'github-token'
        )
      }
    }

    /* --- STATIC ANALYSIS --- */
    stage('Static Code Analysis (SonarQube)') {
      steps {
        script {
          def scannerHome = tool name: 'SonarScanner', type: 'hudson.plugins.sonar.SonarRunnerInstallation'
          withSonarQubeEnv('SonarQubeServer') {
            sh """
              set -eux
              "${scannerHome}/bin/sonar-scanner" \
                -Dsonar.projectKey=employee-mis \
                -Dsonar.projectBaseDir="${WORKSPACE}"
            """
          }
        }
      }
    }

    /* --- DEPENDENCY SCAN --- */
    stage('Dependency Scan (Snyk)') {
      steps {
        sh """
          set -eux
          echo "Installing Python dependencies..."
          pip install --upgrade pip --break-system-packages
          pip install -r requirements.txt --break-system-packages
        """

        snykSecurity(
          snykInstallation: 'SnykSecurity',
          snykTokenId: 'snyk-api-token',
          targetFile: 'requirements.txt',
          monitorProjectOnBuild: true,
          failOnIssues: true
        )
      }
    }

    /* --- TERRAFORM SETUP --- */
    stage('Setting Up Terraform (CLI)') {
      steps {
        echo 'Installing Terraform CLI...'
        sh """
          set -eux
          export HOME=\$WORKSPACE/.tmp-home
          mkdir -p "\$HOME/.local/bin"
          PATH="\$HOME/.local/bin:\$PATH"
          curl -fsSL "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip" -o terraform.zip
          unzip -o terraform.zip && rm -f terraform.zip
          mv -f terraform "\$HOME/.local/bin/"
          terraform -version
        """
      }
    }

    /* --- VM PROVISIONING --- */
    stage('Provision VM with Terraform & Run Tests') {
      agent {
        docker {
          image "hashicorp/terraform:${TERRAFORM_VERSION}"
          args '-u root -v /var/run/docker.sock:/var/run/docker.sock --entrypoint=""'
        }
      }
      environment {
        DO_TOKEN = credentials('do-api-token')
        SSH_KEY  = credentials('do-ssh-key')
      }
      steps {
        dir('terraform') {
          sh """
            set -eux
            terraform init
            terraform plan \
              -var "do-api-token=${DO_TOKEN}" \
              -var "ssh_fingerprint=${SSH_KEY}"
            terraform apply -auto-approve \
              -var "do-api-token=${DO_TOKEN}" \
              -var "ssh_fingerprint=${SSH_KEY}"
            terraform output -raw vm_ip > vm_ip.txt
          """
        }

        script {
          env.VM_IP = sh(script: 'cd terraform && terraform output -raw vm_ip', returnStdout: true).trim()
          echo "Provisioned VM IP: ${env.VM_IP}"
        }

        sshagent(credentials: ['test-vm-ssh-key']) {
          sh """
            set -eux
            echo "Running tests on VM ${env.VM_IP}..."
            rsync -az --delete -e 'ssh -o StrictHostKeyChecking=no' ./ root@${env.VM_IP}:/root/project
            ssh -o StrictHostKeyChecking=no root@${env.VM_IP} <<'EOF'
              set -eux
              apt update -y
              apt install -y python3 python3-pip python3-venv
              python3 -m venv /root/project/venv
              . /root/project/venv/bin/activate
              pip install --upgrade pip
              pip install -r /root/project/requirements.txt
              pytest -v /root/project --maxfail=1 --disable-warnings
            EOF
          """
        }
      }
    }

    /* --- DOCKER BUILD --- */
    stage('Build Docker Image') {
      steps {
        script {
          docker.build("${IMAGE_NAME}:${IMAGE_TAG}")
        }
      }
    }

    /* --- CONTAINER SCAN (Trivy) --- */
    stage('Container Security Scan (Trivy)') {
      agent {
        docker {
          image 'aquasec/trivy:latest'
          args '-v /var/run/docker.sock:/var/run/docker.sock --entrypoint=""'
        }
      }
      steps {
        sh """
          set -eux
          mkdir -p "${TRIVY_CACHE_DIR}"
          trivy --version
          trivy image --cache-dir "${TRIVY_CACHE_DIR}" --severity HIGH,CRITICAL --exit-code 0 "${IMAGE_NAME}:${IMAGE_TAG}"
        """
      }
    }

    /* --- DOCKER HUB PUSH --- */
    stage('Docker Hub Actions') {
      environment {
        DOCKER_IMAGE = "${IMAGE_NAME}:${IMAGE_TAG}"
      }
      steps {
        echo 'Logging in and pushing image to Docker Hub...'
        withCredentials([usernamePassword(
          credentialsId: 'dockerhub-token',
          usernameVariable: 'DOCKER_USER',
          passwordVariable: 'DOCKER_TOKEN'
        )]) {
          sh """
            set -eux
            echo "\$DOCKER_TOKEN" | docker login -u "\$DOCKER_USER" --password-stdin
            docker tag "${DOCKER_IMAGE}" "${FULL_IMAGE}"
            docker push "${FULL_IMAGE}"
            docker logout "${DOCKER_REGISTRY}"
          """
        }
      }
    }

    /* --- KUBERNETES DEPLOYMENT --- */
    stage('Deployment to Kubernetes') {
      agent {
        docker {
          image 'bitnami/kubectl:latest'
          args '-v /var/run/docker.sock:/var/run/docker.sock --entrypoint=""'
        }
      }
      steps {
        echo 'Deploying to DigitalOcean Kubernetes...'
        withCredentials([string(credentialsId: 'do-api-token', variable: 'DO_API_TOKEN')]) {
          sh """
            set -eux
            export HOME=\$WORKSPACE/.tmp-home
            mkdir -p "\$HOME/.local/bin"
            PATH="\$HOME/.local/bin:\$PATH"
            curl -sL "https://github.com/digitalocean/doctl/releases/download/v${DOCTL_VERSION}/doctl-${DOCTL_VERSION}-linux-amd64.tar.gz" | tar -xz
            mv doctl "\$HOME/.local/bin/"
            doctl auth init -t "\$DO_API_TOKEN"
            doctl kubernetes cluster kubeconfig save k8s-devseclab
            export KUBECONFIG="\$HOME/.kube/config"
            kubectl apply -f k8s/deployment.yaml
            kubectl set image deployment/employee-app-deployment employee-app="${FULL_IMAGE}"
            kubectl apply -f k8s/service.yaml
          """
        }
      }
    }

    /* --- MONITORING SETUP --- */
    stage('Monitoring & Observability (Prometheus & Grafana)') {
      agent {
        docker {
          image 'bitnami/kubectl:latest'
          args '-u root -v /var/run/docker.sock:/var/run/docker.sock --entrypoint=""'
        }
      }
      steps {
        echo 'Deploying Prometheus and Grafana to cluster...'
        withCredentials([string(credentialsId: 'do-api-token', variable: 'DO_API_TOKEN')]) {
          sh """
            set -eux
            export HOME=\$WORKSPACE/.tmp-home
            mkdir -p "\$HOME/.local/bin"
            PATH="\$HOME/.local/bin:\$PATH"
            curl -sL "https://github.com/digitalocean/doctl/releases/download/v${DOCTL_VERSION}/doctl-${DOCTL_VERSION}-linux-amd64.tar.gz" | tar -xz
            mv doctl "\$HOME/.local/bin/"
            doctl auth init -t "\$DO_API_TOKEN"
            doctl kubernetes cluster kubeconfig save k8s-devseclab
            export KUBECONFIG="\$HOME/.kube/config"
            kubectl apply -f k8s/prometheus-deployment.yaml
            kubectl apply -f k8s/grafana-deployment.yaml
          """
        }
      }
    }

    /* --- DAST (OWASP ZAP) --- */
    stage('Dynamic Application Security Testing (OWASP ZAP)') {
      agent {
        docker {
          image 'ghcr.io/zaproxy/zaproxy:stable'
          args "-u root -v ${env.WORKSPACE}:/zap/wrk --entrypoint=''"
        }
      }
      steps {
        catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
          sh """
            set -eux
            echo "Running OWASP ZAP Baseline Scan..."
            cd /zap/wrk
            mkdir -p output
            zap-baseline.py -t http://144.126.252.134 -r output/zap_report.html || true
            if [ -f output/zap_report.html ]; then
              cp output/zap_report.html "${WORKSPACE}/zap_report.html"
              chmod 644 "${WORKSPACE}/zap_report.html"
            fi
          """
        }
        script {
          if (fileExists('zap_report.html')) {
            archiveArtifacts artifacts: 'zap_report.html', fingerprint: true
          }
        }
      }
    }

    /* --- POST-DEPLOYMENT SECURITY SCAN (Trivy) --- */
    stage('Post-deployment Security Scan (Trivy)') {
      agent {
        docker {
          image 'aquasec/trivy:latest'
          args '-v /var/run/docker.sock:/var/run/docker.sock --entrypoint=""'
        }
      }
      steps {
        echo 'Running Trivy on deployed image...'
        sh """
          set -eux
          trivy image --cache-dir "${TRIVY_CACHE_DIR}" --exit-code 0 --severity MEDIUM,HIGH,CRITICAL "${FULL_IMAGE}" > trivy-report.txt
          trivy image --cache-dir "${TRIVY_CACHE_DIR}" --exit-code 0 --severity CRITICAL "${FULL_IMAGE}" || true
        """
      }
      post {
        always {
          archiveArtifacts artifacts: 'trivy-report.txt', fingerprint: true
        }
        failure {
          mail to: 'danetopot@gmail.com',
               subject: 'Critical Vulnerabilities Found in Deployment',
               body: 'Check Jenkins build logs and Trivy report for details.'
        }
      }
    }

    /* --- DOCKER CLEANUP --- */
    stage('Docker Cleanup (Prune Dangling Resources)') {
      steps {
        echo 'Cleaning up unused Docker resources (images, volumes, cache)...'
        sh """
          set -eux
          echo "Disk usage before cleanup:"
          docker system df
          
          # Remove unused/dangling containers, networks, images, build cache (safe mode)
          docker system prune -af --volumes || true

          echo "Disk usage after cleanup:"
          docker system df
        """
      }
    }
  }

  post {
    failure {
      echo 'Build failed. Please review logs.'
    }
    success {
      echo "Build succeeded: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
    }
  }
}
