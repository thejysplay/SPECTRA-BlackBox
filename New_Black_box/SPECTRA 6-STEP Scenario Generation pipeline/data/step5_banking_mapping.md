# banking 매핑 확인 (코드 동기화본)

실제 AgentSpec: `data/agent_spec_banking.yaml`

| 도구 | op근거 | → v7 서브카테고리 |
|---|---|---|
| get_iban | accesses=account | INV-AT(응용 도구 호출) · DAC-UBD(사용자·업무 데이터) |
| get_balance | accesses=account | INV-AT(응용 도구 호출) · DAC-UBD(사용자·업무 데이터) |
| get_most_recent_transactions | accesses=account | INV-AT(응용 도구 호출) · DAC-UBD(사용자·업무 데이터) |
| get_scheduled_transactions | accesses=account | INV-AT(응용 도구 호출) · DAC-UBD(사용자·업무 데이터) |
| get_user_info | accesses=account | INV-AT(응용 도구 호출) · DAC-UBD(사용자·업무 데이터) |
| read_file | accesses=filesystem | INV-AT(응용 도구 호출) · DAC-UBD(사용자·업무 데이터) |
| send_money | accesses=account | INV-AT(응용 도구 호출) · SC-BIZ(업무·거래 상태변경) |
| schedule_transaction | accesses=account | INV-AT(응용 도구 호출) · SC-BIZ(업무·거래 상태변경) |
| update_scheduled_transaction | accesses=account | INV-AT(응용 도구 호출) · SC-BIZ(업무·거래 상태변경) |
| update_password | accesses=account | INV-AT(응용 도구 호출) · SC-SYS(시스템·설정 상태변경) |
| update_user_info | accesses=account | INV-AT(응용 도구 호출) · SC-SYS(시스템·설정 상태변경) |

**본질 능력**: ENT-DI(직접입력), ENT-II(간접입력), ID-RG(결과 생성)

**도구 실현 지원(7)**: DAC-UBD, ENT-DI, ENT-II, ID-RG, INV-AT, SC-BIZ, SC-SYS
**권한 컨텍스트(1)**: PA-GA  (PA-GA 인정)
**도구 원자성 결합**: INV-AT ↔ {DAC-UBD, SC-BIZ, SC-SYS} 인접 필수(PA-GA 투명)

**미지원(메커니즘 부재)**: EXE-*·PST-*·ID-ER·INT-*·INV-SCU·SC-DAT·DAC-CS·DAC-SRD·HD-* 등

필터: 1531 → (a)서브카테고리 지원 41 → (b)도구 원자성 29