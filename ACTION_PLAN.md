# PageIndex API – 남은 작업 액션 플랜

> API Phase 1~4 구현 완료. UI는 별도 프로젝트에서 구성. Phase 7 완료.

---

## Phase 7: 통합 및 배포 ✅

### 7.1 운영 환경 설정 ✅
- [x] `env.example` (환경 변수 템플릿)
- [x] CORS `CORS_ORIGINS` 환경 변수 지원

### 7.2 컨테이너화 ✅
- [x] `Dockerfile`
- [x] `docker-compose.yml`
- [x] `.dockerignore`

### 7.3 보안 및 안정성 ✅
- [x] Rate limiting (POST /documents 10/min)
- [x] 업로드 파일 크기 제한 `MAX_UPLOAD_BYTES`

### 7.4 로깅 ✅
- [x] `api/logging_config.py` – 구조화 로깅, 요청 로깅 미들웨어
- [x] `LOG_FORMAT=json`, `LOG_LEVEL` 지원

---

## 선택: 품질 및 유지보수 ✅

### 테스트 ✅
- [x] `tests/test_api.py` – API E2E 테스트

### 문서 ✅
- [x] `docs/API.md` – API 사용 가이드

### 기타 ✅
- [x] `DELETE /documents/{id}`

### 미구현
- [ ] Job 만료 정책 (오래된 job 레코드 정리)

---

## 진행 순서 제안

1. **7.1** 운영 환경 설정 – 바로 적용 가능
2. **7.2** Docker – 배포 자동화
3. **7.3** 보안 – 운영 전 점검
4. **7.4** 로깅 – 운영 관찰
5. 테스트/문서 – 필요 시 순차 진행
