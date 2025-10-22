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
            steps {
                echo('Install Terraform to provide VM to run tests ..')
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
                /*
                sh '''
                    pip install --upgrade pip --break-system-packages
                    pip install -r requirements.txt --break-system-packages
                    python3 -m pytest -v --maxfail=1 --disable-warnings
                    '''*/
            }
        }

       
        stage('Provision VM with Terraform') {
            agent {
                docker {
                    image 'hashicorp/terraform:1.9.8'
                    args '-u root -v /var/run/docker.sock:/var/run/docker.sock --entrypoint=""' 
                }
            }
            environment {
                DO_TOKEN = credentials('do-api-token')
                SSH_KEY = credentials('do-ssh-key')
            }          
            
            steps {

                    /*
                    sh '''
                        #!/bin/bash
                        set -x
                        echo "Checking environment variables..."
                        echo "DO_TOKEN prefix: $(echo "$DO_TOKEN" | cut -c1-20)"
                        echo "SSH_KEY prefix: $(echo "$SSH_KEY" | cut -c1-20)"
                        '''
                    
                    dir('terraform') {
                        sh """
                        #!/bin/bash
                        set -x
                        #export HOME=/tmp
                        #export PATH=\$HOME/.local/bin:\$PATH   
                        terraform init
                        terraform plan \
                            -var "do-api-token=${DO_TOKEN}" \
                            -var "ssh_fingerprint=${SSH_KEY}"
                        terraform apply -auto-approve \
                            -var "do-api-token=${DO_TOKEN}" \
                            -var "ssh_fingerprint=${SSH_KEY}"
                        terraform output \
                            -raw vm_ip > vm_ip.txt   
                        """
                    }*/

                    script{
                        env.VM_IP = '164.90.231.217'
                        /*
                        env.VM_IP = sh(
                            script: 'cd terraform && terraform output -raw vm_ip',
                            returnStdout: true
                        ).trim()
                        */
                    }

                    sshagent(['test-vm-ssh-key']) {
                        sh """
                        echo "Current user inside container: \$(whoami)"
                        echo "Copying files to ${env.VM_IP}:/root/project..."
                        scp -o StrictHostKeyChecking=no -r * root@${env.VM_IP}:/root/project
                        """
                    }

                    /*
                    sshagent (credentials: ['test-vm-ssh-key']){
                        sh """
                            echo "Connecting to VM at: ${env.VM_IP}"
                            scp -o StrictHostKeyChecking=no -r * root@${env.VM_IP}:/root/project
                            ssh -o StrictHostKeyChecking=no root@${env.VM_IP}' 
                            apt update -y
                            apt install -y python3 python3-pip python3-venv
                            python3 -m venv /root/project/venv
                            source /root/project/venv/bin/activate
                            python3 -m pip install --upgrade pip
                            python3 -m pip install -r /root/project/requirements.txt
                            python3 -m pytest -v /root/project --maxfail=1 --disable-warnings
                            EOF
                            """
                    }*/
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

                    doctl compute ssh-key list

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

        stage('Monitoring & Observability') {
            agent {
                docker { 
                    image 'bitnami/kubectl:latest' 
                    args '-v /var/run/docker.sock:/var/run/docker.sock --entrypoint=""'
                }                
            }
            steps {
                    echo 'Install Prometheus & Grafana...'
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

                        doctl compute ssh-key list

                        # Save kubeconfig for your cluster
                        doctl kubernetes cluster kubeconfig save k8s-devseclab

                        # Set KUBECONFIG so kubectl can use it
                        export KUBECONFIG=\$HOME/.kube/config
                        kubectl config current-context

                        # Verify access to cluster
                        # kubectl get nodes
                        kubectl apply -f k8s/prometheus-deployment.yaml
                        kubectl apply -f k8s/grafana-deployment.yaml
                        kubectl version --client
                        kubectl get svc
                        kubectl get nodes -o wide
                        kubectl get deployments
                        kubectl get pods -o wide
                        kubectl get namespaces -o wide
                        kubectl get svc --all-namespaces -o wide | grep prometheus

                        kubectl logs prometheus-deployment-78f4bdd6bd-2rxhq

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
