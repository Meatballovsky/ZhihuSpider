"""知乎用户回答爬虫核心逻辑。"""
import json
import time
import random
from datetime import datetime

from converter import html_to_md, save_answer_as_md


def _interruptible_sleep(seconds, stop_check, pause_event=None, interval=0.5):
    """可中断、可暂停的 sleep。

    pause_event: threading.Event，set=运行中，clear=暂停。
    返回 True 表示被终止（stop），False 表示正常结束。
    """
    end = time.time() + seconds
    while time.time() < end:
        if stop_check and stop_check():
            return True
        if pause_event and not pause_event.is_set():
            print("  [暂停中] 等待继续...")
            while not pause_event.is_set():
                if stop_check and stop_check():
                    return True
                pause_event.wait(0.5)
            print("  [已继续]")
            end = time.time() + max(0, end - time.time())
        time.sleep(min(interval, max(0, end - time.time())))
    return stop_check() if stop_check else False


def _parse_packet(packet, user_id):
    """解析一个 API 响应包，返回 (answers_list, totals, is_end)。"""
    try:
        resp = packet.response
        if hasattr(resp, 'status') and resp.status != 200:
            return [], 0, True

        body = resp.body
        if isinstance(body, str):
            data = json.loads(body)
        elif isinstance(body, dict):
            data = body
        else:
            return [], 0, True

        if 'data' not in data or 'paging' not in data:
            return [], 0, True

        totals = data['paging'].get('totals', 0)
        is_end = data['paging'].get('is_end', True)

        results = []
        for item in data['data']:
            title = item.get('question', {}).get('title', '无标题')
            voteup = item.get('voteup_count', 0)
            content_html = item.get('content', '')
            question_id = item.get('question', {}).get('id', '')
            answer_id = item.get('id', '')
            created = item.get('created_time', 0)
            author_info = item.get('author', {})
            author_name = author_info.get('name', user_id) if isinstance(author_info, dict) else user_id
            date_str = datetime.fromtimestamp(created).strftime('%Y-%m-%d') if created else ''
            url = f'https://www.zhihu.com/question/{question_id}/answer/{answer_id}'

            results.append({
                'title': title,
                'voteup': voteup,
                'author': author_name,
                'date': date_str,
                'url': url,
                'content_md': html_to_md(content_html),
            })
        return results, totals, is_end
    except Exception as e:
        print(f"  [!] 解析响应出错: {e}")
        return [], 0, True


def _wait_for_first_page(tab, user_id, stop_check=None):
    """等待并解析第一页 API 响应，最多重试 10 个包。"""
    for _ in range(10):
        if stop_check and stop_check():
            return [], 0, True
        packet = tab.listen.wait(timeout=8)
        if packet is None:
            break
        answers, totals, is_end = _parse_packet(packet, user_id)
        if answers:
            return answers, totals, is_end
    return [], 0, True


def crawl_answers(tab, user_id, output_dir, max_answers=0,
                  delay_range=(8, 15), stop_check=None, pause_event=None):
    """
    爬取指定用户的全部回答。

    Args:
        tab: DrissionPage 浏览器标签页
        user_id: 知乎用户 ID
        output_dir: 输出目录（会自动创建）
        max_answers: 最大爬取条数，0 表示全部
        delay_range: 翻页间隔 (min_sec, max_sec)
        stop_check: 可选回调，返回 True 时立即终止
        pause_event: threading.Event，set=运行，clear=暂停

    Returns:
        实际保存的回答条数
    """
    import os
    os.makedirs(output_dir, exist_ok=True)

    def _stopped():
        return stop_check() if stop_check else False

    def _sleep(seconds):
        return _interruptible_sleep(seconds, stop_check, pause_event)

    target_url = f'https://www.zhihu.com/people/{user_id}/answers'
    print(f"\n  访问 {target_url} ...")

    tab.listen.start('/answers?')
    tab.get(target_url)
    if _sleep(8):
        tab.listen.stop()
        print("  [!] 已终止。")
        return 0

    print(f"  页面: {tab.title}")

    try:
        close_btn = tab.ele('css:.Modal-closeButton', timeout=2)
        if close_btn:
            close_btn.click()
            _sleep(1)
    except Exception:
        pass

    if _stopped():
        tab.listen.stop()
        print("  [!] 已终止。")
        return 0

    start_time = time.time()
    answers, totals, is_end = _wait_for_first_page(tab, user_id, stop_check)
    tab.listen.stop()

    if _stopped():
        print("  [!] 已终止。")
        return 0

    if not answers:
        print("  [!] 未能获取到回答数据。")
        return 0

    target_count = totals if max_answers == 0 else min(max_answers, totals)
    print(f"  该用户共 {totals} 条回答，本次目标: {'全部' if max_answers == 0 else target_count} 条")

    saved = 0

    def _save_batch(batch):
        nonlocal saved
        for ans in batch:
            if max_answers > 0 and saved >= max_answers:
                break
            if _stopped():
                break
            try:
                save_answer_as_md(ans, output_dir)
                saved += 1
            except Exception as e:
                print(f"  [!] 保存失败: {e}")

    _save_batch(answers)
    print(f"  [第1页] 已保存 {saved}/{target_count} 条")

    if not is_end and (max_answers == 0 or saved < max_answers) and not _stopped():
        tab.listen.start('/answers?')
        page = 1
        retry_count = 0

        while not is_end and (max_answers == 0 or saved < max_answers):
            if _stopped():
                break

            wait = random.uniform(*delay_range)
            jitter = random.uniform(-2, 3)
            wait = max(5, wait + jitter)
            print(f"  休息 {wait:.0f} 秒...")
            if _sleep(wait):
                break

            pre_scroll = random.randint(300, 800)
            tab.scroll.down(pre_scroll)
            if _sleep(random.uniform(1, 3)):
                break

            tab.scroll.to_bottom()
            if _sleep(random.uniform(3, 6)):
                break

            packet = tab.listen.wait(timeout=20)
            if _stopped():
                break

            if packet is None:
                retry_count += 1
                if retry_count >= 2:
                    print("  [!] 连续未收到数据，停止翻页。")
                    break
                print("  [!] 未收到数据，重试滚动...")
                tab.scroll.to_bottom()
                if _sleep(random.uniform(3, 5)):
                    break
                continue

            retry_count = 0
            answers, _, is_end = _parse_packet(packet, user_id)
            if answers:
                page += 1
                _save_batch(answers)
                print(f"  [第{page}页] 已保存 {saved}/{target_count} 条")

        tab.listen.stop()

    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)

    status = "终止" if _stopped() else "完成"
    print(f"\n  {'=' * 50}")
    print(f"  用户 {user_id} 爬取{status}")
    print(f"  保存: {saved} 条 | 耗时: {minutes}分{seconds}秒")
    print(f"  目录: {output_dir}")
    print(f"  {'=' * 50}")

    return saved
