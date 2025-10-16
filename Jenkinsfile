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

        stage('Build Docker Image (Docker)') {
            steps {
                script {
                    docker.build("employee-mis:latest")
                }
            }
        }

        stage('Container Security Scan (Trivy)') {
            steps {
                 sh '''
                  curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh
                  sudo mv trivy /usr/local/bin/
                  trivy --version
                '''
            }
        }

        stage('Automated Testing (Unit & Integration)') {
            steps {
                echo("Skipping ...")
            }
        }

        stage('Dynamic Application Security Testing (OWASP ZAP)') {
            steps {
                echo("Skipping ...")
            }
        }

        stage('Deployment (to Kubernetes or Docker host)') {
            steps {
                echo("Skipping ...")
            }
        }

        stage('Post-deployment Security Scan (Port Scan/Vulnerability check) (Trivy)') {
            steps {
                echo("Skipping ...")
            }
        }
    }
}
