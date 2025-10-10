pipeline {
    agent any
    stages {
        stage('Checkout') 
        {
            steps { 
                git (
                    'https://github.com/danetopotlegit/employeemis.git' ,
                    branch: 'main',
                    credentialsId: 'GitHubAccessTokenId'
                    )
        }
    }
}
