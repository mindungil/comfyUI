# ComfyUI 로그인 시스템

ComfyUI에 로그인 페이지가 추가되었습니다. 이제 웹 인터페이스에 접근하기 전에 로그인이 필요합니다.

## 초기 설정

1. **환경 변수 설정**

   `.env` 파일을 확인하고 필요시 비밀번호를 변경하세요:

   ```bash
   # .env 파일 내용
   COMFYUI_USERNAME=admin
   COMFYUI_PASSWORD=wjsqnrai
   SESSION_TIMEOUT=86400
   ```

   > ⚠️ **보안 권장사항**: 프로덕션 환경에서는 반드시 비밀번호를 변경하세요!

2. **python-dotenv 설치**

   환경 변수를 읽기 위해 필요합니다:

   ```bash
   pip install python-dotenv
   ```

## 사용 방법

1. **ComfyUI 시작하기**
   ```bash
   python main.py
   ```

2. **웹 브라우저에서 접속**
   - 기본 주소: `http://127.0.0.1:8188`
   - 외부 접속 허용: `python main.py --listen 0.0.0.0`

3. **로그인 페이지**
   - ComfyUI 메인 페이지(`/`)나 다른 페이지에 접근하면 자동으로 로그인 페이지(`/login.html`)로 리다이렉트됩니다
   - 아이디와 비밀번호를 입력하고 "로그인" 버튼을 클릭합니다

4. **세션 유지**
   - 로그인 후 24시간 동안 세션이 유지됩니다
   - 브라우저를 닫아도 쿠키가 남아있으면 재로그인이 필요 없습니다

5. **로그아웃**
   - API 엔드포인트: `POST /api/logout` 또는 `POST /logout`
   - 로그아웃하면 세션이 삭제되고 다시 로그인이 필요합니다

## 보안 기능

- ✅ 세션 기반 인증 (쿠키 사용)
- ✅ API 키 인증 (Open-WebUI 및 외부 통합용)
- ✅ HttpOnly 쿠키로 XSS 공격 방지
- ✅ 세션 타임아웃 (24시간)
- ✅ 모든 API 및 웹 페이지 보호
- ✅ 로그인 없이는 WebSocket 연결 불가

## 보호되는 경로

인증이 필요한 경로:
- `/` (메인 페이지)
- `/api/*` (모든 API 엔드포인트, 로그인 제외)
- `/ws` (WebSocket - 프론트엔드 연결용)
- 기타 모든 ComfyUI 기능

인증이 필요 없는 공개 경로:
- `/login.html` (로그인 페이지)
- `/login` 또는 `/api/login` (로그인 API)

## 커스터마이징

### 비밀번호 변경
`.env` 파일을 수정하세요:

```bash
COMFYUI_USERNAME=admin
COMFYUI_PASSWORD=새로운_비밀번호
```

### 세션 타임아웃 변경
`.env` 파일에서 세션 타임아웃을 초 단위로 설정:

```bash
SESSION_TIMEOUT=86400  # 24시간 (원하는 초 단위로 변경)
```

변경 후 ComfyUI를 재시작하면 적용됩니다.

## 문제 해결

### 로그인이 안 될 때
1. 브라우저 콘솔(F12)에서 에러 메시지 확인
2. ComfyUI 서버 로그 확인
3. 쿠키가 활성화되어 있는지 확인

### 세션이 자주 만료될 때
- `SESSION_TIMEOUT` 값을 늘리세요
- 브라우저 쿠키 설정을 확인하세요

### WebSocket 연결 오류
- 로그인이 제대로 되었는지 확인
- 브라우저를 새로고침해보세요
- 세션이 만료되지 않았는지 확인

## API 사용 예제

### 방법 1: 세션 기반 인증 (웹 브라우저 및 curl)

#### 로그인
```bash
# .env 파일에 설정된 username과 password 사용
curl -X POST http://127.0.0.1:8188/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}' \
  -c cookies.txt
```

#### 인증된 요청
```bash
curl http://127.0.0.1:8188/api/queue \
  -b cookies.txt
```

#### 로그아웃
```bash
curl -X POST http://127.0.0.1:8188/api/logout \
  -b cookies.txt
```

### 방법 2: API 키 인증 (Open-WebUI 및 외부 통합용)

API 키를 사용하면 로그인 없이 직접 API에 접근할 수 있습니다. Open-WebUI와 같은 외부 서비스와 통합할 때 유용합니다.

#### API 키 설정

1. `.env` 파일에 API 키 추가:
   ```bash
   API_KEY=your_secure_api_key_here
   ```

2. ComfyUI 재시작:
   ```bash
   python main.py
   ```

#### API 키로 요청하기

**방법 1: Authorization Bearer 헤더 사용**
```bash
curl http://127.0.0.1:8188/api/queue \
  -H "Authorization: Bearer your_secure_api_key_here"
```

**방법 2: X-API-Key 헤더 사용**
```bash
curl http://127.0.0.1:8188/api/queue \
  -H "X-API-Key: your_secure_api_key_here"
```

#### Open-WebUI와 연동하기

Open-WebUI 설정에서 ComfyUI를 외부 API로 추가할 때:

1. **URL**: `http://your-server:8188`
2. **API Key**: `.env` 파일에 설정한 `API_KEY` 값 입력
3. **Header**: `Authorization: Bearer <API_KEY>` 또는 `X-API-Key: <API_KEY>`

#### Python으로 API 키 사용 예제
```python
import requests

API_KEY = "your_secure_api_key_here"
BASE_URL = "http://127.0.0.1:8188"

# 방법 1: Authorization Bearer 헤더
headers = {
    "Authorization": f"Bearer {API_KEY}"
}

# 방법 2: X-API-Key 헤더
# headers = {
#     "X-API-Key": API_KEY
# }

response = requests.get(f"{BASE_URL}/api/queue", headers=headers)
print(response.json())
```

#### API 키 보안 권장사항
- 강력한 랜덤 키를 생성하세요 (최소 32자 이상)
- API 키를 Git에 커밋하지 마세요
- 정기적으로 API 키를 변경하세요
- HTTPS를 사용하여 통신을 암호화하세요

## 구현 세부사항

### 파일 구조
```
ComfyUI/
├── .env                              # 인증 정보 (비밀번호 설정)
├── .env.example                      # 환경 변수 예제 파일
├── login.html                        # 로그인 페이지
├── middleware/
│   └── auth_middleware.py            # 인증 미들웨어
└── server.py                         # 로그인/로그아웃 라우트 추가
```

### 보안 고려사항
- **환경 변수**: 비밀번호는 `.env` 파일에 저장됩니다
- **세션 관리**: 현재 세션은 메모리에 저장됩니다 (서버 재시작 시 모든 세션 삭제)
- **프로덕션 권장사항**:
  - `.env` 파일을 Git에 커밋하지 마세요 (`.gitignore`에 추가)
  - Redis나 데이터베이스 사용 권장
  - HTTPS 사용을 강력히 권장 (TLS 설정: `--tls-keyfile`, `--tls-certfile`)
  - 반드시 기본 비밀번호를 변경하세요
