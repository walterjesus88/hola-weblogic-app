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
    CONTAINER = "my-weblogic-${params.ENV}"
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
          docker exec ${CONTAINER} mkdir -p ${CONTAINER_APPS}
          docker cp target/*.war my-weblogic:${CONTAINER_APPS}/${WAR_NAME}
        """
      }
    }

    stage('Copy WLST scripts to container') {
      steps {
        sh """
          docker exec ${CONTAINER} mkdir -p ${WLST_DIR}
          docker cp wlst/. ${CONTAINER}:${WLST_DIR}/
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
            docker exec ${CONTAINER} \
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
        failure {
            echo '❌ Deploy falló. Rollback aplicado automáticamente.'
        }
        success {
            script {
                def url = ''
                if (params.ENV == 'dev') {
                    url = 'http://localhost:7001/hola'
                } else if (params.ENV == 'qa') {
                    url = 'http://localhost:7002/hola'
                } else if (params.ENV == 'prod') {
                    url = 'http://localhost:7003/hola'
                }
                echo "✅ Deploy exitoso en ${params.ENV}"
                echo "🌐 Accede a: ${url}"
            }
        }
    }
}
