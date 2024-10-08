#!/bin/bash

# Auto Scaling 그룹 이름 설정
ASG_NAME="BackendInfraStack-GPUAutoScalingGroupASGBEA65D5D-ZFE5D6fKbjWN"

# Auto Scaling 그룹의 현재 desired capacity 가져오기
CURRENT_DESIRED_CAPACITY=$(aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names "$ASG_NAME" \
  --query 'AutoScalingGroups[0].DesiredCapacity' --output text)

# desired capacity + 1로 일시적으로 설정
NEW_DESIRED_CAPACITY=$((CURRENT_DESIRED_CAPACITY + 1))
echo "Auto Scaling 그룹 '$ASG_NAME'의 desired capacity를 $NEW_DESIRED_CAPACITY로 업데이트합니다..."

# Auto Scaling 그룹의 desired capacity 업데이트
aws autoscaling update-auto-scaling-group \
  --auto-scaling-group-name "$ASG_NAME" \
  --desired-capacity "$NEW_DESIRED_CAPACITY" \
  --no-cli-pager

if [ $? -eq 0 ]; then
  echo "Auto Scaling 그룹 '$ASG_NAME'의 desired capacity가 $NEW_DESIRED_CAPACITY로 성공적으로 업데이트되었습니다."

  # ECS 서비스에 대한 새 배포 실행 (이전 스크립트 재사용 가능)
  # 클러스터 이름 설정
  CLUSTER_NAME="BackendInfraStack-SearchServiceClusterB05BF7D0-q0WCq5EJCEBB"

  # 클러스터로부터 서비스 목록 가져오기
  SERVICES=$(aws ecs list-services --cluster "$CLUSTER_NAME" --query 'serviceArns[*]' --output text)

  # 서비스 목록이 비어있는지 확인
  if [ -z "$SERVICES" ]; then
    echo "클러스터 '$CLUSTER_NAME'에서 서비스를 찾을 수 없습니다."
    exit 1
  fi

  # 각 서비스에 대해 새 배포를 강제로 적용
  for SERVICE_ARN in $SERVICES; do
    SERVICE_NAME=$(basename "$SERVICE_ARN")  # ARN에서 서비스 이름 추출
    echo "서비스 '$SERVICE_NAME'에 대해 새 배포를 시작합니다..."

    새 배포 강제
    aws ecs update-service \
      --cluster "$CLUSTER_NAME" \
      --service "$SERVICE_NAME" \
      --force-new-deployment \
      --no-cli-pager

    if [ $? -eq 0 ]; then
      echo "서비스 '$SERVICE_NAME'에 새 배포가 성공적으로 적용되었습니다."
    else
      echo "서비스 '$SERVICE_NAME'에 새 배포 적용에 실패했습니다."
    fi
  done

#   # 배포 후 Auto Scaling 그룹의 desired capacity 복원
#   echo "Auto Scaling 그룹 '$ASG_NAME'의 desired capacity를 $CURRENT_DESIRED_CAPACITY로 복원합니다..."
#   aws autoscaling update-auto-scaling-group \
#     --auto-scaling-group-name "$ASG_NAME" \
#     --desired-capacity "$CURRENT_DESIRED_CAPACITY" \
#     --no-cli-pager

#   if [ $? -eq 0 ]; then
#     echo "Auto Scaling 그룹 '$ASG_NAME'의 desired capacity가 성공적으로 복원되었습니다."
#   else
#     echo "Auto Scaling 그룹 '$ASG_NAME'의 desired capacity 복원에 실패했습니다."
#   fi
else
  echo "Auto Scaling 그룹 '$ASG_NAME'의 desired capacity 업데이트에 실패했습니다."
fi
