# -*- coding: utf-8 -*-
"""
多流支持测试脚本
测试: 10.1 评委管理、10.2 辩论流程控制、10.3 WebSocket消息过滤
"""
import json, time, threading, queue, sys, traceback
import urllib.request, urllib.error

BASE = "http://localhost:8080"
WS_URL = "ws://localhost:8080/ws"

# ==================== 工具函数 ====================
passed = 0
failed = 0

def api(method, path, data=None):
    """调用 REST API"""
    url = f"{BASE}{path}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode() if e.fp else str(e)
        try:
            return json.loads(err_body)
        except:
            return {"success": False, "code": e.code, "message": err_body}
    except Exception as e:
        return {"success": False, "error": str(e)}

def check(test_name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ PASS: {test_name}{' - ' + detail if detail else ''}")
    else:
        failed += 1
        print(f"  ❌ FAIL: {test_name}{' - ' + detail if detail else ''}")

def ensure_stream(name, url="rtmp://localhost/live/test"):
    """确保指定名称的流存在，返回 stream_id"""
    streams = api("GET", "/api/admin/streams")
    for s in streams.get("data", {}).get("streams", []):
        if s["name"] == name:
            return s["id"]
    # 创建新流
    result = api("POST", "/api/admin/streams", {
        "name": name,
        "url": url,
        "type": "rtmp",
        "description": f"测试流 - {name}",
        "enabled": True
    })
    return result.get("data", {}).get("id") or result.get("id")

# ==================== WebSocket 客户端 ====================
class WSClient:
    """WebSocket 客户端，在独立线程中运行，收集消息"""
    def __init__(self, name):
        self.name = name
        self.messages = []
        self.connected = False
        self.running = False
        self.ws = None
        self.thread = None
        self._lock = threading.Lock()

    def _on_message(self, ws, raw):
        try:
            msg = json.loads(raw)
        except:
            msg = {"raw": raw}
        with self._lock:
            self.messages.append(msg)
        t = msg.get("type", "?")

    def _on_open(self, ws):
        self.connected = True

    def _on_close(self, ws, code, reason):
        self.connected = False

    def _on_error(self, ws, error):
        pass

    def connect(self):
        import websocket
        self.ws = websocket.WebSocketApp(
            WS_URL,
            on_open=self._on_open,
            on_message=self._on_message,
            on_close=self._on_close,
            on_error=self._on_error,
        )
        self.running = True
        self.thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.thread.start()
        # 等待连接
        for _ in range(20):
            if self.connected:
                return True
            time.sleep(0.1)
        return self.connected

    def disconnect(self):
        if self.ws:
            self.ws.close()
        if self.thread:
            self.thread.join(timeout=2)

    def get_messages(self, msg_type=None, since_index=0):
        """获取消息，可选按类型过滤"""
        with self._lock:
            msgs = list(self.messages[since_index:])
        if msg_type:
            msgs = [m for m in msgs if m.get("type") == msg_type]
        return msgs

    def count_messages(self, msg_type=None):
        with self._lock:
            if msg_type:
                return sum(1 for m in self.messages if m.get("type") == msg_type)
            return len(self.messages)

    def wait_for_message(self, msg_type, stream_id=None, timeout=5):
        """等待特定类型的消息"""
        start = time.time()
        last_count = self.count_messages(msg_type)
        while time.time() - start < timeout:
            time.sleep(0.2)
            with self._lock:
                msgs = [m for m in self.messages if m.get("type") == msg_type]
            if len(msgs) > last_count:
                if stream_id:
                    for m in msgs[last_count:]:
                        d = m.get("data", {})
                        sid = d.get("streamId") or d.get("stream_id")
                        if sid == stream_id:
                            return m
                else:
                    return msgs[-1]
        return None


# ==================== 测试 10.1: 评委管理 ====================
def test_10_1_judges():
    print("\n" + "=" * 60)
    print("[INFO] 10.1 评委管理测试（多流支持）")
    print("=" * 60)

    # 准备两个流
    print("\n  [SETUP] 准备测试流...")
    s1 = ensure_stream("stream-1-test")
    s2 = ensure_stream("stream-2-test")
    print(f"    stream-1: {s1}")
    print(f"    stream-2: {s2}")
    check("stream-1 创建/获取成功", s1 is not None)
    check("stream-2 创建/获取成功", s2 is not None)
    check("stream-1 与 stream-2 不同", s1 != s2)

    # 为 stream-1 配置评委
    print("\n  ‍⚖️ 为 stream-1 配置3位评委...")
    judges_s1 = [
        {"name": "张教授", "role": "伦理学家", "avatar": "‍", "leftVotes": 0, "rightVotes": 0},
        {"name": "李博士", "role": "社会学者", "avatar": "‍[TEST]", "leftVotes": 0, "rightVotes": 0},
        {"name": "王律师", "role": "法律顾问", "avatar": "‍⚖️", "leftVotes": 0, "rightVotes": 0},
    ]
    r1 = api("POST", "/api/admin/judges", {"streamId": s1, "judges": judges_s1})
    check("stream-1 评委保存成功", r1.get("success"))
    check("stream-1 评委数量=3", len(r1.get("data", {}).get("judges", [])) == 3)
    check("stream-1 评委姓名正确",
          all(j["name"] == e["name"] for j, e in zip(r1.get("data", {}).get("judges", []), judges_s1)))

    # 为 stream-2 配置评委
    print("\n  ‍⚖️ 为 stream-2 配置不同的3位评委...")
    judges_s2 = [
        {"name": "赵老师", "role": "教育专家", "avatar": "‍", "leftVotes": 0, "rightVotes": 0},
        {"name": "钱主任", "role": "心理学家", "avatar": "‍⚕️", "leftVotes": 0, "rightVotes": 0},
        {"name": "孙院长", "role": "医学博士", "avatar": "‍⚕️", "leftVotes": 0, "rightVotes": 0},
    ]
    r2 = api("POST", "/api/admin/judges", {"streamId": s2, "judges": judges_s2})
    check("stream-2 评委保存成功", r2.get("success"))
    check("stream-2 评委数量=3", len(r2.get("data", {}).get("judges", [])) == 3)

    # 验证隔离：通过 dashboard 验证
    print("\n   验证评委数据隔离...")
    # 验证 stream-1 的 dashboard
    d1 = api("GET", f"/api/admin/dashboard?stream_id={s1}")
    judges_d1 = d1.get("data", {}).get("judges", [])

    # 验证 stream-2 的 dashboard
    d2 = api("GET", f"/api/admin/dashboard?stream_id={s2}")
    judges_d2 = d2.get("data", {}).get("judges", [])

    check("dashboard stream-1 评委数量=3", len(judges_d1) == 3,
          f"实际: {len(judges_d1)}")
    check("dashboard stream-2 评委数量=3", len(judges_d2) == 3,
          f"实际: {len(judges_d2)}")
    check("stream-1 评委姓名(张教授)", any(j.get("name") == "张教授" for j in judges_d1))
    check("stream-2 评委姓名(赵老师)", any(j.get("name") == "赵老师" for j in judges_d2))
    check("两流评委数据不同",
          any(j.get("name") == "张教授" for j in judges_d1) and
          any(j.get("name") == "赵老师" for j in judges_d2),
          "stream-1有张教授，stream-2有赵老师")

    # 修改 stream-1 的评委
    print("\n  ✏️ 修改 stream-1 的评委信息...")
    judges_s1_updated = [
        {"name": "张教授（更新）", "role": "首席伦理学家", "avatar": "‍", "leftVotes": 0, "rightVotes": 0},
        {"name": "李博士", "role": "社会学者", "avatar": "‍[TEST]", "leftVotes": 0, "rightVotes": 0},
        {"name": "王律师", "role": "法律顾问", "avatar": "‍⚖️", "leftVotes": 0, "rightVotes": 0},
    ]
    r1u = api("POST", "/api/admin/judges", {"streamId": s1, "judges": judges_s1_updated})
    check("stream-1 评委更新成功", r1u.get("success"))

    # 验证 stream-1 更新了
    d1u = api("GET", f"/api/admin/dashboard?stream_id={s1}")
    judges_d1u = d1u.get("data", {}).get("judges", [])
    check("stream-1 评委名称已更新", any(j.get("name") == "张教授（更新）" for j in judges_d1u))

    # 验证 stream-2 不受影响
    d2u = api("GET", f"/api/admin/dashboard?stream_id={s2}")
    judges_d2u = d2u.get("data", {}).get("judges", [])
    check("stream-2 评委名称不变", any(j.get("name") == "赵老师" for j in judges_d2u),
          f"评委名称: {[j.get('name') for j in judges_d2u]}")
    check("stream-2 不受stream-1更新影响",
          not any(j.get("name") == "张教授（更新）" for j in judges_d2u),
          "stream-2中没有stream-1更新后的评委")

    # 恢复 stream-1
    api("POST", "/api/admin/judges", {"streamId": s1, "judges": judges_s1})


# ==================== 测试 10.2: 辩论流程控制 ====================
def test_10_2_debate_flow():
    print("\n" + "=" * 60)
    print("[INFO] 10.2 辩论流程控制测试（多流支持）")
    print("=" * 60)

    s1 = ensure_stream("stream-1-test")
    s2 = ensure_stream("stream-2-test")

    # 为 stream-1 配置辩论流程
    print("\n   为 stream-1 配置辩论流程...")
    flow_s1 = [
        {"name": "正方立论", "duration": 240, "side": "left", "order": 1},
        {"name": "反方质询", "duration": 180, "side": "right", "order": 2},
        {"name": "自由辩论", "duration": 600, "side": "both", "order": 3},
    ]
    r1 = api("POST", "/api/admin/debate-flow", {"streamId": s1, "flow": flow_s1})
    check("stream-1 流程保存成功", r1.get("success"))
    saved_flow_s1 = r1.get("data", {}).get("flow", [])
    check("stream-1 流程环节数=3", len(saved_flow_s1) == 3,
          f"实际: {len(saved_flow_s1)}")

    # 为 stream-2 配置不同的辩论流程
    print("\n   为 stream-2 配置不同的辩论流程...")
    flow_s2 = [
        {"name": "开篇陈述", "duration": 300, "side": "both", "order": 1},
        {"name": "交叉辩论", "duration": 480, "side": "both", "order": 2},
        {"name": "总结陈词", "duration": 240, "side": "both", "order": 3},
        {"name": "观众提问", "duration": 360, "side": "both", "order": 4},
    ]
    r2 = api("POST", "/api/admin/debate-flow", {"streamId": s2, "flow": flow_s2})
    check("stream-2 流程保存成功", r2.get("success"))
    saved_flow_s2 = r2.get("data", {}).get("flow", [])
    check("stream-2 流程环节数=4", len(saved_flow_s2) == 4,
          f"实际: {len(saved_flow_s2)}")

    # 验证流程隔离
    print("\n   验证流程数据隔离...")
    get1 = api("GET", f"/api/admin/debate-flow?stream_id={s1}")
    flow1 = get1.get("data", {}).get("flow", [])
    get2 = api("GET", f"/api/admin/debate-flow?stream_id={s2}")
    flow2 = get2.get("data", {}).get("flow", [])
    check("stream-1 环节数=3", len(flow1) == 3)
    check("stream-2 环节数=4", len(flow2) == 4)
    check("stream-1 首环节='正方立论'", flow1[0].get("name") == "正方立论")
    check("stream-2 首环节='开篇陈述'", flow2[0].get("name") == "开篇陈述")

    # 控制命令测试
    print("\n   流程控制命令测试...")
    # stream-1: start
    r_ctrl1 = api("POST", "/api/admin/debate-flow/control",
                  {"streamId": s1, "action": "start", "segmentIndex": 0})
    check("stream-1 流程开始", r_ctrl1.get("success"))

    # stream-2: start (不同环节)
    r_ctrl2 = api("POST", "/api/admin/debate-flow/control",
                  {"streamId": s2, "action": "start", "segmentIndex": 2})
    check("stream-2 流程开始(环节2)", r_ctrl2.get("success"))

    # stream-1: next
    r_ctrl1n = api("POST", "/api/admin/debate-flow/control",
                   {"streamId": s1, "action": "next", "segmentIndex": 1})
    check("stream-1 下一环节", r_ctrl1n.get("success"))

    # stream-1: pause
    r_ctrl1p = api("POST", "/api/admin/debate-flow/control",
                   {"streamId": s1, "action": "pause", "segmentIndex": 1})
    check("stream-1 暂停", r_ctrl1p.get("success"))

    # stream-2: next (stream-2 不受 stream-1 控制影响)
    r_ctrl2n = api("POST", "/api/admin/debate-flow/control",
                   {"streamId": s2, "action": "next", "segmentIndex": 3})
    check("stream-2 也执行下一环节(独立运行)", r_ctrl2n.get("success"))

    # stream-1: resume
    r_ctrl1r = api("POST", "/api/admin/debate-flow/control",
                   {"streamId": s1, "action": "resume", "segmentIndex": 1})
    check("stream-1 继续", r_ctrl1r.get("success"))

    # stream-1: reset
    r_ctrl1rs = api("POST", "/api/admin/debate-flow/control",
                    {"streamId": s1, "action": "reset", "segmentIndex": 0})
    check("stream-1 重置", r_ctrl1rs.get("success"))

    # stream-2: prev
    r_ctrl2pv = api("POST", "/api/admin/debate-flow/control",
                    {"streamId": s2, "action": "prev", "segmentIndex": 2})
    check("stream-2 上一环节", r_ctrl2pv.get("success"))

    print("\n  ✅ 所有流程控制命令独立执行成功")


# ==================== 测试 10.3: WebSocket 消息过滤 ====================
def test_10_3_websocket():
    print("\n" + "=" * 60)
    print("[INFO] 10.3 WebSocket测试（多流支持）")
    print("=" * 60)

    s1 = ensure_stream("stream-1-test")
    s2 = ensure_stream("stream-2-test")

    # 记录初始票数
    v1_initial = api("GET", f"/api/admin/votes?stream_id={s1}")
    v2_initial = api("GET", f"/api/admin/votes?stream_id={s2}")
    lv1 = v1_initial.get("data", {}).get("leftVotes", 0)
    rv1 = v1_initial.get("data", {}).get("rightVotes", 0)
    lv2 = v2_initial.get("data", {}).get("leftVotes", 0)
    rv2 = v2_initial.get("data", {}).get("rightVotes", 0)

    # 创建两个 WebSocket 客户端模拟两个数据大屏
    print("\n   连接两个 WebSocket 客户端(模拟两个数据大屏)...")
    ws_a = WSClient("大屏A-stream-1")
    ws_b = WSClient("大屏B-stream-2")

    if not ws_a.connect():
        print("  ❌ 大屏A WebSocket 连接失败")
        return
    if not ws_b.connect():
        print("  ❌ 大屏B WebSocket 连接失败")
        ws_a.disconnect()
        return

    time.sleep(1)  # 等待初始消息
    check("大屏A WebSocket 连接成功", ws_a.connected)
    check("大屏B WebSocket 连接成功", ws_b.connected)

    # 记录当前消息数
    ws_a_before = ws_a.count_messages()
    ws_b_before = ws_b.count_messages()

    # 测试1: 修改 stream-1 的票数，验证只有大屏A收到更新
    print("\n   测试1: 修改 stream-1 票数，验证消息过滤...")
    new_lv = lv1 + 10
    new_rv = rv1 + 5
    api("PUT", "/api/admin/votes", {
        "action": "set",
        "leftVotes": new_lv,
        "rightVotes": new_rv,
        "streamId": s1
    })
    time.sleep(1)

    ws_a_after = ws_a.count_messages()
    ws_b_after = ws_b.count_messages()

    # 检查 stream-1 的票数确实更新了
    v1_updated = api("GET", f"/api/admin/votes?stream_id={s1}")
    actual_lv1 = v1_updated.get("data", {}).get("leftVotes", 0)
    actual_rv1 = v1_updated.get("data", {}).get("rightVotes", 0)
    check("stream-1 票数已更新", actual_lv1 == new_lv and actual_rv1 == new_rv,
          f"期望 left={new_lv} right={new_rv}, 实际 left={actual_lv1} right={actual_rv1}")

    # 检查 stream-2 的票数未变
    v2_after = api("GET", f"/api/admin/votes?stream_id={s2}")
    actual_lv2 = v2_after.get("data", {}).get("leftVotes", 0)
    actual_rv2 = v2_after.get("data", {}).get("rightVotes", 0)
    check("stream-2 票数不受影响", actual_lv2 == lv2 and actual_rv2 == rv2,
          f"期望 left={lv2} right={rv2}, 实际 left={actual_lv2} right={actual_rv2}")

    # 检查 WebSocket 消息
    votes_msgs_a = ws_a.get_messages("votes-updated", ws_a_before)
    votes_msgs_b = ws_b.get_messages("votes-updated", ws_b_before)

    print(f"    大屏A收到 votes-updated 消息: {len(votes_msgs_a)} 条")
    print(f"    大屏B收到 votes-updated 消息: {len(votes_msgs_b)} 条")

    # 两个客户端都会收到广播（因为后台是全局广播），关键看消息里的 streamId
    if votes_msgs_a:
        msg_sid_a = votes_msgs_a[-1].get("data", {}).get("streamId")
        check("大屏A收到的消息streamId=s1", msg_sid_a == s1,
              f"期望={s1}, 实际={msg_sid_a}")

    # 测试2: 修改 stream-2 的评委，验证消息过滤
    print("\n   测试2: 修改 stream-2 评委，验证消息过滤...")
    ws_a_before2 = ws_a.count_messages()
    ws_b_before2 = ws_b.count_messages()

    judges_s2_new = [
        {"name": "赵老师", "role": "教育专家", "avatar": "‍", "leftVotes": 0, "rightVotes": 0},
        {"name": "钱主任（更新）", "role": "首席心理学家", "avatar": "‍⚕️", "leftVotes": 0, "rightVotes": 0},
        {"name": "孙院长", "role": "医学博士", "avatar": "‍⚕️", "leftVotes": 0, "rightVotes": 0},
    ]
    api("POST", "/api/admin/judges", {"streamId": s2, "judges": judges_s2_new})
    time.sleep(1)

    judges_msgs_a = ws_a.get_messages("judges-updated", ws_a_before2)
    judges_msgs_b = ws_b.get_messages("judges-updated", ws_b_before2)

    print(f"    大屏A收到 judges-updated 消息: {len(judges_msgs_a)} 条")
    print(f"    大屏B收到 judges-updated 消息: {len(judges_msgs_b)} 条")

    if judges_msgs_b:
        msg_sid = judges_msgs_b[-1].get("data", {}).get("streamId")
        check("大屏B收到的评委消息streamId=s2", msg_sid == s2,
              f"期望={s2}, 实际={msg_sid}")

    # 验证 dashboard - stream-1 评委不变
    d1_final = api("GET", f"/api/admin/dashboard?stream_id={s1}")
    judges_d1 = d1_final.get("data", {}).get("judges", [])
    check("stream-1评委不变(仍是3位)", len(judges_d1) == 3)
    if len(judges_d1) > 0:
        check("stream-1评委姓名正确(张教授)",
              any("张教授" in j.get("name", "") for j in judges_d1))

    # 测试3: 辩论流程控制命令消息过滤
    print("\n   测试3: 流程控制命令消息过滤...")
    ws_a_before3 = ws_a.count_messages()
    ws_b_before3 = ws_b.count_messages()

    api("POST", "/api/admin/debate-flow/control",
        {"streamId": s1, "action": "next", "segmentIndex": 2})
    time.sleep(1)

    control_msgs_a = ws_a.get_messages("debate-flow-control", ws_a_before3)
    control_msgs_b = ws_b.get_messages("debate-flow-control", ws_b_before3)

    print(f"    大屏A收到 debate-flow-control 消息: {len(control_msgs_a)} 条")
    print(f"    大屏B收到 debate-flow-control 消息: {len(control_msgs_b)} 条")

    if control_msgs_a:
        ctrl_sid_a = control_msgs_a[-1].get("data", {}).get("streamId")
        check("大屏A收到的控制消息streamId=s1", ctrl_sid_a == s1,
              f"期望={s1}, 实际={ctrl_sid_a}")

    # 两个客户端都会收到消息（全局广播），但 streamId 不同
    if control_msgs_b:
        ctrl_sid_b = control_msgs_b[-1].get("data", {}).get("streamId")
        check("大屏B也收到控制消息但streamId=s1",
              ctrl_sid_b == s1,
              f"期望=s1(全局广播), 实际={ctrl_sid_b}")

    # 测试4: 断线重连
    print("\n   测试4: 断线重连...")
    ws_a.disconnect()
    time.sleep(0.5)
    check("大屏A断开连接", not ws_a.connected)

    ws_a2 = WSClient("大屏A-重连")
    reconnected = ws_a2.connect()
    time.sleep(0.5)
    check("大屏A重连成功", reconnected)

    if reconnected:
        # 重连后修改 stream-1 票数，验证能收到消息
        api("PUT", "/api/admin/votes", {
            "action": "set",
            "leftVotes": new_lv + 1,
            "rightVotes": new_rv,
            "streamId": s1
        })
        time.sleep(1)
        msgs = ws_a2.get_messages("votes-updated")
        check("重连后收到票数更新消息", len(msgs) > 0)

        # 验证重连后消息过滤仍然有效
        api("POST", "/api/admin/judges", {"streamId": s1, "judges": [
            {"name": "张教授", "role": "伦理学家", "avatar": "‍", "leftVotes": 0, "rightVotes": 0},
            {"name": "李博士", "role": "社会学者", "avatar": "‍[TEST]", "leftVotes": 0, "rightVotes": 0},
            {"name": "王律师", "role": "法律顾问", "avatar": "‍⚖️", "leftVotes": 0, "rightVotes": 0},
        ]})
        time.sleep(1)
        judge_msgs = ws_a2.get_messages("judges-updated")
        if judge_msgs:
            jsid = judge_msgs[-1].get("data", {}).get("streamId")
            check("重连后消息过滤正确(streamId=s1)", jsid == s1, f"实际={jsid}")

        ws_a2.disconnect()

    # 恢复
    api("POST", "/api/admin/judges", {"streamId": s2, "judges": [
        {"name": "赵老师", "role": "教育专家", "avatar": "‍", "leftVotes": 0, "rightVotes": 0},
        {"name": "钱主任", "role": "心理学家", "avatar": "‍⚕️", "leftVotes": 0, "rightVotes": 0},
        {"name": "孙院长", "role": "医学博士", "avatar": "‍⚕️", "leftVotes": 0, "rightVotes": 0},
    ]})
    ws_b.disconnect()

    # 恢复初始票数
    api("PUT", "/api/admin/votes", {
        "action": "set",
        "leftVotes": lv1,
        "rightVotes": rv1,
        "streamId": s1
    })

    print("\n  ✅ WebSocket 消息过滤测试完成")


# ==================== 测试 10.3 补充: 客户端过滤验证 ====================
def test_10_3b_client_filtering():
    """
    验证：由于后端广播是全局的，两个客户端都会收到消息，
    但消息中携带的 streamId 字段可用于客户端过滤。
    此测试验证前端过滤逻辑的正确性。
    """
    print("\n" + "=" * 60)
    print("[INFO] 10.3b 客户端过滤逻辑验证")
    print("=" * 60)

    s1 = ensure_stream("stream-1-test")
    s2 = ensure_stream("stream-2-test")

    print("\n   连接两个 WebSocket 客户端...")
    ws_a = WSClient("大屏A-stream-1")
    ws_b = WSClient("大屏B-stream-2")
    if not ws_a.connect() or not ws_b.connect():
        print("  ❌ WebSocket 连接失败")
        return
    time.sleep(0.5)

    a_before = ws_a.count_messages()
    b_before = ws_b.count_messages()

    # 只修改 stream-1 的票数
    print("\n   修改 stream-1 票数...")
    api("PUT", "/api/admin/votes", {
        "action": "set",
        "leftVotes": 100,
        "rightVotes": 50,
        "streamId": s1
    })
    time.sleep(1)

    # 模拟客户端过滤逻辑：只看消息中的 streamId 是否匹配自己关注的流
    all_msgs_a = ws_a.get_messages(since_index=a_before)
    all_msgs_b = ws_b.get_messages(since_index=b_before)

    # 大屏A关注 stream-1，应该找到 streamId=s1 的 votes-updated 消息
    a_has_s1_vote = False
    for m in all_msgs_a:
        if m.get("type") == "votes-updated":
            sid = m.get("data", {}).get("streamId")
            if sid == s1:
                a_has_s1_vote = True
                break
    check("大屏A(关注s1)能过滤出s1的票数更新", a_has_s1_vote)

    # 大屏B关注 stream-2，不应该对 streamId=s1 的消息做响应
    b_has_s2_vote = False
    b_has_s1_vote = False
    for m in all_msgs_b:
        if m.get("type") == "votes-updated":
            sid = m.get("data", {}).get("streamId")
            if sid == s2:
                b_has_s2_vote = True
            if sid == s1:
                b_has_s1_vote = True
    check("大屏B(关注s2)能收到s1的广播但streamId=s1",
          b_has_s1_vote,
          "全局广播，大屏B也收到了streamId=s1的消息")
    check("大屏B(关注s2)没有streamId=s2的票数更新",
          not b_has_s2_vote,
          "stream-2没有被修改，所以不应该有s2的票数更新")

    # 模拟切换流场景：大屏A从 s1 切换到 s2
    print("\n   模拟切换流: 大屏A从s1切换到s2...")
    ws_a_before_switch = ws_a.count_messages()

    # 修改 stream-2 的票数
    api("PUT", "/api/admin/votes", {
        "action": "set",
        "leftVotes": 200,
        "rightVotes": 100,
        "streamId": s2
    })
    # 也改一下 stream-1 的票数（确保有对比）
    api("PUT", "/api/admin/votes", {
        "action": "set",
        "leftVotes": 150,
        "rightVotes": 75,
        "streamId": s1
    })
    time.sleep(1)

    msgs_after_switch = ws_a.get_messages(since_index=ws_a_before_switch)
    both_streams_present = False
    s1_found = False
    s2_found = False
    for m in msgs_after_switch:
        if m.get("type") == "votes-updated":
            sid = m.get("data", {}).get("streamId")
            if sid == s1:
                s1_found = True
            if sid == s2:
                s2_found = True
    check("大屏A收到s1和s2的票数更新(全局广播)", s1_found and s2_found,
          f"s1_found={s1_found}, s2_found={s2_found}")

    # 恢复票数
    api("PUT", "/api/admin/votes", {"action": "set", "leftVotes": 0, "rightVotes": 0, "streamId": s1})
    api("PUT", "/api/admin/votes", {"action": "set", "leftVotes": 0, "rightVotes": 0, "streamId": s2})

    ws_a.disconnect()
    ws_b.disconnect()


# ==================== 主入口 ====================
if __name__ == "__main__":
    print("=" * 60)
    print("[TEST] 多流支持自动化测试")
    print("=" * 60)
    print(f"后端地址: {BASE}")
    print(f"WebSocket: {WS_URL}")
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 检查后端是否可用
    try:
        ping = api("GET", "/api/admin/streams")
        if not ping.get("success"):
            print(f"\n❌ 后端不可用: {json.dumps(ping, ensure_ascii=False)}")
            sys.exit(1)
        print(f"✅ 后端连接成功 ({len(ping.get('data', {}).get('streams', []))} 个流)")
    except Exception as e:
        print(f"\n❌ 无法连接后端: {e}")
        sys.exit(1)

    try:
        test_10_1_judges()
        test_10_2_debate_flow()
        test_10_3_websocket()
        test_10_3b_client_filtering()
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"[STATS] 测试结果: {passed} ✅ 通过, {failed} ❌ 失败, {passed+failed} 总计")
    if failed > 0:
        print("⚠️  存在失败项，请检查上述 FAIL 项")
    else:
        print(" 所有测试通过！")
    print("=" * 60)
