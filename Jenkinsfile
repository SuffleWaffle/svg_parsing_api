def gitCredentialsId = "github-creds"
def gitRepoUrl = 'git@github.com:Drawer-Inc/svg_parsing_service.git'
def pom = ''

def build_service = '''
        ls -al
        chmod +x ./build_service.sh
        ./build_service.sh
    '''
def build_update_version = '''
        chmod +x ./build_update_version.sh
        ./build_update_version.sh
    '''
def sonar_link_slack = '''https://sonarqube.tools.private.drawer-apps.net/dashboard?id=svg_parsing_service'''

properties(
 [
   parameters(
     [
       [
         $class           : 'GitParameterDefinition',
         branch           : '',
         branchFilter     : '.*',
         defaultValue     : '${env.BRANCH_NAME}',
         description      : 'Branch or Tag',
         name             : 'BRANCH',
         quickFilterEnabled: false,
         selectedValue    : 'DEFAULT',
         sortMode         : 'ASCENDING_SMART',
         tagFilter        : '*',
         type             : 'PT_BRANCH'
       ]
     ]
   ),

    pipelineTriggers([
      [
      $class: 'GenericTrigger',
      genericVariables: [
        [
          key: 'BRANCH',
          value: '$.ref',
          expressionType: 'JSONPath'
        ],
              
      ],
        causeString: 'Triggered by Github',
        token: '2JgXvhUHgteEIsyduprChHXj4mRPe9TmLYAWmv9eJyEshPX2rpROOde1GDOQRrk7',
        printContributedVariables: true,
        printPostContent: true,
        silentResponse: false,
        regexpFilterText: '$BRANCH',
//         regexpFilterExpression:  '^(refs/heads/feat/.+)$'
        regexpFilterExpression:  '^(refs/heads/stage-ci|refs/heads/main|refs/heads/stage-eks-ci|refs/heads/dev-deploy|refs/heads/feat/.+)$'
      ]
      ])

  ]
)


