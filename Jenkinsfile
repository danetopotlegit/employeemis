pipeline {
    agent any

    tools {
        sonarQubeScanner 'SonarScanner'
    }

    environment {
        SONARQUBE_ENV = 'SonarQubeServer'
    }

    stages {
        stage('Code Checkout') {
            steps {
                git(
                    url: 'https://github.com/danetopotlegit/employeemis.git' ,
                    branch: 'main',
                    credentialsId: 'GitHubAccessTokenId'
                    )
            }
        }

        stage('Static Code Analysis') {
            steps { sh 'SonarQubeServer -Dsonar.projectKey=employee-app' }
        }
    }
}
