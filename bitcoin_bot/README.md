# Phoenix 페이퍼 매매 시험 버전

사용자가 올린 `paper_decision_bot.py`를 바탕으로 안전한 **페이퍼 전용** 실행 경로를 분리했다. 실거래 주문이나 API 키는 사용하지 않는다. 매일 3% 수익을 입증하거나 보장하는 프로그램이 아니다.

`paper_decision_bot_safe.py`는 완성된 5분봉에서 LONG 돌파 신호와 상승 추세를 확인한 뒤 공개 호가를 사용해 가상 진입·청산을 기록한다. 원본의 SHORT 실행 조건은 검증 상태와 충돌하고 ML 학습 자료는 54건뿐이어서 이번 페이퍼 버전에서는 제외했다. 기존 고정 점수로는 LONG Phoenix 최고 점수가 88이고 실행 기준이 90이므로, 돌파 신호를 진입 조건으로 삼고 점수는 후보 정렬에만 사용한다. 이 전략의 수익성은 별도 검증이 필요하다.

가상 잔고는 10,000 USDT, 명목 포지션은 잔고 이하, 정상 손절 기준 거래당 계좌 손실 목표는 0.25%다. 가격 손절 0.25%, 이익 목표 0.7%, 최대 보유 60분, 왕복 수수료 가정 0.08%, 입·출구 슬리피지 각각 0.02%를 사용한다. 일일 실현 손실 1%, 일일 거래 4회, 연속 손실 2회부터 신규 진입을 막는다. 가격 급변 시 거래당 손실은 목표를 넘을 수 있다.

## 테스트 단계

1. **오프라인 동작 테스트:** `python -m unittest discover -s tests -v`. 재시작, 중복 신호, 손절 이탈, 호가 검사 등을 확인한다.
2. **공개 시세 연결 테스트:** `python paper_decision_bot_safe.py --state paper_state.json`. 한 번 실행해 `NO_TRADE`, `PAPER_OPEN`, `HOLD`, `CLOSED` 중 하나가 나와야 한다. `DATA_ERROR`는 실패다.
3. **장기간 페이퍼 관찰:** 연결 테스트가 성공한 다음 `python paper_decision_bot_safe.py --state paper_state.json --loop`로 실행하고 거래 기록과 최대 손실을 관찰한다. 상태 파일을 삭제하면 가상 포지션과 기록이 사라진다.
4. **수익성 검증:** 별도의 장기간 원시 시세와 실제 수수료·슬리피지를 이용한 시간순 보류 백테스트가 필요하다. 앞서 제공된 SHORT 신호 CSV는 이 LONG 전략의 성능 근거가 아니다.

Python 3.12에서 설치:

```bash
cd /workspace/-/bitcoin_bot
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
```

공개 현물 데이터는 Binance의 시장 데이터 전용 주소 `data-api.binance.vision`을 사용한다. CCXT는 현재 환경의 HTTPS 프록시와 CA 신뢰 설정을 사용하며, 시장 목록은 현물만 가져온다. 2026-10-19 공개 시세를 이용한 1회 실행에서 `NO_TRADE`로 정상 종료했다. 장기간 페이퍼 거래와 전략 수익성 검증은 아직 진행하지 않았다.
