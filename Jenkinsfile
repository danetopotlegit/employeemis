pipeline {
    agent any
    stages {
        stage('Checkout') {
            steps { git 'https://github.com/your-org/employee-mgmt-app.git' }
        }
        stage('Static Code Analysis') {
            steps { sh 'sonar-scanner -Dsonar.projectKey=employee-app' }
        }
        stage('Dependency Scan') {
            steps { sh 'snyk test' }
        }
        stage('Build Docker Image') {
            steps { sh 'docker build -t employee-app .' }
        }
        stage('Container Scan') {
            steps { sh 'trivy image employee-app' }
        }
        stage('Unit Tests') {
            steps { sh 'pytest tests/' }
        }
        stage('DAST Scan') {
            steps { sh 'zap-cli quick-scan --self-contained http://localhost:5000' }
        }
        stage('Deploy to Kubernetes') {
            steps {
                sh 'kubectl apply -f k8s/deployment.yaml'
                sh 'kubectl apply -f k8s/service.yaml'
            }
        }
    }
}
