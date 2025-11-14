# Lambda Functions for CodeDeploy Lifecycle Hooks

# IAM Role for Lambda
resource "aws_iam_role" "deployment_hook_lambda_role" {
  name = "codedeploy-lifecycle-hook-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for Lambda
resource "aws_iam_role_policy" "deployment_hook_lambda_policy" {
  name = "codedeploy-lifecycle-hook-lambda-policy"
  role = aws_iam_role.deployment_hook_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "codedeploy:PutLifecycleEventHookExecutionStatus"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:DescribeClusters",
          "ecs:DescribeServices",
          "ecs:DescribeTasks",
          "ecs:ListTasks"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:DescribeTargetHealth",
          "elasticloadbalancing:DescribeTargetGroups"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda Function Package
data "archive_file" "lambda_deployment_hooks" {
  type        = "zip"
  source_file = "${path.module}/lambda/deployment-hooks.py"
  output_path = "${path.module}/lambda/deployment-hooks.zip"
}

# Lambda Functions for each hook
resource "aws_lambda_function" "before_install" {
  filename         = data.archive_file.lambda_deployment_hooks.output_path
  function_name    = "codedeploy-before-install-hook"
  role            = aws_iam_role.deployment_hook_lambda_role.arn
  handler         = "deployment-hooks.lambda_handler"
  source_code_hash = data.archive_file.lambda_deployment_hooks.output_base64sha256
  runtime         = "python3.12"
  timeout         = 60

  environment {
    variables = {
      HOOK_NAME = "BeforeInstall"
    }
  }

  tags = {
    Name        = "CodeDeploy BeforeInstall Hook"
    Environment = var.environment
  }
}

resource "aws_lambda_function" "after_install" {
  filename         = data.archive_file.lambda_deployment_hooks.output_path
  function_name    = "codedeploy-after-install-hook"
  role            = aws_iam_role.deployment_hook_lambda_role.arn
  handler         = "deployment-hooks.lambda_handler"
  source_code_hash = data.archive_file.lambda_deployment_hooks.output_base64sha256
  runtime         = "python3.12"
  timeout         = 300  # 5 minutes for task startup

  environment {
    variables = {
      HOOK_NAME = "AfterInstall"
    }
  }

  tags = {
    Name        = "CodeDeploy AfterInstall Hook"
    Environment = var.environment
  }
}

resource "aws_lambda_function" "after_test_traffic" {
  filename         = data.archive_file.lambda_deployment_hooks.output_path
  function_name    = "codedeploy-after-test-traffic-hook"
  role            = aws_iam_role.deployment_hook_lambda_role.arn
  handler         = "deployment-hooks.lambda_handler"
  source_code_hash = data.archive_file.lambda_deployment_hooks.output_base64sha256
  runtime         = "python3.12"
  timeout         = 300

  environment {
    variables = {
      HOOK_NAME = "AfterAllowTestTraffic"
    }
  }

  tags = {
    Name        = "CodeDeploy AfterTestTraffic Hook"
    Environment = var.environment
  }
}

resource "aws_lambda_function" "before_allow_traffic" {
  filename         = data.archive_file.lambda_deployment_hooks.output_path
  function_name    = "codedeploy-before-allow-traffic-hook"
  role            = aws_iam_role.deployment_hook_lambda_role.arn
  handler         = "deployment-hooks.lambda_handler"
  source_code_hash = data.archive_file.lambda_deployment_hooks.output_base64sha256
  runtime         = "python3.12"
  timeout         = 60

  environment {
    variables = {
      HOOK_NAME = "BeforeAllowTraffic"
    }
  }

  tags = {
    Name        = "CodeDeploy BeforeAllowTraffic Hook"
    Environment = var.environment
  }
}

resource "aws_lambda_function" "after_allow_traffic" {
  filename         = data.archive_file.lambda_deployment_hooks.output_path
  function_name    = "codedeploy-after-allow-traffic-hook"
  role            = aws_iam_role.deployment_hook_lambda_role.arn
  handler         = "deployment-hooks.lambda_handler"
  source_code_hash = data.archive_file.lambda_deployment_hooks.output_base64sha256
  runtime         = "python3.12"
  timeout         = 120

  environment {
    variables = {
      HOOK_NAME = "AfterAllowTraffic"
    }
  }

  tags = {
    Name        = "CodeDeploy AfterAllowTraffic Hook"
    Environment = var.environment
  }
}

# Lambda Permissions for CodeDeploy
resource "aws_lambda_permission" "allow_codedeploy_before_install" {
  statement_id  = "AllowExecutionFromCodeDeploy"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.before_install.function_name
  principal     = "codedeploy.amazonaws.com"
}

resource "aws_lambda_permission" "allow_codedeploy_after_install" {
  statement_id  = "AllowExecutionFromCodeDeploy"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.after_install.function_name
  principal     = "codedeploy.amazonaws.com"
}

resource "aws_lambda_permission" "allow_codedeploy_after_test_traffic" {
  statement_id  = "AllowExecutionFromCodeDeploy"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.after_test_traffic.function_name
  principal     = "codedeploy.amazonaws.com"
}

resource "aws_lambda_permission" "allow_codedeploy_before_allow_traffic" {
  statement_id  = "AllowExecutionFromCodeDeploy"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.before_allow_traffic.function_name
  principal     = "codedeploy.amazonaws.com"
}

resource "aws_lambda_permission" "allow_codedeploy_after_allow_traffic" {
  statement_id  = "AllowExecutionFromCodeDeploy"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.after_allow_traffic.function_name
  principal     = "codedeploy.amazonaws.com"
}

# Outputs
output "lambda_hook_arns" {
  description = "ARNs of Lambda deployment hooks"
  value = {
    before_install      = aws_lambda_function.before_install.arn
    after_install       = aws_lambda_function.after_install.arn
    after_test_traffic  = aws_lambda_function.after_test_traffic.arn
    before_allow_traffic = aws_lambda_function.before_allow_traffic.arn
    after_allow_traffic = aws_lambda_function.after_allow_traffic.arn
  }
}
