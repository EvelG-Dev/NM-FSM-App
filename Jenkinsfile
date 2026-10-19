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
    // ── Stage 1: Checkout ──────────────────────────────────────────────
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
    // ── Stage 2: Rebuild Golden AMI only when image contents change─────────────
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
          # Preserve the build record outside the workspace — cleanWs() wipes it
          cp -f ami_manifest.json /home/ec2-user/NM-FSM-App/devops-course/ami_manifest.json
        '''
        archiveArtifacts artifacts: 'devops-course/ami_manifest.json', allowEmptyArchive: true
      }
    }

 // ── Stage 3: Build and push Docker image ──────────────────────────────
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
          # Immutable tag — this is what the pipeline deploys
          docker tag  ${REPO_NAME}:${IMAGE_TAG} ${REPO_URL}:${IMAGE_TAG}
          docker push ${REPO_URL}:${IMAGE_TAG}
          # Moving tag — keeps :latest current for a manual terraform apply
          docker tag  ${REPO_NAME}:${IMAGE_TAG} ${REPO_URL}:latest
          docker push ${REPO_URL}:latest
        '''
      }
    }
 // ── Stage 4: Terraform Plan ─────────────────────────────────────────────
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
   // ── Stage 5: Manual approval before infrastructure change ───────────────
    stage('Approval') {
      steps {
        input message: 'Review Terraform plan. Proceed with apply?',
              ok: 'Apply', submitter: 'admin'
      }
    }

    // ── Stage 6: Terraform Apply ────────────────────────────────────────────
    stage('Terraform Apply') {
      steps {
        sh 'cd /home/ec2-user/NM-FSM-App/devops-course/terraform && terraform workspace select staging && terraform apply -auto-approve tfplan.bin'
      }
    }
   // ── Stage 7: Manual gate then promote to production workspace ──────────────────────────────
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

