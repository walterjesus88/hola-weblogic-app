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
    APP_BASE = 'hola'
    CONTAINER_APPS = "/u01/oracle/apps/${params.ENV}"
    WLST_DIR = "/u01/oracle/wlst"
    VERSION = "${BUILD_NUMBER}"
    APP_VERSIONED = "${APP_BASE}-${params.ENV}-${VERSION}"
    WAR_NAME = "${APP_VERSIONED}.war"
  }

  stages {

    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Build WAR') {
      steps {
        sh '''
          mvn clean package
        '''
      }
    }

    stage('Copy WAR to WebLogic container') {
      steps {
        sh """
          docker exec my-weblogic mkdir -p ${CONTAINER_APPS}
          docker cp target/*.war my-weblogic:${CONTAINER_APPS}/${WAR_NAME}
        """
      }
    }

    stage('Copy WLST scripts to container') {
      steps {
        sh """
          docker exec my-weblogic mkdir -p ${WLST_DIR}
          docker cp wlst/. my-weblogic:${WLST_DIR}/
        """
      }
    }

    stage('Deploy Blue/Green with Rollback') {
      steps {
        withCredentials([usernamePassword(
          credentialsId: 'weblogic-creds',
          usernameVariable: 'WLS_USER',
          passwordVariable: 'WLS_PASS'
        )]) {

          sh """
            docker exec my-weblogic \
            /u01/oracle/oracle_common/common/bin/wlst.sh \
            ${WLST_DIR}/deploy_with_rollback2.py \
            ${params.ENV} \
            ${WLS_USER} \
            ${WLS_PASS} \
            ${APP_BASE} \
            ${VERSION} \
            ${CONTAINER_APPS}/${WAR_NAME} 
          """
        }
      }
    }
  }

  post {
    success {
      echo "✅ Deploy exitoso en ${params.ENV}"
    }
    failure {
      echo "❌ Deploy falló. Rollback aplicado automáticamente."
    }
  }
}
