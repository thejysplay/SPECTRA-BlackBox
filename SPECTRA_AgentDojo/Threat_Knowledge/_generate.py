# -*- coding: utf-8 -*-
"""
SPECTRA Threat Knowledge 정적 구조 생성기  (교수님 최종 Instance 정본: 136 instance)
====================================================================================================
- THREAT_MATRIX : E1~E10 / 24 Subcategory / 136 Instance. 각 Instance = {name_ko, name_en, description, example}.
- CASE_STUDIES  : 31 ATLAS CS (name/description/attack_steps=원본, attack_goal/sequence/instances=SPECTRA 매핑).
- ATTACK_GOALS  : G1~G9 (name/sequence/terminal).
숫자(136)는 목표가 아니라 결과다. Instance = Agent Spec 에서 존재 확인 가능 + 있으면 다른 시나리오를 만들 수 있는 구체적 대상.
출력: threat_knowledge.yaml.  실행: <venv>/python _generate.py
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
ATLAS = HERE.parent / "Threat_Specification" / "ATLAS_Orign" / "ATLAS-2026.07.yaml"

# ── Element 메타 (교수님 표현) ────────────────────────────────────────────────
ELEMENT_META = {
    "E1":  ("진입", "Entry", "Direct + Indirect 모든 입력 수단"),
    "E2":  ("편입", "Integration", "Agent 기능 범위 내에 외부 도구·설정·모델 등의 구성요소가 받아들여짐"),
    "E3":  ("인지 조작", "Cognition Manipulation", "외부 영향으로 Agent 의 판단·계획 또는 생성 결과가 원래 의도와 다르게 변경"),
    "E4":  ("권한·권위", "Privilege/Authority", "Agent 에게 부여된 권한의 사용, Credential 을 통한 접근, 또는 접근통제의 우회"),
    "E5":  ("데이터 확보", "Data Exfiltration", "공격자가 목표로 하는 민감 데이터에 접근하여 정보를 확보"),
    "E6":  ("호출", "Invocation", "Agent 가 작업을 수행하기 위해 Tool·API·System 기능의 실행 요청을 생성"),
    "E7":  ("실행", "Execution", "Agent 의 요청에 의해 실제 실행환경에서 Code·Script 또는 System Command 가 수행"),
    "E8":  ("상태 변경·지속", "State Change & Persistence", "시스템 데이터·상태가 변경되거나, 저장된 Context·Memory 등이 이후에도 계속 영향을 미침"),
    "E9":  ("정보 공개", "Information Disclosure", "공격 결과가 생성되거나, 생성·확보된 정보가 실제 외부 대상으로 전달·노출"),
    "E10": ("인간 의존", "Human Dependency", "공격 성공을 위해 사람이 Agent 결과를 신뢰하고 실제 행동·승인·의사결정을 수행해야 함"),
}
SUBCAT_META = {
    "ENT-DI":   ("직접 입력", "Direct Input", "공격자가 Agent 의 직접 입력 인터페이스를 통해 지시 또는 콘텐츠를 전달"),
    "ENT-II":   ("간접 입력", "Indirect Input", "이메일·파일·웹사이트 등 외부 콘텐츠가 Agent 의 작업 과정에서 간접적으로 Context 에 유입"),
    "INT-EC":   ("실행형 구성요소", "Executable Component", "Agent 가 실제 기능으로 사용할 수 있는 실행형 구성요소"),
    "INT-CR":   ("설정·규칙", "Config·Rule", "Agent 또는 Tool 의 동작 방식·조건·절차를 정하는 구성정보"),
    "INT-MT":   ("모델·템플릿", "Model·Template", "Agent 의 판단·생성에 사용되는 Model 및 Model 수준 구성요소"),
    "CM-AM":    ("행동 조작", "Action Manipulation", "Agent 가 무엇을 하고 어떻게 행동할지에 대한 판단·Planning 이 변경"),
    "CM-GM":    ("생성 조작", "Generation Manipulation", "Agent 가 생성하는 Content·Code·Prompt·File 등의 결과가 변경"),
    "PA-GA":    ("부여 권한", "Granted Authority", "Agent 에게 이미 부여되거나 위임된 권한으로 기능·자원에 접근"),
    "PA-CT":    ("자격증명·토큰 사용", "Credential·Token Use", "인증에 사용되는 Credential·Token 을 이용해 시스템·서비스에 접근"),
    "PA-ACB":   ("접근통제 우회", "Access-Control Bypass", "정상적으로 적용되어야 하는 인증·권한·접근·승인 통제를 거치지 않고 기능이나 자원에 접근"),
    "DEX-UBD":  ("사용자·업무 데이터", "User·Business Data", "사용자·조직·업무 활동과 관련된 데이터"),
    "DEX-CS":   ("자격증명·비밀", "Credential·Secret", "시스템·서비스 접근에 사용되는 인증정보 및 Secret"),
    "DEX-SRD":  ("시스템·런타임 데이터", "System·Runtime Data", "Agent 또는 시스템의 실행환경에서 발생·저장되는 내부 정보"),
    "INV-AT":   ("응용 도구", "Application Tool", "일반적인 업무·Application 기능을 수행하는 Tool 을 호출"),
    "INV-SCU":  ("시스템·컴퓨터 사용", "System·Computer-Use", "Application 수준을 넘어 실제 컴퓨터·OS·실행환경을 직접 조작하는 기능을 호출"),
    "INV-CAI":  ("제어·관리 인터페이스", "Control·Admin Interface", "Agent·서비스·인프라의 운영·관리 기능을 제공하는 제어 인터페이스를 호출"),
    "EXEC-SE":  ("코드·스크립트 실행", "Code·Script Execution", "프로그램 언어 또는 Script 형태의 Code 가 실제 Runtime 에서 실행"),
    "EXEC-SSE": ("Shell·시스템 명령 실행", "Shell·System Command Execution", "Shell·OS·System 수준의 Command 가 실행환경에서 직접 수행"),
    "SCP-SC":   ("상태 변경", "State Change", "Agent 행동으로 실제 System·Application 데이터 또는 상태가 변경"),
    "SCP-CC":   ("컨텍스트 이월", "Context Carryover", "저장된 정보·Context 가 이후 Turn·Session·Agent 실행에서도 다시 사용되어 영향을 지속"),
    "ID-RG":    ("결과 생성", "Result Generation", "정보가 포함된 결과물이 생성되었으나 별도의 외부 전달 여부는 아직 요구하지 않음"),
    "ID-ER":    ("외부 공개", "External Release", "확보하거나 생성한 정보가 현재 Agent 내부 결과를 넘어 별도의 외부 수신자·서비스·저장소로 전달 또는 공개"),
    "HD-UI":    ("사용자 유도", "User Inducement", "Agent 결과에 따라 사용자가 구체적인 추가 행동을 수행하도록 유도"),
    "HD-UAD":   ("사용자 승인·판단", "User Approval·Decision", "공격 성공이 사람의 승인·신뢰·판단에 의존"),
}

# ── 136 Instance 정본 : (element, subcode, [ (KEY, name_ko, name_en, description, example), ... ]) ──
MATRIX_SRC = [
 ("E1", "ENT-DI", [
   ("CHAT", "Chat / 화면 입력", "Chat / UI Input", "사용자가 Agent 의 Chat·UI 화면을 통해 직접 입력하는 콘텐츠", "Chat 창에 직접 Prompt 입력"),
   ("CLI", "CLI / Terminal 입력", "CLI / Terminal Input", "CLI·Terminal 인터페이스를 통해 Agent 에 직접 전달되는 입력", "CLI argument 로 Agent 작업 요청"),
   ("API", "API 입력", "API / Agent Endpoint Input", "Agent API 또는 Endpoint 요청을 통해 직접 전달되는 입력", "API request body 에 작업 지시 포함"),
 ]),
 ("E1", "ENT-II", [
   ("EMAIL", "Email / 메일", "Email", "Agent 가 조회·처리하는 외부 Email 콘텐츠", "Email 본문을 Agent 가 읽음"),
   ("FILE", "File / 문서", "File / Document", "Agent 가 읽거나 처리하는 외부 File·Document 콘텐츠", "read_file 로 문서 내용 조회"),
   ("WEB_URL", "Web / URL", "Web / URL", "Agent 가 접근하여 읽는 외부 Web page 또는 URL 콘텐츠", "Browser 로 Web page 내용 확인"),
   ("MESSAGE_SNS", "Message / SNS", "Message / SNS", "Messenger·SNS·협업 서비스에 존재하는 외부 메시지 콘텐츠", "Slack·Teams 메시지 조회"),
   ("CALENDAR_EVENT", "Calendar / Event", "Calendar / Event", "Calendar 일정의 제목·본문·설명 등에 포함된 콘텐츠", "일정 description 조회"),
   ("RETRIEVED_CONTENT", "검색 / 검색 콘텐츠", "Search / Retrieved Content", "Search·Retrieval·RAG 를 통해 가져온 콘텐츠", "검색 결과 문서를 Agent 가 읽음"),
   ("WORK_ITEM", "업무 항목 / 협업 콘텐츠", "Work Item / Collaboration Content", "Issue·Ticket·PR·Task 등 업무 객체에 저장된 콘텐츠", "PR description 또는 Ticket 본문 조회"),
   ("APPLICATION_RECORD", "애플리케이션 / 서비스 레코드", "Application / Service Record", "연결된 업무 App·서비스에 저장되어 Agent 가 조회하는 Record 형태의 콘텐츠", "거래내역·예약정보·고객 Record 조회"),
 ]),
 ("E2", "INT-EC", [
   ("TOOL_PLUGIN", "Tool / Plugin", "Tool / Plugin", "Agent 가 직접 호출할 수 있도록 등록되는 실행형 Tool·Plugin", "외부 Plugin 등록"),
   ("SKILL_FUNCTION", "Skill / Function", "Skill / Function", "특정 작업을 수행하도록 Agent 에 추가되는 Skill·Function", "새로운 Skill 추가"),
   ("MCP_REMOTE_TOOL", "MCP / Remote Tool", "MCP / Remote Tool", "MCP Server 또는 Remote Function 을 통해 제공되는 실행 기능", "MCP Server 연결"),
   ("PACKAGE_LIBRARY", "Package / Library", "Package / Library", "Agent 실행환경에 포함되어 기능 수행에 사용되는 코드 의존성", "외부 Library 설치"),
   ("EXTENSION_ADDON", "Extension / Add-on", "Extension / Add-on", "기존 Agent 기능에 추가되는 확장 구성요소", "Browser/Agent Extension 설치"),
 ]),
 ("E2", "INT-CR", [
   ("SYSTEM_INSTRUCTION", "System Instruction / Prompt", "System Instruction / Prompt", "Agent 의 기본 역할과 행동 방향을 지정하는 상위 Instruction", "System Prompt 설정"),
   ("POLICY_GUARDRAIL", "Policy / Guardrail 설정", "Policy / Guardrail Configuration", "허용·제한·승인 조건 등 Agent 의 정책적 동작을 정하는 설정", "민감작업 승인 정책"),
   ("CONFIGURATION", "Configuration / Setting", "Configuration / Setting", "Agent 또는 Tool 의 동작값과 기능 설정을 지정하는 구성정보", "Endpoint·Mode 설정"),
   ("INSTRUCTION_FILE", "Instruction File", "Instruction File", "Agent 가 작업 과정에서 참고하는 별도의 지시 파일", "AGENTS.md 등"),
   ("WORKFLOW_PROCEDURE", "Workflow / Procedure 정의", "Workflow / Procedure Definition", "Agent 가 수행할 작업의 단계와 절차를 정의하는 구성", "승인→실행 Workflow"),
 ]),
 ("E2", "INT-MT", [
   ("MODEL_CHECKPOINT", "Model / Checkpoint", "Model / Checkpoint", "Agent 가 추론·생성에 사용하는 Model 또는 Checkpoint", "특정 LLM checkpoint 사용"),
   ("CHAT_TEMPLATE", "Model Chat Template", "Model Chat Template", "Model 에 전달되는 대화 구조와 형식을 지정하는 Template", "Model 별 Chat Template"),
   ("EMBEDDING_INDEX", "Embedding / Index", "Embedding / Index", "검색·표현·유사도 계산 등에 사용되는 Embedding 또는 Index", "Vector Index 사용"),
   ("ADAPTER_LORA", "Adapter / LoRA", "Adapter / LoRA", "기본 Model 에 추가로 결합되어 Model 동작에 영향을 주는 구성요소", "LoRA Adapter 적용"),
 ]),
 ("E3", "CM-AM", [
   ("GOAL_PLAN", "목표 / 계획", "Goal / Plan", "Agent 가 수행하려는 목표 또는 작업 계획", "조회 작업이 다른 작업 수행 계획으로 변경"),
   ("TOOL_SELECTION", "Tool 선택", "Tool Selection", "작업 수행에 사용할 Tool 을 선택하는 판단", "조회 Tool 대신 송금 Tool 선택"),
   ("TOOL_ARGUMENT", "Tool 입력값", "Tool Argument", "Tool 호출에 전달되는 입력값·Parameter", "recipient, amount 값 변경"),
   ("ACTION_ORDER", "작업 순서", "Action Order", "복수 행동 또는 Tool 호출의 수행 순서", "확인 전에 실행부터 수행"),
 ]),
 ("E3", "CM-GM", [
   ("RESPONSE_CONTENT", "생성 Response / Content", "Generated Response / Content", "Agent 가 생성하는 텍스트·정보·콘텐츠", "잘못된 설명 또는 정보 생성"),
   ("CODE_SCRIPT", "생성 Code / Script", "Generated Code / Script", "Agent 가 작성하는 프로그램 Code·Script", "Python Script 생성"),
   ("PROMPT_INSTRUCTION", "생성 Prompt / Instruction", "Generated Prompt / Instruction", "Agent 가 다른 Agent·Model 등에 전달하기 위해 생성하는 Prompt·Instruction", "후속 Agent 용 Prompt 생성"),
   ("FILE_DOCUMENT", "생성 File / Document", "Generated File / Document", "Agent 가 결과물로 생성하는 File·문서", "보고서·문서 File 생성"),
 ]),
 ("E4", "PA-GA", [
   ("USER_AUTHORITY", "사용자 위임 권한", "User-delegated Authority", "사용자가 Agent 에 위임한 작업·자원 접근 권한", "사용자 Calendar 수정 권한"),
   ("SERVICE_APP_AUTHORITY", "Service / App 권한", "Service / App Authority", "Service·App·Connector 자체에 부여된 권한", "Slack App scope"),
   ("ADMIN_ELEVATED_AUTHORITY", "관리자 / 상위 권한", "Admin / Elevated Authority", "일반 사용자보다 높은 관리·특수 작업 권한", "Admin 기능 사용"),
 ]),
 ("E4", "PA-CT", [
   ("ACCESS_OAUTH_TOKEN", "Access / OAuth Token", "Access / OAuth Token", "API·서비스 접근에 사용하는 Access·OAuth·Refresh Token", "OAuth Token 사용"),
   ("API_SECRET_KEY", "API / Secret Key", "API / Secret Key", "API 또는 Service 인증에 사용되는 Key·Secret", "API Key"),
   ("PASSWORD_CREDENTIAL", "Password / Credential", "Password / Credential", "Password 기반 계정 인증정보", "사용자 Password"),
   ("SESSION_COOKIE", "Session / Cookie", "Session / Cookie", "기존 인증상태를 유지·재사용하는 Session 정보", "로그인 Cookie"),
   ("CERT_PRIVATE_KEY", "Certificate / Private Key", "Certificate / Private Key", "Certificate·Private Key 기반 인증정보", "Client Certificate"),
 ]),
 ("E4", "PA-ACB", [
   ("AUTHENTICATION_CONTROL", "인증 통제", "Authentication Control", "사용자·Service 의 신원을 확인하는 통제 지점", "Login/Auth 단계"),
   ("AUTHORIZATION_SCOPE_CONTROL", "권한 / Scope 통제", "Authorization / Scope Control", "허용된 작업·자원 범위를 확인하는 통제", "Permission·OAuth Scope"),
   ("OBJECT_ACCESS_CONTROL", "객체 단위 접근통제", "Object-level Access Control", "특정 Resource 의 소유·접근 가능 여부를 확인하는 통제", "다른 사용자 Resource 접근 제한"),
   ("APPROVAL_GATE", "승인 단계", "Approval Gate", "민감 작업 수행 전에 필요한 사람·시스템 승인 단계", "송금 전 confirmation"),
 ]),
 ("E5", "DEX-UBD", [
   ("CUSTOMER_CRM", "고객 / CRM 데이터", "Customer / CRM Data", "고객·영업·CRM 관련 정보", "고객 이름·고객번호"),
   ("COMMUNICATION_CONTENT", "커뮤니케이션 내용", "Communication Content", "Email·Message·Chat 등 사람 간 커뮤니케이션 내용", "Email 본문·Slack 메시지"),
   ("WORK_DOCUMENT", "업무 문서", "Work Document", "조직 업무 과정에서 생성·사용되는 File·Document", "내부 보고서"),
   ("CALENDAR_SCHEDULE", "Calendar / 일정 데이터", "Calendar / Schedule Data", "일정·Meeting·참석자·시간 관련 정보", "임원 일정"),
   ("CONTACT_PROFILE", "Contact / Profile 데이터", "Contact / Profile Data", "연락처·사용자 Profile·개인 기본정보", "이름·주소·전화번호"),
   ("ACCOUNT_PAYMENT", "Account / Payment 데이터", "Account / Payment Data", "계좌·결제수단·잔액 등 금융계정 관련 정보", "IBAN·잔액"),
   ("TRANSACTION", "거래 데이터", "Transaction Data", "송금·결제·거래 내역", "최근 송금 내역"),
   ("ORDER_RESERVATION", "주문 / 예약 데이터", "Order / Reservation Data", "상품·서비스의 주문·예약 관련 정보", "호텔·항공 예약"),
   ("PROJECT_WORK_ITEM", "Project / 업무항목 데이터", "Project / Work-item Data", "Project·Issue·Ticket·Task 등 업무관리 정보", "Jira Ticket"),
 ]),
 ("E5", "DEX-CS", [
   ("TOKEN_SESSION", "Token / Session Credential", "Token / Session Credential", "Access Token·Session·Cookie 등 인증상태 정보", "로그인 Token"),
   ("API_SECRET_KEY", "API / Secret Key", "API / Secret Key", "API·Service 에서 사용하는 Key·Secret", "API Key"),
   ("PASSWORD_CREDENTIAL", "Password / Credential", "Password / Credential", "사용자 또는 서비스의 Password 기반 Credential", "로그인 Password"),
   ("PRIVATE_KEY_CERT", "Private Key / Certificate", "Private Key / Certificate", "인증·암호화에 사용되는 Private Key·Certificate", "SSH Private Key"),
 ]),
 ("E5", "DEX-SRD", [
   ("SYSTEM_CONFIG_FILE", "System / Configuration File", "System / Configuration File", "시스템·Application 동작을 위한 File·Configuration", "config.yaml"),
   ("ENVIRONMENT_VARIABLE", "환경변수", "Environment Variable", "Process 실행환경에 설정된 환경변수", "API_KEY 환경변수"),
   ("MEMORY_PROCESS", "Memory / Process 데이터", "Memory / Process Data", "실행 중인 Process·Memory 와 관련된 정보", "Process Memory"),
   ("LOG", "Log", "Log", "시스템·Application·Agent 가 기록한 실행 Log", "Access Log"),
   ("CLIPBOARD", "Clipboard", "Clipboard", "사용자·시스템 Clipboard 에 임시 저장된 내용", "복사된 Password"),
   ("SOURCE_REPOSITORY", "Source Code / Repository", "Source Code / Repository", "프로그램 Source Code 와 Repository 내용", "내부 Git Repository"),
   ("BROWSER_LOCAL_SESSION", "Browser / Local Session 데이터", "Browser / Local Session Data", "Browser History·Local Storage·Browser Session 등의 정보", "Local Storage Token"),
 ]),
 ("E6", "INV-AT", [
   ("COMMUNICATION_TOOL", "Communication Tool", "Communication Tool", "Email·Message 등 커뮤니케이션 기능을 제공하는 Tool", "Email/Slack Tool"),
   ("CRM_ERP", "CRM / ERP Tool", "CRM / ERP Tool", "고객·업무·기업 Resource 를 관리하는 Application Tool", "CRM Connector"),
   ("CONNECTOR_API", "Connector / API", "Connector / API", "외부 Application·Service 기능을 연결하는 일반 API·Connector", "SaaS Connector"),
   ("MCP_REMOTE_TOOL", "MCP / Remote Tool", "MCP / Remote Tool", "MCP 또는 Remote Function 형태로 제공되는 Tool", "MCP Tool"),
   ("FILE_STORAGE", "File / Storage Tool", "File / Storage Tool", "File·Document·Cloud Storage 를 조회·변경하는 Tool", "Drive Tool"),
   ("CALENDAR_SCHEDULING", "Calendar / Scheduling Tool", "Calendar / Scheduling Tool", "일정·Meeting·Schedule 을 관리하는 Tool", "Calendar Tool"),
   ("PAYMENT_FINANCIAL", "Payment / Financial Tool", "Payment / Financial Tool", "계좌·결제·송금 등 금융 기능을 수행하는 Tool", "send_money"),
   ("RESERVATION_ORDER", "Reservation / Order Tool", "Reservation / Order Tool", "상품·서비스 예약·주문을 관리하는 Tool", "호텔 예약 Tool"),
   ("SEARCH_RETRIEVAL", "Search / Retrieval Tool", "Search / Retrieval Tool", "외부·내부 정보를 검색·검색결과로 반환하는 Tool", "RAG Search"),
   ("DATABASE_TOOL", "Database Tool", "Database Tool", "Database 의 Record 를 조회·변경하는 Tool", "SQL/DB Connector"),
 ]),
 ("E6", "INV-SCU", [
   ("COMPUTER_USE_GUI", "Computer-Use / GUI", "Computer-Use / GUI", "화면·Mouse·Keyboard 등 GUI 환경을 직접 제어하는 기능", "Desktop 클릭"),
   ("BROWSER_CONTROL", "Browser Control", "Browser Control", "Browser 를 직접 열고 탐색·입력·클릭하는 기능", "Browser automation"),
   ("TERMINAL_CLI", "Terminal / CLI", "Terminal / CLI", "OS Terminal 또는 Command-line 환경을 사용하는 기능", "Terminal Tool"),
   ("FILE_SYSTEM", "File System Tool", "File System Tool", "실행환경의 File System 을 직접 읽거나 변경하는 기능", "Local filesystem"),
   ("CODE_IDE", "Code / IDE Tool", "Code / IDE Tool", "Source Code 작성·편집·실행을 지원하는 개발환경 기능", "IDE Tool"),
   ("SSH_REMOTE_SHELL", "SSH / Remote Shell", "SSH / Remote Shell", "Remote System 에 Shell 수준으로 접근하는 기능", "SSH 접속"),
 ]),
 ("E6", "INV-CAI", [
   ("ADMIN_MANAGEMENT", "Admin / Management Interface", "Admin / Management Interface", "Agent·Application·System 의 운영 설정을 관리하는 기능", "Admin Console/API"),
   ("CLOUD_CONSOLE", "Cloud Console", "Cloud Console", "Cloud Resource 를 생성·변경·관리하는 기능", "AWS/GCP Console"),
   ("IDENTITY_MANAGEMENT", "Identity Management", "Identity Management", "User·Role·Permission 등 Identity 를 관리하는 기능", "IAM Tool"),
   ("DEPLOYMENT_INFRA", "Deployment / Infrastructure Tool", "Deployment / Infrastructure Tool", "Software 배포·Infrastructure 구성·변경 기능", "CI/CD·IaC"),
 ]),
 ("E7", "EXEC-SE", [
   ("PYTHON", "Python 실행", "Python Execution", "Python Code 가 실제 Runtime 에서 실행", "Python Script 실행"),
   ("JAVASCRIPT", "JavaScript 실행", "JavaScript Execution", "JavaScript Code 가 실제 실행환경에서 실행", "Node.js 실행"),
   ("SHELL_SCRIPT", "Shell Script 실행", "Shell Script Execution", "Bash·sh 등의 Script 파일 또는 Script Code 가 실행", ".sh 실행"),
   ("POWERSHELL_SCRIPT", "PowerShell Script 실행", "PowerShell Script Execution", "PowerShell Script 가 실행", ".ps1 실행"),
   ("SQL_SCRIPT", "SQL / Query Script 실행", "SQL / Query Script Execution", "SQL 등의 Query Script 가 실제 Database Engine 에서 실행", "UPDATE SQL 실행"),
   ("NOTEBOOK_CELL", "Notebook / Code Cell 실행", "Notebook / Code Cell Execution", "Notebook 환경의 Code Cell 이 실행", "Jupyter Cell 실행"),
   ("EXECUTABLE_BINARY", "Executable / Binary 실행", "Executable / Binary Execution", "Binary·Executable 프로그램이 실제 실행", "다운로드 Binary 실행"),
 ]),
 ("E7", "EXEC-SSE", [
   ("SHELL_OS_COMMAND", "Shell / OS Command", "Shell / OS Command", "Shell 또는 OS 의 개별 System Command", "rm, chmod, curl"),
   ("POWERSHELL_WINDOWS_COMMAND", "PowerShell / Windows Command", "PowerShell / Windows Command", "Windows·PowerShell 환경의 개별 System Command", "PowerShell command"),
   ("PACKAGE_MANAGEMENT", "Package Management Command", "Package Management Command", "Package 설치·삭제·변경을 수행하는 Command", "pip install, apt"),
   ("CONTAINER_ORCHESTRATION", "Container / Orchestration Command", "Container / Orchestration Command", "Container·Cluster 환경을 제어하는 Command", "Docker·Kubernetes"),
 ]),
 ("E8", "SCP-SC", [
   ("FILE_SHARING", "File / 공유 상태", "File / Sharing State", "File 의 생성·수정·삭제 또는 외부 공유상태", "File 삭제·공유"),
   ("CONFIGURATION", "Configuration 상태", "Configuration State", "Application·System Configuration 값의 상태", "설정 변경"),
   ("CALENDAR_SCHEDULE", "Calendar / Schedule 상태", "Calendar / Schedule State", "일정·Meeting·Schedule 의 생성·수정·삭제 상태", "일정 삭제"),
   ("DEVICE_SYSTEM", "Device / System 상태", "Device / System State", "실제 장치·OS·System 의 동작 또는 설정 상태", "장치 제어"),
   ("PRIVILEGE_ROLE", "Privilege / Role 상태", "Privilege / Role State", "User·Service 의 권한·Role 상태", "Admin Role 부여"),
   ("USER_ACCOUNT", "User / Account 상태", "User / Account State", "User Account·Profile·Credential 관련 저장 상태", "Password·주소 변경"),
   ("COMMUNICATION", "Communication 상태", "Communication State", "Email·Message 등 커뮤니케이션 객체의 저장 상태", "Message 삭제"),
   ("TRANSACTION_PAYMENT", "Transaction / Payment 상태", "Transaction / Payment State", "송금·거래·결제의 생성·수정 상태", "송금 실행"),
   ("RESERVATION_ORDER", "Reservation / Order 상태", "Reservation / Order State", "예약·주문의 생성·수정·취소 상태", "호텔 예약 변경"),
   ("CHANNEL_MEMBERSHIP", "Channel / Membership 상태", "Channel / Membership State", "Channel·Group 의 구성원·멤버십 상태", "사용자 Channel 추가"),
   ("WORKFLOW_TASK", "Workflow / Task 상태", "Workflow / Task State", "Workflow·Task·Job 등의 생성·수정·실행예약 상태", "Task 생성"),
 ]),
 ("E8", "SCP-CC", [
   ("CONVERSATION_SESSION_CONTEXT", "Conversation / Session Context", "Conversation / Session Context", "이전 Turn 의 정보가 같은 Conversation·Session 의 이후 판단에 계속 사용", "Turn 1 정보가 Turn 4 에 영향"),
   ("LONG_TERM_MEMORY", "Long-term Memory", "Long-term Memory", "Session 을 넘어 저장되고 이후 다시 조회되는 Agent Memory", "다음 Session 에서 기억 재사용"),
   ("RAG_KNOWLEDGE_BASE", "RAG / Knowledge Base", "RAG / Knowledge Base", "지속 저장되어 이후 Retrieval 에 사용되는 지식 저장소", "저장 문서가 후속 검색에 반환"),
   ("PERSISTENT_PROMPT_CONFIG", "지속 Prompt / Configuration", "Persistent Prompt / Configuration", "변경된 Prompt·Configuration 이 이후 Agent 실행에도 계속 적용", "다음 실행에도 같은 설정 사용"),
   ("TRAINING_FINETUNING_DATA", "Training / Fine-tuning Data", "Training / Fine-tuning Data", "이후 Model 학습·Fine-tuning 에 사용되어 Model 동작에 장기 영향을 주는 데이터", "Fine-tuning Dataset"),
 ]),
 ("E9", "ID-RG", [
   ("TEXT_RESPONSE", "Text / Response", "Text / Response", "Agent 가 생성하는 일반 Text·Chat Response", "고객정보 포함 답변"),
   ("FILE_DOCUMENT", "File / Document", "File / Document", "Agent 가 생성하는 File·Document 결과", "보고서 File"),
   ("CODE_SCRIPT", "Code / Script", "Code / Script", "Agent 가 결과물로 생성하는 Code·Script", "Python Code"),
   ("IMAGE_MEDIA", "Image / Media", "Image / Media", "Image·Graph·기타 시각적 결과", "데이터 Graph"),
   ("STRUCTURED_DATA", "Structured Data", "Structured Data", "JSON·CSV·Table 등 구조화된 데이터 결과", "고객정보 CSV"),
   ("LOG_NOTIFICATION", "Log / Notification", "Log / Notification", "Log·Alert·Notification 형태로 생성되는 결과", "내부정보 Notification"),
 ]),
 ("E9", "ID-ER", [
   ("EMAIL_EXTERNAL_MESSAGE", "Email / 외부 Message", "Email / External Message", "별도의 외부 Email·Message 수신자에게 정보를 전달", "공격자 Email 로 전송"),
   ("EXTERNAL_API_HTTP", "외부 API / HTTP Endpoint", "External API / HTTP Endpoint", "HTTP·API 요청으로 외부 Server·Endpoint 에 정보를 전달", "외부 POST 요청"),
   ("EXTERNAL_SERVICE_RECIPIENT", "외부 Service / Recipient", "External Service / Recipient", "업무·Application 기능을 이용해 외부 계정·수신자에게 데이터를 전달", "거래 Memo 를 외부 수취인에게 전달"),
   ("WEB_RENDERING_RESOURCE", "Web Rendering / 외부 Resource", "Web Rendering / External Resource", "Rendering·외부 Resource 로딩 과정에서 정보가 외부로 노출", "외부 Image URL 요청"),
   ("EXTERNAL_STORAGE_UPLOAD", "외부 Storage / File Upload", "External Storage / File Upload", "외부 Storage·Repository 등에 Data·File 을 기록", "외부 Drive Upload"),
   ("FILE_SHARE_PUBLIC_LINK", "File Share / Public Link", "File Share / Public Link", "외부에서 접근 가능한 공유 Link 또는 공개 권한을 생성", "Public Share Link"),
 ]),
 ("E10", "HD-UI", [
   ("LINK_NAVIGATION", "Link 이동 / 클릭", "Link Navigation / Click", "사용자가 Agent 가 제공한 Link 를 열거나 클릭", "외부 URL 클릭"),
   ("INFORMATION_ENTRY", "정보 입력", "Information Entry", "사용자가 Form·Chat·Page 등에 정보를 직접 입력", "Password 입력"),
   ("FILE_DOWNLOAD_OPEN", "File 다운로드 / 열기", "File Download / Open", "사용자가 File 을 다운로드하거나 직접 열음", "첨부 File 열기"),
   ("INSTALL_RUN", "설치 / 실행", "Install / Run", "사용자가 Software·Script·Application 을 설치 또는 실행", "프로그램 실행"),
 ]),
 ("E10", "HD-UAD", [
   ("COMMAND_EXECUTION_APPROVAL", "명령 / 실행 승인", "Command / Execution Approval", "사용자가 작업·명령의 실제 실행을 승인", "위험 Command 승인"),
   ("PRIVILEGE_PERMISSION_APPROVAL", "권한 / Permission 승인", "Privilege / Permission Approval", "사용자가 Agent·App 에 추가 권한을 부여", "Drive 권한 승인"),
   ("AUTH_MFA_APPROVAL", "인증 / MFA 승인", "Authentication / MFA Approval", "사용자가 MFA·Authentication 요청을 승인", "MFA Push 승인"),
   ("OAUTH_APP_APPROVAL", "OAuth / App 연결 승인", "OAuth / App Connection Approval", "사용자가 외부 Application 연결과 Scope 를 승인", "OAuth consent"),
   ("PAYMENT_TRANSFER_APPROVAL", "결제 / 송금 승인", "Payment / Transfer Approval", "사용자가 금융 작업을 최종 승인", "송금 확인"),
   ("FILE_SHARE_PUBLICATION_APPROVAL", "File 공유 / 공개 승인", "File Share / Publication Approval", "사용자가 File·Data 의 외부 공유·공개를 승인", "외부공유 확인"),
   ("SECURITY_WARNING_OVERRIDE", "보안 경고 무시 / 진행", "Security Warning Override", "보안 경고를 확인하고도 사용자가 계속 진행", "Browser 경고 무시"),
   ("ADVICE_DECISION_TRUST", "조언 / 의사결정 신뢰", "Advice / Decision Trust", "Agent 의 조언·추천·분석 결과를 신뢰하여 실제 의사결정", "잘못된 추천을 믿고 선택"),
 ]),
]


def build_matrix():
    m = {}
    for e, subcode, insts in MATRIX_SRC:
        if e not in m:
            e_ko, e_en, e_desc = ELEMENT_META[e]
            m[e] = {"name_ko": e_ko, "name_en": e_en, "description": e_desc, "subcategories": {}}
        s_ko, s_en, s_desc = SUBCAT_META[subcode]
        idict = {}
        for key, ko, en, desc, ex in insts:
            idict[f"{subcode}.{key}"] = {"name_ko": ko, "name_en": en, "description": desc, "example": ex}
        m[e]["subcategories"][subcode] = {"name_ko": s_ko, "name_en": s_en, "description": s_desc, "instances": idict}
    return m


# ══════════════════════════════════════════════════════════════════════════════
# ATTACK_GOALS (G1~G9)  · terminal = goal 성립(완료) Element
# ══════════════════════════════════════════════════════════════════════════════
ATTACK_GOALS = {
 "G1": {"name": "데이터 유출",                    "sequence": ["E1","E3","E6","E5","E9"], "terminal": "E9"},
 "G2": {"name": "코드·명령 실행",                 "sequence": ["E1","E3","E6","E7"],      "terminal": "E7"},
 "G3": {"name": "사용자 유도·행동 조작",          "sequence": ["E1","E3","E10"],          "terminal": "E10"},
 "G4": {"name": "지속 상태 오염·유지",            "sequence": ["E1","E8","E3","E9"],      "terminal": "E8"},
 "G5": {"name": "Credential·접근권한 침해",       "sequence": ["E4","E5","E6"],           "terminal": "E6"},
 "G6": {"name": "비의도 Tool 호출·민감작업",      "sequence": ["E1","E3","E6","E8"],      "terminal": "E8"},
 "G7": {"name": "데이터·시스템 파괴",             "sequence": ["E1/E2","E3","E6","E7","E8"],"terminal": "E8"},
 "G8": {"name": "Agent 동작·출력 무결성 침해",    "sequence": ["E2","E3"],                "terminal": "E3"},
 "G9": {"name": "명령·제어(C2)",                  "sequence": ["E1","E3","E9","E1"],      "terminal": "E9"},
}
GOALKEY2G = {
 "data_exfiltration": "G1", "code_execution": "G2", "user_manipulation": "G3", "persistent_state": "G4",
 "credential_abuse": "G5", "unintended_tool": "G6", "system_destruction": "G7", "supply_chain": "G8", "c2": "G9",
}

# ── 31 CS 분석본 (U1~U12 시퀀스) + 대표목표 ──────────────────────────────────
RAW_SEQUENCES = {
 "CS0016": [("U1","External/User Input"),("U3","Code Generation Influence"),("U6","Agent Tool/Plugin"),("U7","Code Execution"),("U5","Environment Variable")],
 "CS0020": [("U1","Web/URL"),("U3","Goal/Decision Influence"),("U12","Sensitive Information Elicitation")],
 "CS0021": [("U1","Web/URL"),("U3","Indirect Instruction"),("U9","Markdown/Image Output"),("U9","Rendering"),("U10","Network/HTTP Request")],
 "CS0024": [("U1","RAG/Retrieved Content"),("U8","RAG/Knowledge Base Persistence"),("U5","RAG/Knowledge Base"),("U3","Output/Response Influence"),("U9","Text/Response Output")],
 "CS0026": [("U1","RAG/Retrieved Content"),("U8","RAG/Knowledge Base Persistence"),("U3","Indirect Instruction"),("U6","Agent Tool/Plugin"),("U9","Text/Response Output"),("U12","Decision Influence")],
 "CS0029": [("U1","Document"),("U3","Indirect Instruction"),("U9","Markdown/Image Output"),("U9","Rendering"),("U10","Network/HTTP Request")],
 "CS0035": [("U1","RAG/Retrieved Content"),("U8","RAG/Knowledge Base Persistence"),("U5","Slack/Message"),("U3","Indirect Instruction"),("U9","Text/Response Output"),("U10","External URL/Attacker Endpoint")],
 "CS0036": [("U5","Process Memory"),("U5","Credential/Secret"),("U4","Credential/Token Use"),("U6","Backend/API"),("U8","Persistent Memory")],
 "CS0037": [("U1","Email"),("U3","Indirect Instruction"),("U5","CRM/Enterprise Data"),("U6","Email Tool"),("U10","Email")],
 "CS0038": [("U1","External/User Input"),("U3","Indirect Instruction"),("U8","Delayed Context"),("U6","Agent Tool/Plugin"),("U5","User/Personal Data")],
 "CS0039": [("U1","External/User Input"),("U3","Indirect Instruction"),("U6","Agent Tool/Plugin"),("U5","CRM/Enterprise Data"),("U10","Tool/Service-mediated Transfer")],
 "CS0040": [("U1","Connected-App Content"),("U3","Indirect Instruction"),("U8","Persistent Memory"),("U3","Output/Response Influence"),("U9","Text/Response Output")],
 "CS0041": [("U2","Rule/Config"),("U3","Code Generation Influence"),("U7","Script Execution")],
 "CS0045": [("U1","Tool Output"),("U3","Indirect Instruction"),("U6","MCP/Remote Tool"),("U7","Shell Command"),("U5","File/File System"),("U10","Network/HTTP Request")],
 "CS0046": [("U1","External/User Input"),("U3","Indirect Instruction"),("U6","Computer-Use/System Tool"),("U7","System Command"),("U11","File/Data Deletion")],
 "CS0047": [("U2","Rule/Config"),("U3","Embedded Instruction"),("U6","Computer-Use/System Tool"),("U7","System Command"),("U11","Cloud Resource Modification")],
 "CS0048": [("U6","Control Interface"),("U4","Authentication/Access-Control Bypass"),("U5","Credential/Secret"),("U6","Agent Tool/Plugin"),("U7","System Command"),("U4","Credential/Token Use")],
 "CS0049": [("U2","Skill"),("U3","Embedded Instruction"),("U12","User Confirmation/Approval"),("U7","Shell Command")],
 "CS0050": [("U1","Web/URL"),("U6","Control Interface"),("U4","Authentication/Access-Control Bypass"),("U7","Host Execution")],
 "CS0051": [("U1","External/User Input"),("U3","Indirect Instruction"),("U7","System Command"),("U8","Prompt/Context File Modification"),("U10","C2/Remote Endpoint")],
 "CS0052": [("U1","External/User Input"),("U3","Tool Argument Influence"),("U6","Internal Function"),("U7","Code Execution"),("U5","Cloud/System Resource"),("U11","Resource Consumption/System Impact")],
 "CS0053": [("U2","MCP/Remote Tool"),("U6","MCP/Remote Tool"),("U5","Email"),("U10","Tool/Service-mediated Transfer")],
 "CS0054": [("U2","MCP/Remote Tool"),("U3","Embedded Instruction"),("U6","MCP/Remote Tool"),("U5","File/File System"),("U10","Remote Service/API")],
 "CS0055": [("U1","Web/URL"),("U3","Goal/Decision Influence"),("U6","Computer-Use/System Tool"),("U5","Clipboard"),("U7","System Command"),("U11","File/System Modification")],
 "CS0059": [("U1","RAG/Retrieved Content"),("U3","Indirect Instruction"),("U5","User/Personal Data"),("U9","Markdown/Image Output"),("U9","Rendering"),("U10","Network/HTTP Request")],
 "CS0061": [("U1","External/User Input"),("U3","Tool Argument Influence"),("U6","Browser/Web Tool"),("U10","C2/Remote Endpoint"),("U1","Web/URL"),("U9","Text/Response Output")],
 "CS0062": [("U1","External/User Input"),("U3","Tool Argument Influence"),("U6","Agent Tool/Plugin"),("U7","Code Execution"),("U11","Resource Consumption/System Impact")],
 "CS0063": [("U1","Calendar"),("U8","Multi-turn Context"),("U4","Delegated Authority"),("U6","Connector"),("U11","Calendar Modification")],
 "CS0064": [("U2","Model Artifact"),("U3","Prompt Construction Influence"),("U6","Agent Tool/Plugin")],
 "CS0066": [("U1","External/User Input"),("U8","Persistent Memory"),("U3","Indirect Instruction"),("U6","Connector"),("U10","Tool/Service-mediated Transfer")],
 "CS0067": [("U1","External/User Input"),("U3","Indirect Instruction"),("U6","Agent Tool/Plugin"),("U5","Credential/Secret"),("U9","Generated Code/Script"),("U10","Network/HTTP Request")],
}
CASE_GOAL = {
 "CS0021":"data_exfiltration","CS0029":"data_exfiltration","CS0035":"data_exfiltration","CS0037":"data_exfiltration",
 "CS0039":"data_exfiltration","CS0045":"data_exfiltration","CS0053":"data_exfiltration","CS0054":"data_exfiltration",
 "CS0059":"data_exfiltration","CS0066":"data_exfiltration","CS0067":"data_exfiltration",
 "CS0016":"code_execution","CS0049":"code_execution","CS0050":"code_execution","CS0052":"code_execution","CS0055":"code_execution","CS0062":"code_execution",
 "CS0020":"user_manipulation","CS0026":"user_manipulation",
 "CS0024":"persistent_state","CS0040":"persistent_state",
 "CS0036":"credential_abuse","CS0048":"credential_abuse",
 "CS0038":"unintended_tool","CS0063":"unintended_tool",
 "CS0046":"system_destruction","CS0047":"system_destruction",
 "CS0041":"supply_chain","CS0064":"supply_chain",
 "CS0051":"c2","CS0061":"c2",
}

ELEM_MAP = {"U1":"E1","U2":"E2","U3":"E3","U4":"E4","U5":"E5","U6":"E6","U7":"E7","U8":"E8","U9":"E9","U10":"E9","U11":"E8","U12":"E10"}

# ── (U, 기존라벨) → 새 136 Instance ID  크로스워크 ("@GOAL"=목표의존, goal_e3 로 해소) ──
INST_MAP = {
 ("U1","External/User Input"):"ENT-DI.CHAT", ("U1","Web/URL"):"ENT-II.WEB_URL", ("U1","RAG/Retrieved Content"):"ENT-II.RETRIEVED_CONTENT",
 ("U1","Document"):"ENT-II.FILE", ("U1","Tool Output"):"ENT-II.RETRIEVED_CONTENT", ("U1","Email"):"ENT-II.EMAIL",
 ("U1","Connected-App Content"):"ENT-II.APPLICATION_RECORD", ("U1","Calendar"):"ENT-II.CALENDAR_EVENT",
 ("U2","Rule/Config"):"INT-CR.CONFIGURATION", ("U2","Skill"):"INT-EC.SKILL_FUNCTION", ("U2","MCP/Remote Tool"):"INT-EC.MCP_REMOTE_TOOL", ("U2","Model Artifact"):"INT-MT.MODEL_CHECKPOINT",
 ("U3","Code Generation Influence"):"CM-GM.CODE_SCRIPT", ("U3","Goal/Decision Influence"):"CM-AM.GOAL_PLAN",
 ("U3","Output/Response Influence"):"CM-GM.RESPONSE_CONTENT", ("U3","Prompt Construction Influence"):"CM-GM.PROMPT_INSTRUCTION",
 ("U3","Tool Argument Influence"):"CM-AM.TOOL_ARGUMENT", ("U3","Indirect Instruction"):"@GOAL", ("U3","Embedded Instruction"):"@GOAL",
 ("U4","Credential/Token Use"):"PA-CT.ACCESS_OAUTH_TOKEN", ("U4","Authentication/Access-Control Bypass"):"PA-ACB.AUTHENTICATION_CONTROL", ("U4","Delegated Authority"):"PA-GA.USER_AUTHORITY",
 ("U5","Environment Variable"):"DEX-SRD.ENVIRONMENT_VARIABLE", ("U5","RAG/Knowledge Base"):"DEX-UBD.WORK_DOCUMENT", ("U5","CRM/Enterprise Data"):"DEX-UBD.CUSTOMER_CRM",
 ("U5","User/Personal Data"):"DEX-UBD.CONTACT_PROFILE", ("U5","Process Memory"):"DEX-SRD.MEMORY_PROCESS", ("U5","Credential/Secret"):"DEX-CS.API_SECRET_KEY",
 ("U5","File/File System"):"DEX-SRD.SYSTEM_CONFIG_FILE", ("U5","Slack/Message"):"DEX-UBD.COMMUNICATION_CONTENT", ("U5","Cloud/System Resource"):"DEX-SRD.SYSTEM_CONFIG_FILE",
 ("U5","Clipboard"):"DEX-SRD.CLIPBOARD", ("U5","Email"):"DEX-UBD.COMMUNICATION_CONTENT",
 ("U6","Agent Tool/Plugin"):"INV-AT.CONNECTOR_API", ("U6","Email Tool"):"INV-AT.COMMUNICATION_TOOL", ("U6","Computer-Use/System Tool"):"INV-SCU.COMPUTER_USE_GUI",
 ("U6","Control Interface"):"INV-CAI.ADMIN_MANAGEMENT", ("U6","Internal Function"):"INV-AT.CONNECTOR_API", ("U6","Browser/Web Tool"):"INV-SCU.BROWSER_CONTROL",
 ("U6","Connector"):"INV-AT.CONNECTOR_API", ("U6","Backend/API"):"INV-AT.CONNECTOR_API", ("U6","MCP/Remote Tool"):"INV-AT.MCP_REMOTE_TOOL",
 ("U7","Code Execution"):"EXEC-SE.PYTHON", ("U7","Script Execution"):"EXEC-SE.SHELL_SCRIPT", ("U7","Shell Command"):"EXEC-SSE.SHELL_OS_COMMAND",
 ("U7","System Command"):"EXEC-SSE.SHELL_OS_COMMAND", ("U7","Host Execution"):"EXEC-SSE.SHELL_OS_COMMAND",
 ("U8","RAG/Knowledge Base Persistence"):"SCP-CC.RAG_KNOWLEDGE_BASE", ("U8","Delayed Context"):"SCP-CC.CONVERSATION_SESSION_CONTEXT", ("U8","Persistent Memory"):"SCP-CC.LONG_TERM_MEMORY",
 ("U8","Multi-turn Context"):"SCP-CC.CONVERSATION_SESSION_CONTEXT", ("U8","Prompt/Context File Modification"):"SCP-CC.PERSISTENT_PROMPT_CONFIG",
 ("U9","Markdown/Image Output"):"ID-RG.IMAGE_MEDIA", ("U9","Rendering"):"ID-ER.WEB_RENDERING_RESOURCE", ("U9","Text/Response Output"):"ID-RG.TEXT_RESPONSE", ("U9","Generated Code/Script"):"ID-RG.CODE_SCRIPT",
 ("U10","Network/HTTP Request"):"ID-ER.EXTERNAL_API_HTTP", ("U10","External URL/Attacker Endpoint"):"ID-ER.EXTERNAL_API_HTTP", ("U10","Email"):"ID-ER.EMAIL_EXTERNAL_MESSAGE",
 ("U10","Tool/Service-mediated Transfer"):"ID-ER.EXTERNAL_SERVICE_RECIPIENT", ("U10","Remote Service/API"):"ID-ER.EXTERNAL_API_HTTP", ("U10","C2/Remote Endpoint"):"ID-ER.EXTERNAL_API_HTTP",
 ("U11","File/Data Deletion"):"SCP-SC.FILE_SHARING", ("U11","Cloud Resource Modification"):"SCP-SC.DEVICE_SYSTEM", ("U11","Resource Consumption/System Impact"):"SCP-SC.DEVICE_SYSTEM",
 ("U11","File/System Modification"):"SCP-SC.FILE_SHARING", ("U11","Calendar Modification"):"SCP-SC.CALENDAR_SCHEDULE",
 ("U12","Sensitive Information Elicitation"):"HD-UI.INFORMATION_ENTRY", ("U12","Decision Influence"):"HD-UAD.ADVICE_DECISION_TRUST", ("U12","User Confirmation/Approval"):"HD-UAD.COMMAND_EXECUTION_APPROVAL",
}


def goal_e3(goalkey):
    """Indirect/Embedded Instruction 을 CS 대표목표에 맞춰 CM 인스턴스로 해소 (신 taxonomy)."""
    if goalkey == "unintended_tool":
        return "CM-AM.TOOL_SELECTION"
    return "CM-AM.GOAL_PLAN"


# ══════════════════════════════════════════════════════════════════════════════
def load_atlas():
    import yaml
    doc = yaml.safe_load(ATLAS.read_text(encoding="utf-8"))
    cases, rels = doc["case-studies"], doc["relationships"]
    out = {}
    for cid in RAW_SEQUENCES:
        full = f"AML.{cid}"
        c = cases[full]
        emp = sorted(rels.get(full, {}).get("employs", []), key=lambda x: x.get("step-id", ""))
        steps = [{"description": x["description"].strip(), "technique": x["target"]} for x in emp]
        out[cid] = {"name": c["name"], "description": c["description"].strip(), "attack_steps": steps}
    return out


def build_case_studies():
    atlas = load_atlas()
    valid = {iid for e in build_matrix().values() for s in e["subcategories"].values() for iid in s["instances"]}
    cs_out = {}
    for cid, raw in RAW_SEQUENCES.items():
        goalkey = CASE_GOAL[cid]
        seq, insts = [], []
        for u, sub in raw:
            e = ELEM_MAP[u]
            if not seq or seq[-1] != e:
                seq.append(e)
            iid = INST_MAP[(u, sub)]
            if iid == "@GOAL":
                iid = goal_e3(goalkey)
            if iid not in valid:
                raise SystemExit(f"[크로스워크 오류] {cid}: {(u,sub)} → {iid} 는 THREAT_MATRIX 에 없음")
            insts.append(iid)
        a = atlas[cid]
        cs_out[f"AML.{cid}"] = {"name": a["name"], "description": a["description"], "attack_steps": a["attack_steps"],
                               "attack_goal": GOALKEY2G[goalkey], "sequence": seq, "instances": insts}
    return cs_out


_HEADER = (
 "# ============================================================================\n"
 "# SPECTRA Threat Knowledge  (자동생성: _generate.py · 직접 편집 금지)\n"
 "# THREAT_MATRIX: E1~E10 / 24 Subcategory / 136 Instance {name_ko,name_en,description,example}\n"
 "# CASE_STUDIES : 31 ATLAS CS   ·   ATTACK_GOALS: G1~G9\n"
 "# ============================================================================\n"
)


def emit():
    import yaml
    K = {"THREAT_MATRIX": build_matrix(), "ATTACK_GOALS": ATTACK_GOALS, "CASE_STUDIES": build_case_studies()}
    dump = yaml.safe_dump(K, allow_unicode=True, sort_keys=False, default_flow_style=False, width=1000, indent=2)
    (HERE / "threat_knowledge.yaml").write_text(_HEADER + dump, encoding="utf-8")
    n = sum(len(s["instances"]) for e in K["THREAT_MATRIX"].values() for s in e["subcategories"].values())
    print(f"emit → threat_knowledge.yaml  (Instances {n}, CASE_STUDIES {len(K['CASE_STUDIES'])})")


def validate():
    import yaml
    K = yaml.safe_load((HERE / "threat_knowledge.yaml").read_text(encoding="utf-8"))
    TM, CSD, AG = K["THREAT_MATRIX"], K["CASE_STUDIES"], K["ATTACK_GOALS"]
    ok = True
    def chk(c, m):
        nonlocal ok; print(("  OK  " if c else " FAIL ") + m); ok = ok and c
    n_e = len(TM); n_sub = sum(len(e["subcategories"]) for e in TM.values())
    all_inst = {iid for e in TM.values() for s in e["subcategories"].values() for iid in s["instances"]}
    chk(n_e == 10, f"Elements = {n_e} (기대 10)")
    chk(n_sub == 24, f"Subcategories = {n_sub} (기대 24)")
    print(f"  ..  Instances = {len(all_inst)} (숫자는 목표 아님)")
    chk(len(CSD) == 31, f"Case Studies = {len(CSD)} (기대 31)")
    chk(len(AG) == 9, f"Attack Goals = {len(AG)} (기대 9)")
    bad_i = [(c, i) for c, v in CSD.items() for i in v["instances"] if i not in all_inst]
    chk(not bad_i, f"CASE_STUDIES.instances 참조정합 (미존재 {len(bad_i)})" + (f" {bad_i[:3]}" if bad_i else ""))
    valid_e = set(TM) | {"E1/E2"}
    bad_seq = [(c, s) for c, v in CSD.items() for s in v["sequence"] if s not in valid_e] + \
              [(g, s) for g, v in AG.items() for s in v["sequence"] if s not in valid_e]
    chk(not bad_seq, f"sequence E번호 범위 (이상 {len(bad_seq)})")
    print("\n" + ("=== ALL PASS ===" if ok else "=== FAIL ==="))
    return ok


if __name__ == "__main__":
    emit(); print(); validate()
