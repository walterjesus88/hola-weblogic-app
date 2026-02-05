pipeline { 
  agent any
  stages {
    stage('Build') {
      steps {
         sh '''
          mvn clean package
          cp target/*.war /shared/apps/hola.war
        '''
      }
    }
  }
}
