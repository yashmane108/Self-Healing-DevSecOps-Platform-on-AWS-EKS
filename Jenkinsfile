@Library('Shared') _

pipeline {
    agent any

    environment {
        TAG = "v${env.BUILD_NUMBER}"
        KUBECONFIG = '/home/ubuntu/.kube/config'
    }

    stages {

        stage('GitHub: Git Clone') {
            steps {
                gitClone("https://github.com/yashmane108/DevOps-P1.git", "master")
            }
        }

        stage('Gitleaks: Secrets Scan') {
            steps {
                script {
                    echo "Running Gitleaks Secret Scan..."

                    sh '''
                    docker run --rm \
                    -v $(pwd):/path \
                    ghcr.io/gitleaks/gitleaks:latest detect \
                    --source=/path \
                    --baseline-path=/path/.gitleaks-baseline.json
                    '''

                    echo "No hardcoded secrets detected"
                }
            }
        }

        stage('SonarQube: Code Scan') {
            steps {
                sonarToken("sonarQ-token")
            }
        }

        stage('Trivy: File System Scan') {
            steps {
                sh '''
                trivy fs \
                --exit-code 1 \
                --severity HIGH,CRITICAL \
                .
                '''
            }
        }

        stage('Docker: Build Image') {
            steps {
                sh "docker build -t yashmane108/simple-app:${TAG} ."
            }
        }

        stage('Trivy: Image Scan') {
            steps {
                sh '''
                trivy image \
                --exit-code 1 \
                --severity HIGH,CRITICAL \
                yashmane108/simple-app:${TAG}
                '''
            }
        }

        stage('Trivy: Kubernetes YAML Scan') {
            steps {
                sh "trivy config ./k8s/"
            }
        }

        stage('Docker: Push Image') {
            steps {
                dockerHubPushCred("dockerCred", "simple-app")
            }
        }

        stage('Cosign: Image Signing') {
            steps {
                cosign("cosign-private-key", "cosign-password")
            }
        }

        stage('Terraform: Drift Detection & Recovery') {
            steps {
                dir('terraform') {
                    script {

                        def exitCode = sh(
                            script: 'terraform plan -detailed-exitcode',
                            returnStatus: true
                        )

                        if (exitCode == 2) {

                            echo "⚠️ Infrastructure drift detected!"

                            sh 'terraform apply --auto-approve'

                            echo "✅ Infrastructure restored successfully"

                        } else if (exitCode == 0) {

                            echo "✅ No infrastructure drift detected"

                        } else {

                            error "Terraform plan failed"

                        }
                    }
                }
            }
        }

        stage('Kubernetes: Apply Kyverno Policies') {
            steps {
                sh "kubectl apply -f k8s/kyverno-policy.yaml"
            }
        }

        stage('Helm: Deploy Application') {
            steps {

                sh """
                helm upgrade --install my-app ./my-chart \
                --namespace my-ns \
                --create-namespace \
                --set image.tag=${TAG}
                """
            }
        }

        stage('Kubernetes: Health Check & Self-Healing') {
            steps {
                script {

                    try {

                        echo "Checking deployment rollout status..."

                        sh '''
                        kubectl rollout status deployment/my-dep \
                        -n my-ns \
                        --timeout=180s
                        '''

                        echo "✅ Deployment successful"

                        sh '''
                        kubectl get pods -n my-ns
                        '''

                        def podStatus = sh(
                            script: '''
                            kubectl get pods -n my-ns --no-headers | \
                            grep -E "CrashLoopBackOff|ImagePullBackOff|ErrImagePull" || true
                            ''',
                            returnStdout: true
                        ).trim()

                        if (podStatus) {

                            echo "❌ Pod issue detected:"
                            echo podStatus

                            echo "⚠️ Starting automatic rollback..."

                            sh "helm rollback my-app"

                            error "Self-healing triggered due to unhealthy pods"
                        }

                    } catch (Exception e) {

                        echo "❌ Deployment unhealthy"

                        echo "⚠️ Rolling back to previous stable version..."

                        sh "helm rollback my-app"

                        error "Deployment failed and rollback completed"
                    }
                }
            }
        }
    }
}
