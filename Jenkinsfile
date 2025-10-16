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
                sh '''
                    pip install --upgrade pip --break-system-packages
                    pip install -r requirements.txt --break-system-packages
                    python3 -m pytest -v --maxfail=1 --disable-warnings
                    '''
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
            steps {
                echo 'Deploying to Kubernetes cluster...'

                withCredentials([string(credentialsId: 'do-api-token', variable: 'DO_API_TOKEN')]) {
                    sh """
                    doctl auth init -t $DO_API_TOKEN
                    doctl kubernetes cluster kubeconfig save do-fra1-k8s-devseclab
                    export KUBECONFIG=$HOME/.kube/config
                    kubectl set image deployment/employee-mis employee-mis=${DOCKER_REGISTRY}/${DOCKER_IMAGE}
                    kubectl rollout status deployment/employee-mis
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
