/* groovylint-disable LineLength */
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

         stage('Dependency Scan') {
            steps {
                withCredentials([string(credentialsId: 'snyk-api-token', variable: 'snyk-api-token')]) {
                    sh 'snyk auth $snyk-api-token'
                    sh 'snyk test'
                }
            }
        }
    }
}
