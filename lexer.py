
import sys
from typing import List, Tuple, Dict

class Token:
    def __init__(self, token_type: str, value: str, line: int):
        self.token_type = token_type   # KEYWORD / IDENTIFIER / INT_CONSTANT / REAL_CONSTANT / STRING_CONSTANT / OPERATOR / DELIMITER
        self.value = value
        self.line = line

KEYWORDS = {
    "if", "else", "while", "for", "int", "float", "char", "return",
    "void", "main", "double", "bool", "true", "false"
}


tokens: List[Token] = []
errors: List[str] = []
source_code: str = ""
pos: int = 0
current_line: int = 1
current_col: int = 1

def peek() -> str:
    """前看当前字符"""
    global pos
    if pos >= len(source_code):
        return '\0'
    return source_code[pos]

def advance() -> str:
    global pos, current_line, current_col
    if pos >= len(source_code):
        return '\0'
    ch = source_code[pos]
    pos += 1
    if ch == '\n':
        current_line += 1
        current_col = 1
    else:
        current_col += 1
    return ch

def skip_whitespace_and_comments() -> None:
    global pos
    while True:
        ch = peek()
        if ch.isspace():
            advance()
            continue

        if ch == '/' and pos + 1 < len(source_code) and source_code[pos + 1] == '/':
            advance()
            advance()
            while peek() != '\n' and peek() != '\0':
                advance()
            continue
        if ch == '/' and pos + 1 < len(source_code) and source_code[pos + 1] == '*':
            advance()
            advance()
            while True:
                if peek() == '\0':
                    errors.append(f"错误：未闭合的多行注释 at line {current_line}")
                    return
                if peek() == '*' and pos + 1 < len(source_code) and source_code[pos + 1] == '/':
                    advance()
                    advance()
                    break
                advance()
            continue

        break



def recognize_identifier() -> None:
    global pos
    start_line = current_line
    identifier = ""

    while peek().isalnum() or peek() == '_':
        identifier += advance()

    if len(identifier) > 32:
        errors.append(f"警告：标识符长度超过32位，已截断为32位: {identifier} at line {start_line}")
        identifier = identifier[:32]

    token_type = "KEYWORD" if identifier in KEYWORDS else "IDENTIFIER"
    tokens.append(Token(token_type, identifier, start_line))


def recognize_number() -> None:
    start_line = current_line
    num_str = ""
    has_dot = False
    has_digit_after_dot = False

    ch = peek()
    if (ch in '+-') and pos + 1 < len(source_code) and source_code[pos + 1].isdigit():
        num_str += advance()

    while True:
        ch = peek()
        if ch.isdigit():
            num_str += advance()
            if has_dot:
                has_digit_after_dot = True
        elif ch == '.' and not has_dot:
            num_str += advance()
            has_dot = True
        else:
            break

    if not has_dot:
        start_idx = 1 if num_str and num_str[0] in '+-' else 0
        if start_idx < len(num_str) and num_str[start_idx] == '0' and len(num_str) > start_idx + 1:
            errors.append(f"错误：前导零的整数常量: {num_str} at line {start_line}")
            return
        if num_str:
            tokens.append(Token("INT_CONSTANT", num_str, start_line))
    else:
        if not has_digit_after_dot:
            errors.append(f"错误：不完整的实数常量: {num_str} at line {start_line}")
            return
        dot_pos = num_str.find('.')
        int_part = num_str[:dot_pos]
        start_idx = 1 if int_part and int_part[0] in '+-' else 0
        if start_idx < len(int_part) and int_part[start_idx] == '0' and len(int_part) > start_idx + 1:
            errors.append(f"错误：实数整数部分前导零: {num_str} at line {start_line}")
            return
        tokens.append(Token("REAL_CONSTANT", num_str, start_line))


def recognize_string() -> None:
    start_line = current_line
    advance()
    string_val = ""
    closed = False

    while peek() != '\0':
        ch = advance()
        if ch == '"':
            closed = True
            break
        if ch == '\n':
            break
        string_val += ch

    if not closed:
        errors.append(f"错误：未闭合的字符串常量 at line {start_line}")
    else:
        tokens.append(Token("STRING_CONSTANT", string_val, start_line))


def recognize_operator() -> None:
    op = advance()
    next_ch = peek()

    if (op == '+' and next_ch == '+') or \
       (op == '-' and next_ch == '-') or \
       (op == '=' and next_ch == '=') or \
       (op == '!' and next_ch == '=') or \
       (op == '<' and next_ch == '=') or \
       (op == '>' and next_ch == '=') or \
       (op == '&' and next_ch == '&') or \
       (op == '|' and next_ch == '|'):
        op += advance()

    tokens.append(Token("OPERATOR", op, current_line))


def recognize_delimiter() -> None:
    delim = advance()
    tokens.append(Token("DELIMITER", delim, current_line))


def lexical_analyze() -> None:
    global pos, current_line, current_col
    tokens.clear()
    errors.clear()
    pos = 0
    current_line = 1
    current_col = 1

    while pos < len(source_code):
        skip_whitespace_and_comments()
        if pos >= len(source_code):
            break

        ch = peek()

        if ch.isalpha() or ch == '_':
            recognize_identifier()
        elif ch == '"':
            recognize_string()
        elif ch.isdigit() or ((ch in '+-') and pos + 1 < len(source_code) and source_code[pos + 1].isdigit()):
            recognize_number()
        elif ch in '+-*/=!<>%&|^~':
            recognize_operator()
        elif ch in ';,(){}[]':
            recognize_delimiter()
        else:
            # 非法字符
            illegal = advance()
            errors.append(f"错误：非法字符 '{illegal}' at line {current_line}, col {current_col-1}")


def main():
    # 输入文件路径
    filename = input("请输入源程序文件路径（例如：test.txt）：").strip()
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            global source_code
            source_code = f.read()
    except FileNotFoundError:
        print(f"错误：无法打开文件 {filename}")
        sys.exit(1)
    except Exception as e:
        print(f"读取文件出错: {e}")
        sys.exit(1)

    print("\n正在进行词法分析...\n")
    lexical_analyze()

    # 输出单词符号表
    print("=" * 20 + " 词法分析结果 " + "=" * 20)
    if not tokens:
        print("（无有效单词）")
    else:
        print(f"{'行号':<8}{'类型':<20}{'值':<30}")
        print("-" * 60)
        for t in tokens:
            print(f"{t.line:<8}{t.token_type:<20}{t.value:<30}")

    # 输出错误报告
    if errors:
        print("\n" + "=" * 20 + " 错误报告 " + "=" * 20)
        for err in errors:
            print(err)
    else:
        print("\n分析完成，无错误！")

    # 保存结果到文件
    with open("result.txt", 'w', encoding='utf-8') as f:
        f.write("词法分析结果（行号 类型 值）\n")
        for t in tokens:
            f.write(f"{t.line} {t.token_type} {t.value}\n")
        if errors:
            f.write("\n错误：\n")
            for err in errors:
                f.write(err + "\n")
    print("\n结果已保存至 result.txt")


if __name__ == "__main__":
    main()