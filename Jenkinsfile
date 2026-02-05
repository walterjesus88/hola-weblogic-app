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

    stage('Deploy to WebLogic') {
      steps {
        sh '''
          docker exec my-weblogic \
          /u01/oracle/oracle_common/common/bin/wlst.sh \
          /u01/oracle/wlst/deploy_app.py \
          hola /u01/oracle/apps/hola.war AdminServer
        '''
      }
    }
  }
}
