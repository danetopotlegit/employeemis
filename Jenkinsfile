pipeline {
    agent any
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
            steps { sh 'sonar-scanner -Dsonar.projectKey=employee-app' }
        }
    }
}
