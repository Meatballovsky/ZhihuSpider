"""知乎用户内容爬虫核心逻辑，支持回答、文章、想法。"""
import json
import time
import random
from datetime import datetime

from converter import (
    html_to_md, pin_content_to_md,
    save_answer_as_md, save_article_as_md, save_pin_as_md,
)

CONTENT_TYPES = {
    'answers': {
        'label': '回答',
        'page_path': '/answers',
        'listen_pattern': '/answers?',
        'saver': save_answer_as_md,
    },
    'articles': {
        'label': '文章',
        'page_path': '/posts',
        'listen_pattern': '/articles?',
        'saver': save_article_as_md,
    },
    'pins': {
        'label': '想法',
        'page_path': '/pins',
        'listen_pattern': '/moments?',
        'saver': save_pin_as_md,
    },
}


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


# --------------- item 解析（按内容类型） ---------------

def _parse_answer_item(item, user_id):
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

    return {
        'title': title,
        'voteup': voteup,
        'author': author_name,
        'date': date_str,
        'url': url,
        'content_md': html_to_md(content_html),
    }


def _parse_article_item(item, user_id):
    title = item.get('title', '无标题')
    voteup = item.get('voteup_count', 0)
    content_html = item.get('content', '')
    article_id = item.get('id', '')
    created = item.get('created', 0) or item.get('created_time', 0)
    author_info = item.get('author', {})
    author_name = author_info.get('name', user_id) if isinstance(author_info, dict) else user_id
    date_str = datetime.fromtimestamp(created).strftime('%Y-%m-%d') if created else ''
    url = f'https://zhuanlan.zhihu.com/p/{article_id}'

    return {
        'title': title,
        'voteup': voteup,
        'author': author_name,
        'date': date_str,
        'url': url,
        'content_md': html_to_md(content_html),
    }


def _parse_pin_item(item, user_id):
    pin_id = item.get('id', '')
    created = item.get('created', 0)
    like_count = item.get('reaction_count', 0) or item.get('like_count', 0)
    comment_count = item.get('comment_count', 0)
    author_info = item.get('author', {})
    author_name = author_info.get('name', user_id) if isinstance(author_info, dict) else user_id
    date_str = datetime.fromtimestamp(created).strftime('%Y-%m-%d') if created else ''
    url = f'https://www.zhihu.com/pin/{pin_id}'

    content_blocks = item.get('content', [])
    excerpt = item.get('excerpt_title', '')
    if not excerpt and content_blocks:
        for block in content_blocks:
            if block.get('type') == 'text':
                excerpt = (block.get('content', '') or '')[:20]
                break

    return {
        'author': author_name,
        'date': date_str,
        'like_count': like_count,
        'comment_count': comment_count,
        'url': url,
        'excerpt': excerpt,
        'content_md': pin_content_to_md(content_blocks),
    }


_ITEM_PARSERS = {
    'answers': _parse_answer_item,
    'articles': _parse_article_item,
    'pins': _parse_pin_item,
}


# --------------- 通用包解析 ---------------

def _parse_packet(packet, user_id, content_type='answers'):
    """解析一个 API 响应包，返回 (items_list, totals, is_end)。"""
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

        parser = _ITEM_PARSERS.get(content_type, _parse_answer_item)
        results = []
        for item in data['data']:
            try:
                results.append(parser(item, user_id))
            except Exception as e:
                print(f"  [!] 解析单条数据出错: {e}")
        return results, totals, is_end
    except Exception as e:
        print(f"  [!] 解析响应出错: {e}")
        return [], 0, True


def _wait_for_first_page(tab, user_id, content_type='answers', stop_check=None):
    """等待并解析第一页 API 响应，最多重试 10 个包。"""
    for _ in range(10):
        if stop_check and stop_check():
            return [], 0, True
        packet = tab.listen.wait(timeout=8)
        if not packet:
            break
        items, totals, is_end = _parse_packet(packet, user_id, content_type)
        if items:
            return items, totals, is_end
    return [], 0, True


# --------------- 通用爬取函数 ---------------

