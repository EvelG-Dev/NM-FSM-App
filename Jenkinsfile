pipeline {
  agent any
  triggers { pollSCM('* * * * *') }
  environment {
    AWS_REGION     = 'us-east-1'
    REPO_NAME      = 'nm-fsm-app'
    PYTHONPATH     = "${WORKSPACE}"
    ANSIBLE_VAULT_PASSWORD_FILE = '/var/lib/jenkins/.ansible_vault_pass'  // Created by professor script and understood by Ansible
  }
  options {
    buildDiscarder(logRotator(numToKeepStr: '10'))
    timestamps(); ansiColor('xterm')
  }
  stages {
    stage('Checkout') {
      steps {
        checkout scm
        sh 'git log -1 --oneline'
        script {
          env.IMAGE_TAG = sh(script: 'git rev-parse --short HEAD',
                             returnStdout: true).trim()
          echo "Image tag for this build: ${env.IMAGE_TAG}"
        }
      }
    }

    stage('Unit & HTTP Tests') {
      steps {
        sh 'PYTHONPATH=$WORKSPACE pytest tests/unit/ tests/http/ -v'
      }
    }
    stage('IaC Scan with Checkov') {
      steps {
        sh '''
          checkov -d "$WORKSPACE/devops-course/terraform" --quiet --compact --framework terraform \
            --skip-check CKV_AWS_126,CKV_AWS_135,CKV_AWS_79,CKV_AWS_8,CKV_AWS_3,CKV_AWS_189,CKV2_AWS_2,CKV_AWS_163,CKV_AWS_51,CKV_AWS_136,CKV_AWS_333,CKV_AWS_158,CKV_AWS_338,CKV_AWS_23,CKV_AWS_382,CKV_AWS_65,CKV_AWS_272,CKV_AWS_116,CKV_AWS_115,CKV_AWS_117,CKV_AWS_50 \
            -o json > checkov-report.json
        '''
      }
      post {
        always { archiveArtifacts artifacts: 'checkov-report.json', allowEmptyArchive: true }
      }
    }
    stage('Packer Build') {
      when {
        anyOf {
          changeset "devops-course/roles/**"
          changeset "devops-course/group_vars/**"
          changeset "devops-course/site.yml"
          changeset "devops-course/vault.yml"
          changeset "devops-course/mysql-ami.pkr.hcl"
        }
      }
      steps {
        sh '''
          set -e
          cd "$WORKSPACE/devops-course"
          packer init .
          packer validate .
          packer build mysql-ami.pkr.hcl
          # Preserve the build record outside the workspace â€” cleanWs() wipes it
          cp -f ami_manifest.json /home/ec2-user/NM-FSM-App/devops-course/ami_manifest.json
        '''
        archiveArtifacts artifacts: 'devops-course/ami_manifest.json', allowEmptyArchive: true
      }
    }

  stage('Docker Build & Push') {
      steps {
        sh '''
          set -e
          : "${IMAGE_TAG:?IMAGE_TAG not set - run a full pipeline build}"
          TF=/home/ec2-user/NM-FSM-App/devops-course/terraform
          REPO_URL=$(TF_WORKSPACE=staging terraform -chdir=$TF output -raw ecr_repository_url)
          REGISTRY=${REPO_URL%/*}
          aws ecr get-login-password --region ${AWS_REGION} | \
            docker login --username AWS --password-stdin ${REGISTRY}
          docker build -t ${REPO_NAME}:${IMAGE_TAG} .
          # Immutable tag â€” this is what the pipeline deploys
          docker tag  ${REPO_NAME}:${IMAGE_TAG} ${REPO_URL}:${IMAGE_TAG}
          docker push ${REPO_URL}:${IMAGE_TAG}
          # Moving tag â€” keeps :latest current for a manual terraform apply
          docker tag  ${REPO_NAME}:${IMAGE_TAG} ${REPO_URL}:latest
          docker push ${REPO_URL}:latest
        '''
      }
    }

    stage('Terraform Test') {
      steps {
        sh '''
          set -e
          SRC="$WORKSPACE/devops-course/terraform"
          DST=/home/ec2-user/NM-FSM-App/devops-course/terraform
          cp -f "$SRC"/*.tf "$SRC/terraform.tfvars" "$DST/"
          mkdir -p "$DST/tests"
          cp -f "$SRC"/tests/*.tftest.hcl "$DST/tests/"
          cd "$DST"
          terraform init -input=false
          TF_WORKSPACE=staging terraform test
        '''
      }
    }
 stage('Terraform Plan') {
      steps {
        sh '''
          set -e
          SRC=$WORKSPACE/devops-course/terraform
          DST=/home/ec2-user/NM-FSM-App/devops-course/terraform
          cp -f $SRC/*.tf $SRC/terraform.tfvars $DST/
          cd $DST
          terraform init
          terraform workspace select staging
          terraform plan -var="flask_image_tag=$IMAGE_TAG" -out=tfplan.bin
          terraform show -no-color tfplan.bin | tee tfplan.txt
          cp tfplan.txt $WORKSPACE/tfplan.txt
        '''
        archiveArtifacts artifacts: 'tfplan.txt'
      }
    }
    stage('Approval') {
      steps {
        input message: 'Review Terraform plan. Proceed with apply?',
              ok: 'Apply', submitter: 'admin'
      }
    }

    stage('Terraform Apply') {
      steps {
        sh 'cd /home/ec2-user/NM-FSM-App/devops-course/terraform && terraform workspace select staging && terraform apply -auto-approve tfplan.bin'
      }
    }

    stage('Integration Tests') {
      steps {
        withCredentials([string(credentialsId: 'db-password', variable: 'DB_PASS')]) {
          sh '''
            set +x
            set -e
            TF=/home/ec2-user/NM-FSM-App/devops-course/terraform
            DB_IP=$(TF_WORKSPACE=staging terraform -chdir="$TF" output -raw db_private_ip)
            export DATABASE_URL="mysql+pymysql://flaskapp:${DB_PASS}@${DB_IP}/fsm_db"
            pytest tests/integration/ -v
          '''
        }
      }
    }
    stage('E2E Tests') {
      steps {
        sh '''
          set -e
          aws ecs wait services-stable --cluster cis4641-cluster --services flask-staging
          TASK_ARN=$(aws ecs list-tasks --cluster cis4641-cluster --service-name flask-staging --desired-status RUNNING --query 'taskArns[0]' --output text)
          STAGING_IP=$(aws ecs describe-tasks --cluster cis4641-cluster --tasks "$TASK_ARN" --query 'tasks[0].attachments[0].details[?name==`privateIPv4Address`].value' --output text)
          test -n "$STAGING_IP"
          test "$STAGING_IP" != None
          export STAGING_URL="http://${STAGING_IP}:5000"
          for i in $(seq 1 12); do
            curl -sf "$STAGING_URL/" > /dev/null && break
            sleep 5
          done
          curl -sf "$STAGING_URL/" > /dev/null
          pytest tests/e2e/ -v --tb=short
        '''
      }
    }
   stage('Promote to Production') {
      steps {
        input message: 'Staging verified. Promote to production?',
              ok: 'Promote', submitter: 'admin'
        sh '''
          set -e
          cd /home/ec2-user/NM-FSM-App/devops-course/terraform
          terraform workspace select production
          terraform apply -auto-approve -var="flask_image_tag=$IMAGE_TAG"
        '''
      }
    }
  } // end stages

  post {
    success { echo 'Deployment to staging and production complete.' }
    failure { echo 'Pipeline FAILED. Check logs above.' }
    always  { cleanWs() }
  }
}
