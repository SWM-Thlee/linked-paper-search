# Lambda 기반 데이터 수집 및 전처리 모듈

AWS Lambda와 Chalice를 사용하여 논문 데이터를 수집하고 전처리하는 모듈

## Chalice
Chalice는 AWS에서 제공하는 마이크로서비스 프레임워크로, Python 언어로 AWS Lambda 함수를 빠르고 배포 가능

### 설치 방법
```bash
pip install chalice==1.31.2
```
### 배포 방법
```bash
aws configure
```
lambda 함수 생성과 IAM role 생성이 가능한 계정으로 설정

Chalice 애플리케이션을 AWS에 배포하려면, 프로젝트 루트 디렉토리에서 다음 명령어를 실행
```bash
chalice deploy
```
배포시, lambda 실행에 IAM role 생성과 lambda 함수 생성

### 필수 라이브러리
Lambda 함수 패키징에 필요한 라이브러리는 requirements.txt 파일에 명시. AWS Lambda의 패키징 사이즈 제한(50 MB)을 고려하여 필요한 라이브러리만 포함


### 프로젝트 구조
```bash
/
|- .chalice/            # Chalice 설정 파일 및 자동 생성된 정책
|- chalicelib/          # 사용자 정의 모듈 및 라이브러리
|- app.py               # 주 실행 애플리케이션 파일
|- requirements.txt     # 필수 Python 라이브러리
```


### IAM Policy
필요한 IAM 권한 정리
TODO