def crawl_content(tab, user_id, output_dir, content_type='answers',
                  max_items=0, delay_range=(8, 15),
                  stop_check=None, pause_event=None):
    """
    爬取指定用户的指定类型内容。

    Args:
        tab: DrissionPage 浏览器标签页
        user_id: 知乎用户 ID
        output_dir: 输出目录（会自动创建）
        content_type: 内容类型 ('answers', 'articles', 'pins')
        max_items: 最大爬取条数，0 表示全部
        delay_range: 翻页间隔 (min_sec, max_sec)
        stop_check: 可选回调，返回 True 时立即终止
        pause_event: threading.Event，set=运行，clear=暂停

    Returns:
        实际保存的条数
    """
    import os
    os.makedirs(output_dir, exist_ok=True)

    type_cfg = CONTENT_TYPES.get(content_type)
    if not type_cfg:
        print(f"  [!] 未知的内容类型: {content_type}")
        return 0

    type_label = type_cfg['label']
    page_path = type_cfg['page_path']
    listen_pattern = type_cfg['listen_pattern']
    saver = type_cfg['saver']

    def _stopped():
        return stop_check() if stop_check else False

    def _sleep(seconds):
        return _interruptible_sleep(seconds, stop_check, pause_event)

    target_url = f'https://www.zhihu.com/people/{user_id}{page_path}'
    print(f"\n  访问 {target_url} ...")

    tab.listen.start(listen_pattern)
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
    items, totals, is_end = _wait_for_first_page(
        tab, user_id, content_type, stop_check)
    tab.listen.stop()

    if _stopped():
        print("  [!] 已终止。")
        return 0

    if not items:
        print(f"  首页未捕获到 API 数据，尝试滚动加载...")
        tab.listen.start(listen_pattern)
        tab.scroll.to_bottom()
        if _sleep(random.uniform(3, 5)):
            tab.listen.stop()
            return 0
        items, totals, is_end = _wait_for_first_page(
            tab, user_id, content_type, stop_check)
        tab.listen.stop()

        if _stopped():
            print("  [!] 已终止。")
            return 0

        if not items:
            print(f"  [!] 未能获取到{type_label}数据。")
            return 0

    target_count = totals if max_items == 0 else min(max_items, totals)
    print(f"  该用户共 {totals} 条{type_label}，"
          f"本次目标: {'全部' if max_items == 0 else target_count} 条")

    saved = 0

    def _save_batch(batch):
        nonlocal saved
        for item in batch:
            if max_items > 0 and saved >= max_items:
                break
            if _stopped():
                break
            try:
                saver(item, output_dir)
                saved += 1
            except Exception as e:
                print(f"  [!] 保存失败: {e}")

    _save_batch(items)
    print(f"  [第1页] 已保存 {saved}/{target_count} 条")

    if not is_end and (max_items == 0 or saved < max_items) and not _stopped():
        tab.listen.start(listen_pattern)
        page = 1
        retry_count = 0

        while not is_end and (max_items == 0 or saved < max_items):
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

            if not packet:
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
            items, _, is_end = _parse_packet(packet, user_id, content_type)
            if items:
                page += 1
                _save_batch(items)
                print(f"  [第{page}页] 已保存 {saved}/{target_count} 条")

        tab.listen.stop()

    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)

    status = "终止" if _stopped() else "完成"
    print(f"\n  {'=' * 50}")
    print(f"  用户 {user_id} {type_label}爬取{status}")
    print(f"  保存: {saved} 条 | 耗时: {minutes}分{seconds}秒")
    print(f"  目录: {output_dir}")
    print(f"  {'=' * 50}")

    return saved


def crawl_answers(tab, user_id, output_dir, max_answers=0,
                  delay_range=(8, 15), stop_check=None, pause_event=None):
    """兼容旧接口：爬取回答。"""
    return crawl_content(
        tab, user_id, output_dir,
        content_type='answers', max_items=max_answers,
        delay_range=delay_range, stop_check=stop_check,
        pause_event=pause_event,
    )
