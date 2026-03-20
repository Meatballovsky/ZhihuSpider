"""HTML -> Markdown 转换 和 文件保存。"""
import os
import re

from bs4 import BeautifulSoup


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|\n\t]', '', name)[:80]


def html_to_md(html: str) -> str:
    if not html:
        return ''
    soup = BeautifulSoup(html, 'lxml')

    for img in soup.find_all('img'):
        src = img.get('data-original') or img.get('data-actualsrc') or img.get('src', '')
        alt = img.get('alt', '')
        img.replace_with(f'![{alt}]({src})')

    for a in soup.find_all('a'):
        href = a.get('href', '')
        text = a.get_text()
        if href and text:
            a.replace_with(f'[{text}]({href})')

    for b in soup.find_all(['b', 'strong']):
        b.replace_with(f'**{b.get_text()}**')

    for i_tag in soup.find_all(['i', 'em']):
        i_tag.replace_with(f'*{i_tag.get_text()}*')

    for br in soup.find_all('br'):
        br.replace_with('\n')

    for p in soup.find_all('p'):
        p.replace_with(p.get_text() + '\n\n')

    for li in soup.find_all('li'):
        li.replace_with('- ' + li.get_text() + '\n')

    for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        level = int(h.name[1])
        h.replace_with('#' * level + ' ' + h.get_text() + '\n\n')

    for blockquote in soup.find_all('blockquote'):
        lines = blockquote.get_text().strip().split('\n')
        blockquote.replace_with('\n'.join('> ' + line for line in lines) + '\n\n')

    text = soup.get_text()
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def save_answer_as_md(answer: dict, output_dir: str) -> str:
    """将一条回答保存为 Markdown 文件，返回文件名。"""
    title = answer.get('title', '无标题')
    safe_title = sanitize_filename(title)
    voteup = answer.get('voteup', 0)
    author = answer.get('author', '')
    date = answer.get('date', '')
    url = answer.get('url', '')
    content = answer.get('content_md', '')

    filename = f"{safe_title}-{voteup}赞.md"
    filepath = os.path.join(output_dir, filename)

    md = f"# [{title}]({url})\n\n"
    md += f"**{author}** / {date} 👍 {voteup}\n\n"
    md += "---\n\n"
    md += content + "\n"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md)
    return filename
