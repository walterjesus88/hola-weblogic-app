pipeline {
  agent any

  parameters {
    choice(
      name: 'ENV',
      choices: ['dev', 'qa', 'prod'],
      description: 'Ambiente de despliegue'
    )
  }

  environment {
    APP_NAME = 'hola'
    SHARED_DIR = "/shared/apps/${params.ENV}"
    CONTAINER_DIR = "/u01/oracle/apps/${params.ENV}"
  }

  stages {

    stage('Build WAR') {
      steps {
        sh '''
          mvn clean package
        '''
      }
    }

   stage('Copy WAR to WebLogic container') {
    steps {
      sh '''
        docker exec my-weblogic mkdir -p /u01/oracle/apps/${ENV}
        docker cp target/*.war my-weblogic:/u01/oracle/apps/${ENV}/hola.war
      '''
    }
  }

        
    stage('Copy WLST scripts to container') {
      steps {
        sh '''
          docker exec my-weblogic mkdir -p /u01/oracle/wlst
          docker cp wlst/. my-weblogic:/u01/oracle/wlst/
        '''
      }
    }


    stage('Deploy to WebLogic') {
      steps {
        withCredentials([usernamePassword(
          credentialsId: 'weblogic-creds',
          usernameVariable: 'WLS_USER',
          passwordVariable: 'WLS_PASS'
        )]) {

          sh """
          docker exec my-weblogic \
          /u01/oracle/oracle_common/common/bin/wlst.sh \
          /u01/oracle/wlst/deploy_app.py \
          ${params.ENV} \
          $WLS_USER \
          $WLS_PASS \
          ${CONTAINER_DIR}/${APP_NAME}.war \
          ${APP_NAME}
          """
        }
      }
    }
  }
}
