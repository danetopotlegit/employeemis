/* groovylint-disable LineLength */
pipeline {
    agent any

    stages {
        stage('Code Checkout (from Git)') {
            steps {
                git(
                    url: 'https://github.com/danetopotlegit/employeemis.git' ,
                    branch: 'master',
                    credentialsId: 'github-token'
                    )
            }
        }

        stage('Static Code Analysis (SonarQube)') {
                steps {
                    script {
                        def scannerHome = tool name: 'SonarScanner', type: 'hudson.plugins.sonar.SonarRunnerInstallation'
                        withSonarQubeEnv('SonarQubeServer')
                        {
                            sh "${scannerHome}/bin/sonar-scanner -Dsonar.projectKey=employee-mis"
                        }
                    }
                }
        }

        stage('Dependency Scan (Snyk)') {
            steps {
                sh '''
                    echo "Installing Python dependencies (forcing system install)..."
                    pip install --upgrade pip --break-system-packages
                    pip install -r requirements.txt --break-system-packages
                    '''

                snykSecurity(
                    snykInstallation: 'SnykSecurity',
                    snykTokenId: 'snyk-api-token',
                    targetFile: 'requirements.txt',
                    monitorProjectOnBuild: true,
                    failOnIssues: true
                )
            }
        }

        stage('Automated Testing (Unit & Integration)') {
            environment {
                DO_TOKEN = 'do-api-token'
                SSH_KEY = 'do-private-key'
            }
            
            steps {
                echo('Install Terraform tp provide VM to run tests ..')
                sh '''
                    #!/bin/bash
                    set -e

                    echo "Installing Terraform..."
                    # Set environment for non-root container                
                    TERRAFORM_VERSION="1.9.8"
                    export USER=jenkins
                    export HOME=/tmp
                    export PATH=\$HOME/.local/bin:\$PATH   

                    # Create a writable bin directory
                    mkdir -p \$HOME/.local/bin
                    cd $HOME

                    # Download Terraform binary
                    curl -fsSL https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip -o terraform.zip

                    # Unzip and move to /$HOME/local/bin
                    unzip -o terraform.zip                    
                    rm terraform.zip


                    # Clean up any existing directory named "terraform"
                    if [ -d "\$HOME/.local/bin/terraform" ]; then
                        echo "Removing old terraform directory..."
                        rm -rf \$HOME/.local/bin/terraform
                    fi

                    mv -f terraform \$HOME/.local/bin/

                    # Add to PATH (for current session)
                    export PATH=$HOME/.local/bin:$PATH

                    terraform -v
                    '''

                sh '''
                    pip install --upgrade pip --break-system-packages
                    pip install -r requirements.txt --break-system-packages
                    python3 -m pytest -v --maxfail=1 --disable-warnings
                    '''

                script {
                    dir('terraform') {
                        echo "Provision VM with Terraform..."
                        
                        sh '''
                            terraform init
                            terraform apply -auto-approve \
                            -var "do_token=$DO_TOKEN" \
                            -var "ssh_fingerprint=$SSH_KEY"
                        '''
                    }
                }
            }
        }

        stage('Build Docker Image (Docker)') {
            steps {
                script {
                    docker.build('employee-mis:latest')
                }
            }
        }

        stage('Container Security Scan (Trivy)') {
            agent {
                docker {
                    image 'aquasec/trivy:latest'
                    args '-v /var/run/docker.sock:/var/run/docker.sock --entrypoint=""'
                }
            }

            environment {
                TRIVY_CACHE_DIR = "${WORKSPACE}/.trivycache"
            }

            steps {
                sh '''
                    mkdir -p $TRIVY_CACHE_DIR
                    trivy --version
                    trivy image --severity HIGH,CRITICAL --exit-code 0 employee-mis:latest
                    '''
            }
        }

        stage('Docker Hub Actions') { 
            environment {
                DOCKER_IMAGE = 'employee-mis:latest'
                DOCKER_REGISTRY = 'docker.io/danetopot'
            }
            steps {
                echo('Login to Docker Hub ..')
                withCredentials([
                    usernamePassword(credentialsId: 'dockerhub-token', 
                    usernameVariable: 'DOCKER_USER', 
                    passwordVariable: 'DOCKER_TOKEN')]) 
                {
                    sh 'echo $DOCKER_TOKEN | docker login -u $DOCKER_USER --password-stdin'
                }

                echo('Build Docker Image..')
                sh "docker build -t danetopot/${DOCKER_IMAGE} ."

                echo('Tag and Push Docker Image..')
                sh "docker tag ${DOCKER_IMAGE} ${DOCKER_REGISTRY}/${DOCKER_IMAGE}"
                sh "docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE}"

                echo('Tag and Push Docker Image..')
                sh "docker logout ${DOCKER_REGISTRY}"               
            }
        }

        stage('Deployment to Kubernetes') {
            agent {
                docker { 
                    image 'bitnami/kubectl:latest' 
                    args '-v /var/run/docker.sock:/var/run/docker.sock --entrypoint=""'
                }                
            }
            environment {
                DOCKER_IMAGE = 'employee-mis:latest'
                DOCKER_REGISTRY = 'docker.io/danetopot'
            }            
            steps {
                echo 'Installing doctl and preparing kubeconfig...'
                withCredentials([string(credentialsId: 'do-api-token', variable: 'DO_API_TOKEN')]) {
                    sh """
                    # Set environment for non-root container
                    export USER=jenkins
                    export HOME=/tmp
                    export PATH=\$HOME/.local/bin:\$PATH

                    # Create a writable bin directory
                    mkdir -p \$HOME/.local/bin

                    # Download and extract doctl
                    curl -sL https://github.com/digitalocean/doctl/releases/download/v1.102.0/doctl-1.102.0-linux-amd64.tar.gz | tar -xzv
                    mv doctl \$HOME/.local/bin/

                    # Verify installation
                    doctl version

                    # Authenticate to DigitalOcean
                    doctl auth init -t $DO_API_TOKEN

                    # Save kubeconfig for your cluster
                    doctl kubernetes cluster kubeconfig save k8s-devseclab

                    # Set KUBECONFIG so kubectl can use it
                    export KUBECONFIG=\$HOME/.kube/config
                    kubectl config current-context

                    # Verify access to cluster
                    # kubectl get nodes
                    kubectl apply -f k8s/deployment.yaml
                    kubectl set image deployment/employee-app-deployment employee-app=docker.io/danetopot/employee-mis:latest
                    kubectl apply -f k8s/service.yaml
                    kubectl version --client
                    kubectl get svc
                    kubectl get nodes -o wide
                    kubectl get deployments
                    kubectl get pods -o wide
                    kubectl logs employee-app-deployment-6d676cc848-fb9v4
                    """
                }
            }
        }           

        stage('Dynamic Application Security Testing (OWASP ZAP)') {
            steps {
                echo('Skipping ....')
            }
        }

        stage('Post-deployment Security Scan (Port Scan/Vulnerability check) (Trivy)') {
            steps {
                echo('Skipping ...')
            }
        }
    }
}
