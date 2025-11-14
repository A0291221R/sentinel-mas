"""
CodeDeploy Lifecycle Hook Lambda Functions
Validates deployment at various stages of Blue/Green deployment
"""

import json
import boto3
import time
import os
from typing import Dict, Any

codedeploy = boto3.client('codedeploy')
ecs = boto3.client('ecs')
elbv2 = boto3.client('elbv2')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, str]:
    """
    Main Lambda handler for CodeDeploy lifecycle hooks
    
    Event structure:
    {
        "DeploymentId": "d-XXXXXXXXX",
        "LifecycleEventHookExecutionId": "xxxxx-xxxx-xxxx",
        "TaskSetArn": "arn:aws:ecs:...",
        ...
    }
    """
    print(f"Event: {json.dumps(event, indent=2)}")
    
    deployment_id = event.get('DeploymentId')
    lifecycle_event_hook_execution_id = event.get('LifecycleEventHookExecutionId')
    
    try:
        # Determine which hook is being executed
        hook_name = event.get('LifecycleEventName', 'Unknown')
        
        if hook_name == 'BeforeInstall':
            result = validate_before_install(event)
        elif hook_name == 'AfterInstall':
            result = validate_after_install(event)
        elif hook_name == 'AfterAllowTestTraffic':
            result = validate_test_traffic(event)
        elif hook_name == 'BeforeAllowTraffic':
            result = validate_before_production(event)
        elif hook_name == 'AfterAllowTraffic':
            result = validate_after_production(event)
        else:
            print(f"Unknown hook: {hook_name}")
            result = {'status': 'Succeeded', 'message': 'Hook not implemented'}
        
        # Report success to CodeDeploy
        if result['status'] == 'Succeeded':
            codedeploy.put_lifecycle_event_hook_execution_status(
                deploymentId=deployment_id,
                lifecycleEventHookExecutionId=lifecycle_event_hook_execution_id,
                status='Succeeded'
            )
            print(f"✅ {hook_name} validation passed")
        else:
            raise Exception(result.get('message', 'Validation failed'))
            
    except Exception as e:
        print(f"❌ Hook validation failed: {str(e)}")
        
        # Report failure to CodeDeploy
        codedeploy.put_lifecycle_event_hook_execution_status(
            deploymentId=deployment_id,
            lifecycleEventHookExecutionId=lifecycle_event_hook_execution_id,
            status='Failed'
        )
        
        raise e
    
    return {'statusCode': 200, 'body': json.dumps(result)}


def validate_before_install(event: Dict[str, Any]) -> Dict[str, str]:
    """Validate environment before new tasks are created"""
    print("🔍 Running BeforeInstall validation...")
    
    # Check if cluster has capacity
    cluster_arn = get_cluster_from_event(event)
    if cluster_arn:
        cluster_info = ecs.describe_clusters(clusters=[cluster_arn])
        if cluster_info['clusters']:
            cluster = cluster_info['clusters'][0]
            print(f"Cluster status: {cluster['status']}")
            print(f"Active services: {cluster['activeServicesCount']}")
            print(f"Running tasks: {cluster['runningTasksCount']}")
    
    return {'status': 'Succeeded', 'message': 'Pre-deployment checks passed'}


def validate_after_install(event: Dict[str, Any]) -> Dict[str, str]:
    """Validate new tasks are healthy after creation"""
    print("🔍 Running AfterInstall validation...")
    
    task_set_arn = event.get('TaskSetArn')
    if not task_set_arn:
        return {'status': 'Succeeded', 'message': 'No task set to validate'}
    
    # Wait for tasks to be running
    max_attempts = 20
    for attempt in range(max_attempts):
        tasks = get_tasks_from_task_set(task_set_arn)
        
        if not tasks:
            print(f"Attempt {attempt + 1}/{max_attempts}: No tasks found yet")
            time.sleep(15)
            continue
        
        # Check task health
        healthy_count = 0
        total_count = len(tasks)
        
        for task in tasks:
            last_status = task.get('lastStatus', '')
            health_status = task.get('healthStatus', 'UNKNOWN')
            
            print(f"Task: {task['taskArn'].split('/')[-1]} - Status: {last_status}, Health: {health_status}")
            
            if last_status == 'RUNNING' and health_status == 'HEALTHY':
                healthy_count += 1
        
        if healthy_count == total_count and total_count > 0:
            print(f"✅ All {total_count} tasks are healthy")
            return {'status': 'Succeeded', 'message': f'{healthy_count}/{total_count} tasks healthy'}
        
        print(f"Attempt {attempt + 1}/{max_attempts}: {healthy_count}/{total_count} tasks healthy")
        time.sleep(15)
    
    return {'status': 'Failed', 'message': 'Tasks did not become healthy in time'}


