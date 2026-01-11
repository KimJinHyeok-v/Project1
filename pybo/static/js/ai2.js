/* static/js/ai2.js */

(() => {
  // ---------- shared utils ----------
  function $(id){ return document.getElementById(id); }

  function appendMsg(logEl, role, text){
    const row = document.createElement("div");
    row.className = "ai2-msg " + (
      role === "user" ? "ai2-msg--user" :
      role === "system" ? "ai2-msg--system" :
      "ai2-msg--bot"
    );

    const bubble = document.createElement("div");
    bubble.className = "ai2-bubble";
    bubble.textContent = text;

    row.appendChild(bubble);
    logEl.appendChild(row);
    logEl.scrollTop = logEl.scrollHeight;
    return bubble;
  }

  // 보고서처럼 "긴 본문"을 예쁘게 넣기(white-space 유지 + max-width CSS로 100% 덮어씀)
  function appendReport(logEl, text){
    const row = document.createElement("div");
    row.className = "ai2-msg ai2-msg--bot";

    const bubble = document.createElement("div");
    bubble.className = "ai2-bubble";

    const pre = document.createElement("pre");
    pre.className = "b2b-report-pre"; // (CSS에서 #b2b_report_log pre 오버라이드 넣었으면 없어도 됨)
    pre.textContent = text;

    bubble.appendChild(pre);
    row.appendChild(bubble);
    logEl.appendChild(row);
    logEl.scrollTop = logEl.scrollHeight;
  }

  function setB2BMeta({ district, yearFrom, yearTo, hintText }){
    const hintEl = $("b2b_result_hint");
    const tagEl  = $("b2b_result_tag");

    if(hintEl) hintEl.textContent = hintText || "";
    if(tagEl){
      if(district && yearFrom && yearTo){
        tagEl.textContent = `${district} / ${yearFrom}~${yearTo} / 취약지역 집중지원`;
      }else{
        tagEl.textContent = "";
      }
    }
  }

  // ---------- GEO (B2C) ----------
  let CURRENT_POS = null;

  function setGeo(state, text){
    const dot = $("geoDot");
    const label = $("geoText");
    if(!dot || !label) return;
    label.textContent = text || "";
    dot.classList.remove("ok", "bad", "wait");
    if(state === "ok") dot.classList.add("ok");
    if(state === "bad") dot.classList.add("bad");
    if(state === "wait") dot.classList.add("wait");

  }

  function getLocationOnce(){
    return new Promise((resolve, reject) => {
      if(CURRENT_POS) return resolve(CURRENT_POS);
      if(!navigator.geolocation) return reject(new Error("위치 미지원"));

      setGeo("wait", "위치 확인 중…");
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          CURRENT_POS = { lat: pos.coords.latitude, lon: pos.coords.longitude };
          setGeo("ok", "위치 확인됨");
          resolve(CURRENT_POS);
        },
        (err) => {
          setGeo("bad", "위치 권한 필요");
          reject(err);
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
      );
    });
  }



    // ===== 직전 추천 목록 저장(2번 상세용) =====
  let LAST_CENTERS = [];

  function parseDetailIndex(text){
    const s = (text || "").replace(/\s+/g, "");
    const m = s.match(/(\d+)번(상세|정보|자세|자세히)/);
    if(!m) return null;
    const idx = parseInt(m[1], 10);
    return Number.isFinite(idx) ? idx : null;
  }

  // "위치가 꼭 필요한 요청"만 골라서 위치 강제
  function needsGeo(msg){
    const s = (msg || "").replace(/\s+/g, "");
    // 추천류 / 내 위치류 / km 반경 언급 -> 위치 필요
    if (/(추천|가까|근처|제일가까|가장가까|먼|제일먼|가장먼)/.test(s)) return true;
    if (/(내가어디|내위치|지금어디|현재위치)/.test(s)) return true;
    if (/\d+(\.\d+)?km/i.test(s)) return true;
    return false;
  }

  // 추천 응답일 때만 LAST_CENTERS 갱신(조회 응답 centers로 덮어쓰기 방지)
  function looksLikeRecoResponse(data){
    try{
      const text = (data?.text || "").trim();
      const startsReco = /^1\)\s/.test(text);   // "1) ..." 형태면 추천
      const hasDistance = Array.isArray(data?.centers) && data.centers.some(c => c && typeof c.distance_km !== "undefined");
      return (startsReco || hasDistance) && (Array.isArray(data?.centers) && data.centers.length >= 1);
    }catch(e){
      return false;
    }
  }

  // ---------- B2C ----------
  window.resetChat = function resetChat(){
    const log = $("ai2_chat_log");
    if(!log) return;
    log.innerHTML = "";
    appendMsg(log, "bot",
      "안녕하세요! 조건을 말해주면 근처 지역아동센터를 추천해드릴게요.\n" +
      "예: '제일 가까운 곳 추천해줘', '정원20', '토요일', '3km', '5개 추천해줘'"
    );
  };

    window.sendAi2Chat = async function sendAi2Chat(){
    const log = $("ai2_chat_log");
    const inputEl = $("ai2_chat_input");
    const btn = $("ai2_send_btn");
    if(!log || !inputEl || !btn) return;

    const userMsg = (inputEl.value || "").trim();
    if(!userMsg) return;

    appendMsg(log, "user", userMsg);
    inputEl.value = "";

    btn.disabled = true;
    const thinking = appendMsg(log, "bot", "생각중...");

    // 기본 payload: 위치는 "필요할 때만" 추가
    const payload = { message: userMsg };

    // ✅ "2번 상세" 처리: selected_center_id 추가
    const detailIdx = parseDetailIndex(userMsg);
    if(detailIdx !== null){
      const picked = LAST_CENTERS[detailIdx - 1];
      if(picked && picked.center_id){
        payload.selected_center_id = picked.center_id;
      }else{
        thinking.textContent = "‘n번 상세’는 직전에 추천된 목록이 있어야 해요. 먼저 추천을 받아줘!";
        btn.disabled = false;
        return;
      }
    }

    // ✅ 위치가 필요한 요청만 위치 강제
    const requireGeo = needsGeo(userMsg);

    if(requireGeo){
      try{
        const pos = await getLocationOnce();
        payload.lat = pos.lat;
        payload.lon = pos.lon;
      }catch(e){
        thinking.textContent = "이 요청은 위치가 필요해요. 브라우저에서 위치 허용 후 다시 전송해줘.";
        btn.disabled = false;
        return;
      }
    } else {
      // 위치가 없어도 되는 요청은: 가능하면 위치 붙여주고(거리 계산/상세에 도움), 실패해도 진행
      try{
        const pos = await getLocationOnce();
        payload.lat = pos.lat;
        payload.lon = pos.lon;
      }catch(e){
        // 위치 없이 진행
      }
    }

    try{
      const res = await fetch("/ai2/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await res.json().catch(() => ({}));

      if(!res.ok){
        thinking.textContent = data.error || "오류가 발생했습니다.";
        return;
      }

      thinking.textContent = data.text || "(빈 응답)";

      // ✅ 추천 응답일 때만 LAST_CENTERS 업데이트
      if(looksLikeRecoResponse(data)){
        LAST_CENTERS = data.centers || [];
      }

    }catch(e){
      thinking.textContent = "요청 중 오류가 발생했습니다.";
    }finally{
      btn.disabled = false;
    }
  };


  function bindB2CEnter(){
    const inputEl = $("ai2_chat_input");
    if(!inputEl) return;
    inputEl.addEventListener("keydown", (e) => {
      if(e.key === "Enter"){
        e.preventDefault();
        window.sendAi2Chat();
      }
    });
  }

  // ---------- B2B (textarea/미니채팅 제거 버전) ----------
  window.b2bResetAll = function b2bResetAll(){
    // 폼 초기화(원하면 값 유지해도 됨)
    const districtSel = $("b2b_district");
    const fromSel = $("b2b_year_from");
    const toSel = $("b2b_year_to");

    if(districtSel) districtSel.selectedIndex = 0; // "자치구 선택"
    // 연도는 select로 이미 채워져 있을 테니 첫/마지막 정도로만 정리
    if(fromSel) fromSel.value = String(fromSel.value || 2023);
    if(toSel) toSel.value = String(toSel.value || 2030);

    // 메타/로그 초기화
    setB2BMeta({
      district: "",
      yearFrom: "",
      yearTo: "",
      hintText: "초안 생성 전입니다. “초안 생성”을 누르면 아래에 보고서가 출력됩니다."
    });

    const reportLog = $("b2b_report_log");
    if(reportLog){
      reportLog.innerHTML = "";
      appendMsg(reportLog, "system", "초안 생성 전입니다. “초안 생성”을 누르면 아래에 보고서가 출력됩니다.");
    }
  };

  window.b2bGenerateReport = async function b2bGenerateReport(){
    const district = ($("b2b_district")?.value || "").trim();
    const year_from = Number($("b2b_year_from")?.value || 0);
    const year_to = Number($("b2b_year_to")?.value || 0);

    // 고정
    const report_type = "취약지역 집중지원";

    const reportLog = $("b2b_report_log");
    const btn = $("b2b_gen_btn");

    if(!reportLog || !btn) return;

    if(!district){
      appendMsg(reportLog, "system", "자치구를 선택해줘.");
      return;
    }
    if(!year_from || !year_to || year_from > year_to){
      appendMsg(reportLog, "system", "연도 범위를 확인해줘. (시작연도 ≤ 종료연도)");
      return;
    }

    // UI: 메타 먼저 갱신
    setB2BMeta({
      district,
      yearFrom: year_from,
      yearTo: year_to,
      hintText: "초안 생성 중…"
    });

    btn.disabled = true;

    // 로그: 새로 생성할 때는 화면 깔끔하게 리셋하고 진행
    reportLog.innerHTML = "";
    appendMsg(reportLog, "user", `${district} / ${year_from}~${year_to} / ${report_type}`);
    const thinking = appendMsg(reportLog, "bot", "초안 생성 중...");

    try{
      const res = await fetch("/ai2/b2b/report/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ district, year_from, year_to, report_type })
      });

      const data = await res.json().catch(() => ({}));

      if(!res.ok){
        thinking.textContent = data.error || "생성 중 오류가 발생했습니다.";
        setB2BMeta({
          district,
          yearFrom: year_from,
          yearTo: year_to,
          hintText: "생성 실패: 오류가 발생했습니다."
        });
        return;
      }

      const reportText = data.report || "";

      // bot 생각중 메시지 제거하고, 보고서 버블로 렌더
      thinking.textContent = "초안 생성 완료.";
      appendReport(reportLog, reportText);

      setB2BMeta({
        district,
        yearFrom: year_from,
        yearTo: year_to,
        hintText: "초안 생성 완료. 아래에 보고서가 출력되었습니다."
      });

    }catch(e){
      appendMsg(reportLog, "system", "요청 중 오류가 발생했습니다.");
      setB2BMeta({
        district,
        yearFrom: year_from,
        yearTo: year_to,
        hintText: "요청 실패: 네트워크 오류"
      });
    }finally{
      btn.disabled = false;
    }
  };

  // ---------- init ----------
  document.addEventListener("DOMContentLoaded", () => {
    // B2C init
    if($("ai2_chat_log")) window.resetChat();
    bindB2CEnter();

    // B2B init (b2b_report_log 존재 기준)
    if($("b2b_report_log")) window.b2bResetAll();

    // pre-fetch geo for smoother UX
    if($("geoDot") && $("geoText")){
      setGeo("wait", "위치 확인 대기");
      getLocationOnce().catch(() => {});
    }
  });
})();
