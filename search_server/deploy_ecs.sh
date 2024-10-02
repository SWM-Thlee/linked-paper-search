#!/bin/bash

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

  # 새 배포 강제
  aws ecs update-service \
    --cluster "$CLUSTER_NAME" \
    --service "$SERVICE_NAME" \
    --force-new-deployment

  if [ $? -eq 0 ]; then
    echo "서비스 '$SERVICE_NAME'에 새 배포가 성공적으로 적용되었습니다."
  else
    echo "서비스 '$SERVICE_NAME'에 새 배포 적용에 실패했습니다."
  fi
done