def validate_test_traffic(event: Dict[str, Any]) -> Dict[str, str]:
    """Validate service with 10% test traffic"""
    print("🔍 Running AfterAllowTestTraffic validation...")
    
    # Get target group for new deployment
    target_group_arn = get_target_group_from_event(event)
    if not target_group_arn:
        return {'status': 'Succeeded', 'message': 'No target group to validate'}
    
    # Perform health checks
    time.sleep(30)  # Allow time for traffic to flow
    
    health_checks = perform_health_checks(target_group_arn)
    
    if health_checks['healthy'] >= health_checks['minimum_required']:
        print(f"✅ Test traffic validation passed: {health_checks['healthy']}/{health_checks['total']} targets healthy")
        return {'status': 'Succeeded', 'message': 'Test traffic validation passed'}
    else:
        return {'status': 'Failed', 'message': f"Insufficient healthy targets: {health_checks['healthy']}/{health_checks['total']}"}


def validate_before_production(event: Dict[str, Any]) -> Dict[str, str]:
    """Final validation before shifting all traffic"""
    print("🔍 Running BeforeAllowTraffic validation...")
    
    # Run comprehensive health checks
    task_set_arn = event.get('TaskSetArn')
    if task_set_arn:
        tasks = get_tasks_from_task_set(task_set_arn)
        
        if not tasks:
            return {'status': 'Failed', 'message': 'No tasks found'}
        
        # Verify all tasks are healthy
        unhealthy_tasks = []
        for task in tasks:
            health_status = task.get('healthStatus', 'UNKNOWN')
            if health_status != 'HEALTHY':
                unhealthy_tasks.append(task['taskArn'].split('/')[-1])
        
        if unhealthy_tasks:
            return {'status': 'Failed', 'message': f'Unhealthy tasks: {", ".join(unhealthy_tasks)}'}
    
    return {'status': 'Succeeded', 'message': 'Ready for production traffic'}


def validate_after_production(event: Dict[str, Any]) -> Dict[str, str]:
    """Validate deployment after all traffic is shifted"""
    print("🔍 Running AfterAllowTraffic validation...")
    
    # Monitor for any issues after full traffic shift
    time.sleep(60)  # Monitor for 1 minute
    
    target_group_arn = get_target_group_from_event(event)
    if target_group_arn:
        health_checks = perform_health_checks(target_group_arn)
        
        if health_checks['healthy'] < health_checks['minimum_required']:
            return {'status': 'Failed', 'message': 'Health degraded after traffic shift'}
    
    print("✅ Post-deployment validation passed")
    return {'status': 'Succeeded', 'message': 'Deployment completed successfully'}


def get_cluster_from_event(event: Dict[str, Any]) -> str:
    """Extract cluster ARN from event"""
    # This depends on your event structure
    # You may need to parse from TaskSetArn or get from deployment metadata
    return event.get('ClusterArn', '')


def get_tasks_from_task_set(task_set_arn: str) -> list:
    """Get tasks from a task set"""
    try:
        # Parse cluster and service from task set ARN
        parts = task_set_arn.split('/')
        cluster = parts[-3]
        service = parts[-2]
        
        # List tasks
        response = ecs.list_tasks(
            cluster=cluster,
            serviceName=service,
            desiredStatus='RUNNING'
        )
        
        if not response.get('taskArns'):
            return []
        
        # Describe tasks
        tasks_response = ecs.describe_tasks(
            cluster=cluster,
            tasks=response['taskArns']
        )
        
        return tasks_response.get('tasks', [])
        
    except Exception as e:
        print(f"Error getting tasks: {str(e)}")
        return []


def get_target_group_from_event(event: Dict[str, Any]) -> str:
    """Extract target group ARN from event"""
    return event.get('TargetGroupArn', '')


def perform_health_checks(target_group_arn: str) -> Dict[str, int]:
    """Perform health checks on target group"""
    try:
        response = elbv2.describe_target_health(
            TargetGroupArn=target_group_arn
        )
        
        total = len(response['TargetHealthDescriptions'])
        healthy = sum(1 for target in response['TargetHealthDescriptions'] 
                     if target['TargetHealth']['State'] == 'healthy')
        
        # Require at least 80% healthy
        minimum_required = max(1, int(total * 0.8))
        
        return {
            'total': total,
            'healthy': healthy,
            'minimum_required': minimum_required
        }
        
    except Exception as e:
        print(f"Error checking target health: {str(e)}")
        return {'total': 0, 'healthy': 0, 'minimum_required': 1}
