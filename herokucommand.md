<!-- Build Command -->

docker build --platform linux/amd64 --provenance=false -t registry.heroku.com/tutoria-backend/web .
<!-- Push command -->
docker push registry.heroku.com/tutoria-backend/web

<!-- release -->

heroku container:release web -a tutoria-backend
<!-- set config env -->

heroku config:set SECRET_KEY="your_secret_value" -a tutoria-backend

