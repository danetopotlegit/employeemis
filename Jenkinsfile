/* groovylint-disable LineLength */
pipeline {
    agent any

    stages {
        stage('Code Checkout') {
            steps {
                git(
                    url: 'https://github.com/danetopotlegit/employeemis.git' ,
                    branch: 'main',
                    credentialsId: 'github-token'
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

        stage('Debug Workspace') {
        steps {
            sh 'pwd'
            sh 'ls -la'
            sh 'ls -la requirements.txt || echo "File not found here"'
        }
        }

        stage('Dependency Scan') {
            steps {
                snykSecurity(
                    snykInstallation: 'SnykSecurity',
                    snykTokenId: 'snyk-api-token',
                    targetFile: 'requirements.txt',
                    monitorProjectOnBuild: true,
                    failOnIssues: true
                )
            }
        }
    }
}
