# Taint and recreate API service
terraform taint module.ecs.aws_ecs_service.api
terraform apply -target=module.ecs.aws_ecs_service.api

# Taint and recreate UI service
terraform taint module.ecs.aws_ecs_service.ui
terraform apply -target=module.ecs.aws_ecs_service.ui

# Taint and recreate Central service
terraform taint module.ecs.aws_ecs_service.central
terraform apply -target=module.ecs.aws_ecs_service.central