pipeline {
  environment {
    SERVICE_NAME = 'svg_parsing_service'
    AWS_REGION = 'us-east-1'
    AWS_ACCOUNT = '064427434392'
    SLACK_DOMAIN = 'drawerai'
    SLACK_CHANNEL = "#ci-cd-ai"
    SLACK_TOKEN = credentials("slack-token")
    PROD_PASSWORD   = credentials("ai-prod-password")
    STAGE_PASSWORD  = credentials("ai-stage-password")
  }

  agent any

  options {
    buildDiscarder(logRotator(numToKeepStr: '20'))
    ansiColor('xterm')
    timestamps()
  }

 
  stages {

    stage('Prepare') {
      steps {
        script {
          currentBuild.displayName = "#${env.BUILD_NUMBER}-${env.BRANCH}"
        }
      }
    }

    stage('Checkout') {
      steps {
        checkout(
          [
            $class           : 'GitSCM',
            branches         : [[name: "${BRANCH}"]],
            userRemoteConfigs: [[url: "${gitRepoUrl}", credentialsId: "${gitCredentialsId}"]],
          ]
        )
      }
    }

    /*SONAR STAGE*/
  stage('SonarQube analysis') {
        steps {
            script{
            def scmVars = checkout([$class: 'GitSCM', branches: [[name:  "${BRANCH}"]], 
              userRemoteConfigs: [[url: "${gitRepoUrl}", credentialsId: "${gitCredentialsId}"]],])
              env.REPOGIT_COMMIT = scmVars.GIT_COMMIT //переприсвоюємо номер коміту (поки не ясно навіщо)
         
            sh "echo ${env.BRANCH}" //перевіряємо поточну гілку
            def scmBranch = "-Dsonar.branch.name=${env.BRANCH}" //задаємо поточну гілку
            def scmRevision = "-Dsonar.scm.revision=${env.REPOGIT_COMMIT}" //задаємо поточний коміт
            def scannerHome = tool 'sonarscan'; //задаємо поточну тулзу - сонаркуб
              withSonarQubeEnv('sonarqube') {
                sh "cd ${WORKSPACE} && ${tool("sonarscan")}/bin/sonar-scanner ${scmBranch} ${scmRevision}"
								//запускаємо сам аналіз використовуючи змінні сонару
              }
            }
        }
    }

  /*SONAR STAGE*/

  /**/
  stage("Quality gate") {
      steps {
        script {
          sh "echo Passing quality gate..."
          def qualitygate = waitForQualityGate() 
          sleep(10) 
          if (qualitygate.status != "OK") { 
            slackSend(
            color: 'danger',
            channel: SLACK_CHANNEL,
            message: "*${env.JOB_NAME}* - <${env.RUN_DISPLAY_URL}|#${env.BUILD_NUMBER}> " +
              "\n:warning: *WARNING* :warning: Quality gate not passed! " +
              "\nTo check details please refer to dashboard <${sonar_link_slack}|link> " +
              "\n*Additional info:*" +
              "\nRepository: *${gitRepoUrl}*" +
              "\nCommit Hash: *${env.GIT_COMMIT}*",
            teamDomain: SLACK_DOMAIN,
            token: SLACK_TOKEN
            )
            //waitForQualityGate abortPipeline: true //абортає пайплайн
          }
        }
      }
    }
  /**/
  
    stage ('Docker Build') {
      steps{
        script { sh build_service }
      }
    }

  
  stage ('Prepare deploy') {
    stages{
      stage('Deploy dev'){
        when {
          anyOf {
            expression {env.BRANCH =~ /^refs\/heads\/dev-deploy$/}
            expression {env.BRANCH =~ /^refs\/tags\/dev-.+$/}
            expression {env.BRANCH =~ /^origin\/dev-deploy/}
            expression {env.BRANCH =~ /^origin\/dev-tests/}
          }
        }
        steps {
          script {
            sshagent(['ai-dev-creds']) {
              sh """
                scp -o StrictHostKeyChecking=no -P 9376 deploy_service.sh administrator@66.117.7.18:/home/administrator/dev/jenkins/svg_parsing_service
                ssh -o StrictHostKeyChecking=no -l administrator 66.117.7.18  -p 9376  chmod +x /home/administrator/dev/jenkins/svg_parsing_service/deploy_service.sh
                ssh -o StrictHostKeyChecking=no -l administrator 66.117.7.18  -p 9376  "cd dev/jenkins/svg_parsing_service && ./deploy_service.sh ${env.image_tag}"
              """
            }
          }
        }  
      }
      stage('Deploy stage'){
        when {
          anyOf {
            expression {env.BRANCH =~ /^refs\/heads\/stage-ci$/}
            expression {env.BRANCH =~ /^refs\/heads\/stage-eks-ci$/}
            expression {env.BRANCH =~ /^refs\/tags\/stage-.+$/}
            expression {env.BRANCH =~ /^origin\/stage-ci$/}
            expression {env.BRANCH =~ /^origin\/stage-eks-ci$/}   
          }
        }
        parallel{
          stage('Deploy on-prem'){
            when{anyOf{
              expression {env.BRANCH =~ /^refs\/heads\/stage-ci$/}
              expression {env.BRANCH =~ /^origin\/stage-ci$/}
            }}
            steps {
              script {
                echo "Skipping!"
                // sh """
                //   sshpass -p $STAGE_PASSWORD scp -o StrictHostKeyChecking=no -P 9376 deploy_service.sh administrator@205.134.224.136:/home/administrator/stg/jenkins/svg_parsing_service
                //   sshpass -p $STAGE_PASSWORD ssh -o StrictHostKeyChecking=no administrator@205.134.224.136 -p 9376 "sed -i 's/BRANCH_NAME=\\"dev-deploy\\"/BRANCH_NAME=\\"stage-ci\\"/g' /home/administrator/stg/jenkins/svg_parsing_service/deploy_service.sh"
                //   sshpass -p $STAGE_PASSWORD ssh -o StrictHostKeyChecking=no administrator@205.134.224.136 -p 9376 "sed -i 's/ENV_NAME=\\"dev\\"/ENV_NAME=\\"stage\\"/g' /home/administrator/stg/jenkins/svg_parsing_service/deploy_service.sh"
                //   sshpass -p $STAGE_PASSWORD ssh -o StrictHostKeyChecking=no administrator@205.134.224.136 -p 9376 chmod +x /home/administrator/stg/jenkins/svg_parsing_service/deploy_service.sh 
                //   sshpass -p $STAGE_PASSWORD ssh -o StrictHostKeyChecking=no administrator@205.134.224.136 -p 9376 "cd stg/jenkins/svg_parsing_service && ./deploy_service.sh ${env.image_tag}"
                // """
              }
            }
          }
          stage('Deploy on EKS'){
            when{anyOf{
              expression {env.BRANCH =~ /^refs\/heads\/stage-ci$/}
              expression {env.BRANCH =~ /^origin\/stage-ci$/}
            }}
            stages {  
              stage('Checkout helm repo') {
                steps {
                  checkout(
                    [
                      $class           : 'GitSCM',
                      branches         : [[name: 'main']],
                      extensions       : [[$class: 'RelativeTargetDirectory',
                      relativeTargetDir: 'helm']],
                      userRemoteConfigs: [[url: 'git@github.com:Drawer-Inc/helm.git', credentialsId: "${gitCredentialsId}"]],
                    ]
                  )
                }
              }
              stage ('Update version') {
                steps{script { sh build_update_version }}
              }
              stage('Push version') {
                steps {
                    sshagent (credentials: ["${gitCredentialsId}"]) {
                    sh """
                      cd ${WORKSPACE}/helm
                      git config user.email "jenkins@drawer.ai"
                      git config user.name "Jenkins CI"
                      git checkout main
                      git add drawerai-services/drawerai-dev-values.yaml
                      git commit -am "Job updated version."
                      git push origin main
                    """
                  }
                }
              }
            }
          }  
        }  
      }
      stage('Deploy prod'){
        when {
          anyOf {
            expression {env.BRANCH =~ /^refs\/heads\/main$/}
            expression {env.BRANCH =~ /^refs\/tags\/prod-.+$/}
            expression {env.BRANCH =~ /^origin\/main$/}
          }
        }
        steps {
          slackSend(
            color: 'warning',
            channel: SLACK_CHANNEL,
            message: "*${env.JOB_NAME}* - <${env.RUN_DISPLAY_URL}|#${env.BUILD_NUMBER}> " +
              "\n:warning: *WARNING* :warning: it seems to be deploying on PROD environment! " +
              "\nPlease, approve this step in Jenkins via <${env.JOB_URL}|link> " +
              "\n*Additional info:*" +
              "\nRepository: *${gitRepoUrl}*" +
              "\nCommit Hash: *${env.GIT_COMMIT}*",
            teamDomain: SLACK_DOMAIN,
            token: SLACK_TOKEN
          )
          timeout(time: 10, unit: "MINUTES") {
            input message: 'Do you want to approve this deployment on prod?', ok: 'Approve'
          }
          slackSend(
            color: 'good',
            channel: SLACK_CHANNEL,
            message: "Job *${env.JOB_NAME}* (<${env.RUN_DISPLAY_URL}|#${env.BUILD_NUMBER}>) is *approved* to deploy on PROD" +
            "\n:thumbsup:",
            teamDomain: SLACK_DOMAIN,
            token: SLACK_TOKEN
          )
          script {
            sh """
              sshpass -p $PROD_PASSWORD scp -o StrictHostKeyChecking=no -P 9376 deploy_service.sh administrator@38.17.49.2:/home/administrator/prod/jenkins/svg_parsing_service
              sshpass -p $PROD_PASSWORD ssh -o StrictHostKeyChecking=no administrator@38.17.49.2 -p 9376 "sed -i 's/BRANCH_NAME=\\"dev-deploy\\"/BRANCH_NAME=\\"main\\"/g' /home/administrator/prod/jenkins/svg_parsing_service/deploy_service.sh"
              sshpass -p $PROD_PASSWORD ssh -o StrictHostKeyChecking=no administrator@38.17.49.2 -p 9376 "sed -i 's/ENV_NAME=\\"dev\\"/ENV_NAME=\\"prod\\"/g' /home/administrator/prod/jenkins/svg_parsing_service/deploy_service.sh"
              sshpass -p $PROD_PASSWORD ssh -o StrictHostKeyChecking=no administrator@38.17.49.2 -p 9376 chmod +x /home/administrator/prod/jenkins/svg_parsing_service/deploy_service.sh 
              sshpass -p $PROD_PASSWORD ssh -o StrictHostKeyChecking=no administrator@38.17.49.2 -p 9376 "cd prod/jenkins/svg_parsing_service && ./deploy_service.sh ${env.image_tag}"
            """
          }
        }  
      }
    } 
  }
}




  
//test
    post {
    always {
      junit allowEmptyResults: true, testResults: '**/*Test.xml'
      cleanWs()
    }

    aborted {
      wrap([$class: 'BuildUser']) {
        slackSend(
          color: '#808080',
          channel: SLACK_CHANNEL,
          message: "*${env.JOB_NAME}* - <${env.RUN_DISPLAY_URL}|#${env.BUILD_NUMBER}> " +
            "Aborted after ${currentBuild.durationString.replaceAll(' and counting', '')}" +
            "\nRepository: *${gitRepoUrl}*" +
            "\nBranch: *${BRANCH}*" +
            "\nCommit Hash: *${env.GIT_COMMIT}*" +
            // "\nLaunched by: *${env.BUILD_USER}*" +
            "\n:octagonal_sign:",
          teamDomain: SLACK_DOMAIN,
          token: SLACK_TOKEN
        )
      }
    }

    failure {
      wrap([$class: 'BuildUser']) {
        slackSend(
          color: 'danger',
          channel: SLACK_CHANNEL,
          message: "*${env.JOB_NAME}* - <${env.RUN_DISPLAY_URL}|#${env.BUILD_NUMBER}> " +
            "Failed after ${currentBuild.durationString.replaceAll(' and counting', '')}" +
            "\nRepository: *${gitRepoUrl}*" +
            "\nBranch: *${env.GIT_BRANCH}*" +
            "\nCommit Hash: *${env.GIT_COMMIT}*" +
            // "\nLaunched by: *${env.BUILD_USER}*" +
            "\n:poop:",
          teamDomain: SLACK_DOMAIN,
          token: SLACK_TOKEN
        )
      }
    }

    success {
      wrap([$class: 'BuildUser']) {
        slackSend(
          color: 'good',
          channel: SLACK_CHANNEL,
          message: "*${env.JOB_NAME}* - <${env.RUN_DISPLAY_URL}|#${env.BUILD_NUMBER}> " +
            "Success after ${currentBuild.durationString.replaceAll(' and counting', '')}" +
            "\nRepository: *${gitRepoUrl}*" +
            "\nBranch: *${env.GIT_BRANCH}*" +
            "\nCommit Hash: *${env.GIT_COMMIT}*" +
            // "\nLaunched by: *${env.BUILD_USER}*" +
            "\n:tada:",
          teamDomain: SLACK_DOMAIN,
          token: SLACK_TOKEN
        )
      }
    }
  }

}