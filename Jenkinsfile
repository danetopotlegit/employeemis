/* groovylint-disable LineLength */
pipeline {
    agent any

    stages {
        stage('Code Checkout') {
            steps {
                git(
                    url: 'https://github.com/danetopotlegit/employeemis.git' ,
                    branch: 'master',
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

        stage('Dependency Scan') {
            steps {
                echo("Skipping dependency scan  for now ...")
                /*snykSecurity(
                    snykInstallation: 'SnykSecurity',
                    snykTokenId: 'snyk-api-token',
                    targetFile: 'requirements.txt',
                    monitorProjectOnBuild: true,
                    failOnIssues: true
                )*/
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("employee-mis:latest")
                }
            }
        }
    }
}
