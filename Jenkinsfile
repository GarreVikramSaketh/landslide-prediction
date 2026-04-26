pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "vikamsakethgarre/landslide-app"
        IMAGE_TAG = "${BUILD_NUMBER}"
    }

    stages {

        stage('Build Docker Image') {
            steps {
                sh '''
                docker build -t $DOCKER_IMAGE:$IMAGE_TAG .
                docker tag $DOCKER_IMAGE:$IMAGE_TAG $DOCKER_IMAGE:latest
                '''
            }
        }

        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                    sh '''
                    echo $PASS | docker login -u $USER --password-stdin
                    docker push $DOCKER_IMAGE:$IMAGE_TAG
                    docker push $DOCKER_IMAGE:latest
                    '''
                }
            }
        }

        stage('Deploy (Blue-Green - EC2)') {
            steps {
                sh '''
                echo "Starting Blue-Green Deployment..."

                if docker ps -a --format '{{.Names}}' | grep -q landslide-blue; then
                    docker stop landslide-green || true
                    docker rm landslide-green || true

                    docker run -d -p 81:5000 --name landslide-green $DOCKER_IMAGE:latest

                    docker stop landslide-blue
                    docker rm landslide-blue

                    docker run -d -p 80:5000 --name landslide-blue $DOCKER_IMAGE:latest

                    docker stop landslide-green
                    docker rm landslide-green
                else
                    docker stop landslide || true
                    docker rm landslide || true

                    docker run -d -p 80:5000 --name landslide-blue $DOCKER_IMAGE:latest
                fi
                '''
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: 'aws-creds',
                    accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                    secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                ]]) {
                    sh '''
                    echo "Deploying to Kubernetes..."

                    docker run --rm \
                      -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
                      -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
                      -e AWS_DEFAULT_REGION=us-east-1 \
                      -e KUBECONFIG=/root/.kube/config.new \
                      -v /var/jenkins_home/.kube:/root/.kube \
                      -v $(pwd):/app \
                      bitnami/kubectl:latest \
                      apply -f /app/k8s/ --validate=false

                    docker run --rm \
                      -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
                      -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
                      -e AWS_DEFAULT_REGION=us-east-1 \
                      -e KUBECONFIG=/root/.kube/config.new \
                      -v /var/jenkins_home/.kube:/root/.kube \
                      -v $(pwd):/app \
                      bitnami/kubectl:latest \
                      rollout restart deployment landslide-app
                    '''
                }
            }
        }
    }
}