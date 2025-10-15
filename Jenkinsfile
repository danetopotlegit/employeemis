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
                    script{
                        def scannerHome = tool name: 'SonarScanner', type: 'hudson.plugins.sonar.SonarRunnerInstallation'
                         withSonarQubeEnv('SonarQubeServer') 
                         {
                            sh "${scannerHome}/bin/sonar-scanner -Dsonar.projectKey=employee-mis"
                         }
                    }
                }
        }
    }
}
