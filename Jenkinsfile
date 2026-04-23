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

        stage('Deploy (Blue-Green)') {
            steps {
                sh '''
                echo "Starting Blue-Green Deployment..."

                # Check if BLUE exists
                if docker ps -a --format '{{.Names}}' | grep -q landslide-blue; then

                    echo "Deploying GREEN version..."
                    docker stop landslide-green || true
                    docker rm landslide-green || true

                    docker run -d -p 81:5000 --name landslide-green $DOCKER_IMAGE:latest

                    echo "Switching traffic to GREEN..."

                    docker stop landslide-blue
                    docker rm landslide-blue

                    docker run -d -p 80:5000 --name landslide-blue $DOCKER_IMAGE:latest

                    echo "Cleaning up GREEN..."
                    docker stop landslide-green
                    docker rm landslide-green

                else
                    echo "First deployment → BLUE"
                    docker stop landslide || true
                    docker rm landslide || true

                    docker run -d -p 80:5000 --name landslide-blue $DOCKER_IMAGE:latest
                fi
                '''
            }
        }
    }
}